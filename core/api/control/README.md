# Control API

HTTP control plane for Vimana Framework (`vimana api`).

## Surfaces

| Path | Role |
|------|------|
| `/admin/` | Admin UI (static; Monitor drawer) |
| `/docs` | OpenAPI |
| `/monitor/` | Exception Monitor API (mounted same process) |
| `/v1/monitor/info` | Mount hint for Admin / agents |
| `/v1/health` | Health |
| `/v1/about` | Framework overview (`vimana_about`) |
| `/v1/analyze` | Live-target fingerprint + triage (`POST`) |
| `/v1/tools` | Tool descriptors (MCP-compatible JSON schema) |
| `/v1/tools/{name}` | Invoke tool in-process (`POST` body = arguments) |
| `/v1/plugins` | Plugin catalog |
| `/v1/plugins/{name}` | Detail + capabilities |
| `/v1/plugins/{name}/explain` | Guide card (`?focus=overview\|usage\|args`) |
| `/v1/plugins/{name}/run` | Run plugin (`?async=true` → `202` + poll `/v1/runs/{id}`) |
| `/v1/runs`, `/v1/runs/{id}` | Run history (memory + `~/.vimana/control/runs/`) |
| `/v1/findings/runs/{id}` | Findings slice of a run |
| `/v1/labs` | All labs status |
| `/v1/labs/cleanup` | Stop all running labs |
| `/v1/labs/{plugin}` | Lab status |
| `/v1/labs/{plugin}/start\|stop` | Lab lifecycle |
| `/v1/labs/{plugin}/test` | Start lab + run via `run_hint` (`--lab X --test`) |
| `/v1/atma` | Atma suite manifest + safety flags |
| `/v1/atma/start` | Start dogfood job (localhost Control API only) |
| `/v1/atma/active`, `/v1/atma/{job_id}` | Job status (per-plugin run links) |
| `/v1/specs`, `/v1/specs/{id}` | Shared OpenAPI specs (`_SPECS_` + body) |
| `/v1/channels`, `/v1/channels/{id}` | Shared channels (`_CHANNELS_`) |
| `/v1/cases`, `/v1/cases/{id}` | Saved cases (`_CASES_`) |
| `/v1/cases/{id}/run` | Replay case via Control run (default async) |
| `/v1/resources/spec-consumers` | Plugins that accept `--apispec` |

Plugin detail includes `form`: ordered fields from `specialty_args` → `guide.naviargs` → conditional `target_url`.

Runs include `stdout` / `stderr` and `artifacts_detail` (console, structured report JSON, exported files) for Admin inspection. Handler defaults pad specialty `store_true` fields from the form schema so older plugins do not `KeyError` under API.

### Labs (CLI)

```bash
vimana run --lab boundr --stop
vimana run --lab-operation list
vimana run --cleanup-labs          # no --lab required
vimana run --lab-operation cleanup
```

### Resources (Admin)

Aside sections:

- **Plugins** — catalog (collapsed by default)
- **Labs** — framework lab environments (Docker); cleanup all; not collected artifacts
- **Resources** — shared artifacts: Specs, Channels, Cases

Open a spec for **Docs** (Swagger UI replica) or **JSON**. Run consumers with `apispec_enabled`. Cases replay saved argv via Control (not subprocess CLI).

### Atma (dogfood)

Zero-config self-scan from Admin (**◎ atma**): curated FastAPI suite against this Control API (localhost only, sequential, no fuzz/WS).

Distinct from Exception Monitor (`core/api/backend/`), which is mounted at `/monitor` when Control runs. Real UI is FuzzingDashboard (`core/api/frontend`, `:3000`). Overview: [`core/api/README.md`](../README.md). Detail: `docs/internal/EXCEPTION_MONITOR_API.md`.

### MCP / tools (Fase 2.1)

User-facing guide: [`docs/MCP.md`](../../../docs/MCP.md). Admin UI **MCP** button + `GET /v1/mcp/connect`.

Agents call the same Control surface without an embedded LLM:

```bash
vimana mcp          # stdio MCP server
# or HTTP:
curl -s http://127.0.0.1:8090/v1/tools
curl -s -X POST http://127.0.0.1:8090/v1/tools/vimana_health -d '{}'
curl -s -X POST http://127.0.0.1:8090/v1/tools/vimana_run \
  -H 'Content-Type: application/json' -d '{"name":"boundr"}'
```

`vimana_run` = one-shot playbook (lab+test via `run_hint`, or direct run). Lab-only: `vimana_lab_start`. See [`docs/AGENT.md`](../../../docs/AGENT.md).

Cursor: put the server in **project** `.cursor/mcp.json` (this repo already has one). Do **not** also register `vimana` in `~/.cursor/mcp.json` when `/Users/<you>` is a workspace root — Cursor loads that file twice (user + project) and shows duplicate entries stuck on “Loading tools”.

Transport is **newline-delimited JSON** (official MCP SDK / Cursor), not Content-Length.

```json
{
  "mcpServers": {
    "vimana": {
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": ["-u", "-m", "core.api.control.mcp_server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "VIMANA_PATH": "${workspaceFolder}",
        "VIMANA_MCP": "1",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Or `vimana mcp` if the CLI is on `PATH`. Tools include plugins list/get/run, runs/findings, labs lifecycle + cleanup, specs/channels/cases. Prefer `vimana_run_plugin` with `async: true` then `vimana_get_run`.

### Agent / agentic (Fase 2.2)

Native LLM loop over the same tools (no MCP required):

```bash
# smoke without a live model
vimana agent --provider scripted "check health and list plugins"

# security smoke: scripted attempts lab_cleanup under default policy=safe → denied
vimana agent --provider scripted --scripted-deny --json "security smoke"

# inspect policy / threat notes (learning surface)
vimana agent --show-policy

# Ollama (OpenAI-compatible /v1) — escalate only when needed
vimana agent --policy run --model qwen3.5:0.8b \
  "Check health then list plugins with labs"

# deterministic boundr dogfood (Docker required)
vimana agent --provider scripted --scripted-scenario boundr --policy run --json "boundr e2e"
```

**Tool policies (fail-closed, least privilege):**

| Policy | May call |
|--------|----------|
| `safe` (default) | read/orient only (`health`, `list_*`, `get_*`, lab status) |
| `lab` | safe + `lab_start` / `lab_stop` |
| `run` | lab + `run_plugin` / `run_case` |
| `full` | all tools including `lab_cleanup` (explicit opt-in) |

`--deny-tool` always wins. Unknown tools are denied. The model only sees allowed tools; every call is re-checked before dispatch.

**EXECUTE guards:** targets default to **loopback only**; widen with `--allow-target` / `--allow-any-target`. Optional `--confirm` before `run_plugin`/`run_case` (`--yes` skips).

Providers: `ollama` (default, `http://127.0.0.1:11434/v1`), `openai` / LM Studio via `--base-url`, `scripted` for CI.

Env defaults: `VIMANA_AGENT_MODEL`, `VIMANA_AGENT_PROVIDER`, `VIMANA_AGENT_BASE_URL`, `VIMANA_AGENT_POLICY`. Transcripts land in `~/.vimana/control/agent/` unless `--no-save` (include `denied_calls` + policy).
