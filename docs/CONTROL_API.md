# Control API

Operate Vimana over HTTP: plugins, runs, labs, findings, shared resources, Atma dogfood.

## Quick start

```bash
vimana api                  # http://127.0.0.1:8090
# Admin UI
open http://127.0.0.1:8090/admin/
# OpenAPI (Swagger)
open http://127.0.0.1:8090/docs
```

Bind options: `vimana api --host 127.0.0.1 --port 8090`.

## Surfaces

| Path | Role |
|------|------|
| `/admin/` | Admin UI (Monitor drawer → seed / link UI) |
| `/docs` | OpenAPI / Swagger |
| `/monitor/` | Exception Monitor API (same process) |
| `/v1/health` | Health |
| `/v1/about` | Framework overview (`vimana about` spirit) |
| `/v1/analyze` | Fingerprint + plugin triage (`POST` `{target_url}`) |
| `/v1/monitor/info` | Monitor mount hint |
| `/v1/tools` | Tool descriptors (agent / MCP schema) |
| `/v1/tools/{name}` | Invoke tool (`POST`) |
| `/v1/mcp/connect` | Cursor-ready MCP JSON snippet |
| `/v1/plugins` | Plugin catalog |
| `/v1/plugins/{name}/explain` | Guide card (`?focus=overview\|usage\|args`) |
| `/v1/plugins/{name}/run` | Run (`?async=true` → poll `/v1/runs/{id}`) |
| `/v1/runs` | Run history |
| `/v1/labs` | Labs status / lifecycle |
| `/v1/atma` | Dogfood suite (+ MCP checks) |
| `/v1/specs`, `/v1/channels`, `/v1/cases` | Shared resources |

Exception UI (FuzzingDashboard) is separate: `cd core/api/frontend && npm run dev` → `:3000` with `?monitor=http://127.0.0.1:8090/monitor`. Standalone API: `vimana monitor --seed-demo` → `:8000`. See [`core/api/README.md`](../core/api/README.md).

Module notes and deeper detail: [`core/api/control/README.md`](../core/api/control/README.md).

Related: [MCP](MCP.md) · [Labs](LABS.md) · [Agent](AGENT.md)
