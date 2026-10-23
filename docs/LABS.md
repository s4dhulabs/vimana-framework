# Labs

Plugin lab environments (typically Docker) for specialty auditors that need a vulnerable / demo target.

## CLI

```bash
vimana run --lab boundr --test     # start + run hint
vimana run --lab boundr --stop
vimana run --lab-operation list
vimana run --cleanup-labs            # stop all (no --lab required)
vimana run --lab-operation cleanup
```

## Control API / Admin

- `GET /v1/labs` — status for all labs  
- `POST /v1/labs/{plugin}/start|stop`  
- `POST /v1/labs/cleanup`  
- Admin UI **Labs** section in the aside  

## MCP / Agent

Read-only orientation: `vimana_list_labs`, `vimana_lab_status` (agent policy `safe`).

Mutating: `vimana_lab_start` / `vimana_lab_stop` require `--policy lab` (or higher).  
`vimana_lab_cleanup` requires `--policy full`.

Related: [Control API](CONTROL_API.md) · [MCP](MCP.md) · [Agent](AGENT.md)
