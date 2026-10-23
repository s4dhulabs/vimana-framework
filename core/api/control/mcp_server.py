# -*- coding: utf-8 -*-
"""
Minimal MCP stdio server for Vimana Control tools (Fase 2.1).

JSON-RPC 2.0 over stdin/stdout as newline-delimited JSON (official MCP SDK
transport used by Cursor). No Content-Length framing.

No LLM embedded — external agents (Cursor, Claude Code, etc.) call tools.

Usage:
  vimana mcp

Cursor example (project .cursor/mcp.json — avoid duplicating in ~/.cursor when
home is also a workspace root). Use ${workspaceFolder}; never host-absolute paths:
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
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any, Dict, Optional, Set

from core.api.control.tools import call_tool, list_tools

# Cursor / @modelcontextprotocol/sdk SUPPORTED_PROTOCOL_VERSIONS includes these.
SUPPORTED_PROTOCOL_VERSIONS: Set[str] = {
    '2024-10-07',
    '2024-11-05',
    '2025-03-26',
    '2025-06-18',
    '2025-11-25',
}
DEFAULT_PROTOCOL_VERSION = '2025-03-26'
SERVER_INFO = {'name': 'vimana-control', 'version': '1.0.0'}

# Real stdout used only for MCP replies (plugins must not write here).
_MCP_STDOUT = None


def _ensure_vimana_path() -> None:
    if os.getenv('VIMANA_PATH'):
        return
    here = os.path.abspath(__file__)
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))
    if os.path.isdir(os.path.join(repo, 'siddhis')):
        os.environ['VIMANA_PATH'] = repo


def _read_message() -> Optional[Dict[str, Any]]:
    """Read one MCP message (newline-delimited JSON) from stdin."""
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        text = line.decode('utf-8').strip()
        if not text:
            continue
        return json.loads(text)


def _write_message(payload: Dict[str, Any]) -> None:
    """Write one MCP message as a single JSON line to the real stdout."""
    data = (json.dumps(payload, default=str, ensure_ascii=False) + '\n').encode('utf-8')
    out = _MCP_STDOUT or sys.__stdout__
    buf = getattr(out, 'buffer', None)
    if buf is not None:
        buf.write(data)
        buf.flush()
    else:
        os.write(1, data)


def _ok(req_id: Any, result: Any) -> Dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': req_id, 'result': result}


def _err(req_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {'code': code, 'message': message}
    if data is not None:
        err['data'] = data
    return {'jsonrpc': '2.0', 'id': req_id, 'error': err}


def _handle(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = msg.get('method')
    req_id = msg.get('id')
    params = msg.get('params') or {}

    # Notifications (no id) — acknowledge silently
    if req_id is None and method:
        return None

    if method == 'initialize':
        requested = str((params or {}).get('protocolVersion') or '')
        version = (
            requested
            if requested in SUPPORTED_PROTOCOL_VERSIONS
            else DEFAULT_PROTOCOL_VERSION
        )
        return _ok(req_id, {
            'protocolVersion': version,
            'capabilities': {'tools': {}},
            'serverInfo': SERVER_INFO,
        })

    if method == 'ping':
        return _ok(req_id, {})

    if method == 'tools/list':
        return _ok(req_id, {'tools': list_tools()})

    if method == 'tools/call':
        name = params.get('name')
        arguments = params.get('arguments') or {}
        if not name:
            return _err(req_id, -32602, 'missing tool name')
        try:
            result = call_tool(str(name), arguments if isinstance(arguments, dict) else {})
            text = json.dumps(result, default=str, ensure_ascii=False, indent=2)
            return _ok(req_id, {
                'content': [{'type': 'text', 'text': text}],
                'structuredContent': result if isinstance(result, dict) else {'result': result},
                'isError': False,
            })
        except LookupError as exc:
            return _ok(req_id, {
                'content': [{'type': 'text', 'text': str(exc)}],
                'isError': True,
            })
        except Exception as exc:
            return _ok(req_id, {
                'content': [{
                    'type': 'text',
                    'text': f'{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=6)}',
                }],
                'isError': True,
            })

    return _err(req_id, -32601, f'method not found: {method}')


def serve_mcp_stdio() -> None:
    """Block on stdin and serve MCP until EOF."""
    global _MCP_STDOUT
    from core.api.control.mcp_log import log_mcp, log_mcp_banner

    _ensure_vimana_path()
    os.environ['VIMANA_MCP'] = '1'
    os.environ.setdefault('VIMANA_QUIET_CONSOLE', '1')

    # Isolate MCP replies on the real stdout; divert prints to stderr so plugin
    # banners / logging cannot corrupt NDJSON messages.
    _MCP_STDOUT = sys.stdout
    sys.stdout = sys.stderr

    log_mcp_banner(
        'stdio server ready — NDJSON on stdout; traffic log on stderr. '
        'Note: Admin Atma spawns its own MCP child (watch the `vimana api` terminal, '
        'not this idle process).'
    )

    while True:
        try:
            msg = _read_message()
        except (json.JSONDecodeError, ValueError) as exc:
            _write_message(_err(None, -32700, f'parse error: {exc}'))
            continue
        if msg is None:
            break
        log_mcp('← client', msg, tag='mcp')
        try:
            response = _handle(msg)
        except Exception as exc:
            response = _err(
                msg.get('id'),
                -32603,
                f'internal error: {exc}',
                traceback.format_exc(limit=4),
            )
        if response is not None:
            log_mcp('→ client', response, tag='mcp')
            _write_message(response)


def main() -> None:
    serve_mcp_stdio()


if __name__ == '__main__':
    main()
