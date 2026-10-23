# MCP (Model Context Protocol)

Expose Vimana Control tools to external agents (Cursor, Claude Code, etc.) over **stdio**.

Framing: **newline-delimited JSON** (official MCP SDK / Cursor). Not Content-Length / LSP framing.

## Quick start

```bash
vimana mcp
```

Or:

```bash
python -u -m core.api.control.mcp_server
```

## Cursor

Prefer **project** `.cursor/mcp.json` (not only `~/.cursor/mcp.json` if your home folder is also a workspace root — Cursor would register the server twice).

From a running Control API:

```bash
curl -s http://127.0.0.1:8090/v1/mcp/connect | jq .cursor.mcp_json
```

Admin UI → **MCP** button also shows the same JSON with syntax highlighting and **Copy**.

Example shape (**portable** — Cursor interpolates `${workspaceFolder}`; never commit host-absolute paths):

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

`GET /v1/mcp/connect` returns that portable JSON as `cursor.mcp_json` (what Admin **Copy JSON** uses). A machine-resolved copy lives under `cursor.resolved_local` (`do_not_commit: true`) for local debugging only — keep `.cursor/mcp.json` out of git.

## HTTP alternative

While `vimana api` is up:

- `GET /v1/tools` — descriptors  
- `POST /v1/tools/{name}` — invoke in-process  

## Dogfood

**Atma** (Admin → ◎ atma) runs non-destructive MCP checks after the plugin suite: initialize, tools/list, health, list_plugins, list_labs, unknown-tool error.

Those checks **spawn a private** `mcp_server` subprocess. They do **not** talk to an idle `vimana mcp` in another terminal. Watch the **`vimana api`** terminal for highlighted NDJSON traffic (`[atma-mcp]`).

Interactive `vimana mcp` (or Cursor) logs client traffic on **stderr** as `[mcp]` when stderr is a TTY. Force with `VIMANA_MCP_LOG=1`; disable with `VIMANA_MCP_LOG=0`.

Related: [Control API](CONTROL_API.md) · [Agent](AGENT.md)
