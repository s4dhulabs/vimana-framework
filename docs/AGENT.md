# Agent (native LLM loop)

`vimana agent` runs an in-process planner that calls the same Control tools as MCP / HTTP — with a **fail-closed tool policy**.

## Natural language playbook

Short commands are resolved **deterministically** (no LLM required):

| You say | Agent does |
|---------|------------|
| `o que é a vimana?` / `what is vimana?` | `vimana_about` — overview from framework docs |
| `o que é o plugin framewalk?` / `what does boundr do?` | `vimana_explain_plugin` (guide overview) |
| `como usar o plugin X?` / `how to use Y?` | `vimana_explain_plugin` (args + examples + labs) |
| `Analyze this target http://…` | `vimana_analyze_target` — framewalk fingerprint → framework → plugin triage |
| `rode o framewalk` / `run boundr` / `run the plugin X` | `vimana_run` — lab if needed + run + **stop lab** |
| `rode o lab framewalk` / `start the boundr lab` | `vimana_lab_start` only — lab stays up |
| bare catalog name (`framewalk`) | same as run plugin |

Informational answers reuse the same material as `vimana about` / `vimana guide` / plugin YAML guides — the agent organizes it; it does not invent docs.

**Analyze target** (live URL, not a lab): stderr shows colored stages (`parse` → `fingerprint` → `framework` → `triage` → `recommend` / `auto`). Default is fingerprint + **ordered** recommendations only.

Deterministic triage queues (when confidence selects the primary stack):

| Stack | Order |
|-------|--------|
| FastAPI / Starlette | `jcolt` → `fff` → `pyserial` (if OpenAPI) → `boundr` → `socketline` → … |
| Django | `sttinger` → `dmt` → `d4m8` → `jungle` → `objgate` → … |

`--auto` (or NL `with auto` / `full suite`) runs the full queue after fingerprint. Remote hosts need `--allow-target <host>` (loopback allowed by default).

To leave a lab running after a plugin run (power users): `stop_lab_after=false`, or `vimana_lab_start` then `vimana_run_plugin`.

```bash
# informational (policy safe is enough)
vimana agent --policy safe "o que é a vimana?"
vimana agent --policy safe "o que é o plugin framewalk?"
vimana agent --policy safe "como usar o boundr?"

# analyze a live target (fingerprint → ordered triage)
vimana agent --policy run --allow-target target-pyyapi.com \
  "Analyze this target http://target-pyyapi.com"
# run the full playbook queue after triage
vimana agent --policy run --auto --allow-target 127.0.0.1 \
  "Analyze this target http://127.0.0.1:18003"

# run / lab
vimana agent --policy run "rode o framewalk"
vimana agent --policy lab "rode o lab boundr"
vimana agent --policy run --json "run the siddhi fetchbane"
```

Longer free-form goals still use the LLM; the system prompt steers it to prefer `vimana_about` / `vimana_explain_plugin` for Q&A, `vimana_analyze_target` for unknown stacks, and `vimana_run` over guessing specialty args.

## Quick start

```bash
# deterministic smoke (no LLM)
vimana agent --provider scripted "check health"

# security smoke: attempts lab_cleanup under default policy → denied
vimana agent --provider scripted --scripted-deny --json "security smoke"

# security smoke: remote EXECUTE target denied (loopback allowlist)
vimana agent --provider scripted --scripted-scenario remote-deny --policy run --json \
  "remote deny"

# dogfood e2e (Docker): lab → boundr audit → findings → stop
vimana agent --provider scripted --scripted-scenario boundr --policy run --json \
  "boundr e2e"

# live model (prefer playbook phrases above on small models)
vimana agent --policy run --model qwen3.5:0.8b "rode o boundr"

vimana agent --show-policy
```

`--scripted-scenario boundr` remains the reliable CI dogfood for the multi-step chain. `vimana_run` is the everyday one-shot.

## Policies (least privilege)

| Policy | Privilege |
|--------|-----------|
| `safe` (default) | Read / orient only |
| `lab` | + start/stop individual labs |
| `run` | + `vimana_run` / `vimana_lab_test` / `run_plugin` / `run_case` |
| `full` | All tools including `lab_cleanup` |

`--deny-tool` always wins. Unknown tools are denied. The model only sees allowed tools; every call is re-checked.

## EXECUTE guards

| Control | Default | Override |
|---------|---------|----------|
| Target hosts | loopback + any `--allow-target` (additive) | `--allow-any-target` to disable |
| Human confirm | off | `--confirm` (prompt before EXECUTE); `--yes` skips |

Default Ollama model is **auto-detected** from installed tags (prefers `qwen3.5:0.8b` when present). Override with `--model` / `VIMANA_AGENT_MODEL`.

Env: `VIMANA_AGENT_MODEL`, `VIMANA_AGENT_PROVIDER`, `VIMANA_AGENT_POLICY`, `VIMANA_AGENT_ALLOW_TARGETS`, `VIMANA_AGENT_ALLOW_ANY_TARGET`, `VIMANA_AGENT_YES`, …

Transcripts: `~/.vimana/control/agent/` (unless `--no-save`).

Related: [MCP](MCP.md) · [Control API](CONTROL_API.md)
