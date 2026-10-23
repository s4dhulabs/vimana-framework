# Vimana `core/api`

```
core/api/
  backend/           # Exception Monitor API (vf_server, mock_seed, cli)
  frontend/          # FuzzingDashboard (Next.js) — real exception UI
  control/           # Control API + Admin (@ :8090) — mounts /monitor
  + MCP / agent      # vimana mcp · vimana agent (docs/MCP.md, docs/AGENT.md)
```

## Surfaces

| Surface | Role |
|---------|------|
| `:8090` Control + Admin | Operate plugins / labs / runs / Atma / MCP snippet |
| `:8090/monitor` or `:8000` | Exception JSON + WebSocket backend |
| `:3000` FuzzingDashboard | Live exception panel (Scan filter, `?monitor=` / `?scan=`) |
| `:8090/admin` Monitor drawer | Seed / browse; **UI ↗** opens `:3000` |

## Demo (seed, no lab)

```bash
# Terminal 1
vimana monitor --seed-demo

# Terminal 2 (first time: npm install)
cd core/api/frontend && cp -n .env.example .env.local
npm install && npm run dev
# → http://127.0.0.1:3000  — use Scan dropdown
```

## Live (fuzz → UI)

```bash
vimana monitor                                          # empty API
cd core/api/frontend && npm run dev                     # UI
export VIMANA_MONITOR_ENABLED=1
export VIMANA_MONITOR_URL=http://127.0.0.1:8000
vimana run djunch …                                    # or d4m8 + lab
```

Same API under Control: `vimana api` → `VIMANA_MONITOR_URL=http://127.0.0.1:8090/monitor`.

## Related docs

- [`docs/CONTROL_API.md`](../../docs/CONTROL_API.md) · [`docs/MCP.md`](../../docs/MCP.md) · [`docs/AGENT.md`](../../docs/AGENT.md)
- [`docs/internal/EXCEPTION_MONITOR_API.md`](../../docs/internal/EXCEPTION_MONITOR_API.md)
