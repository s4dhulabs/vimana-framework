# -*- coding: utf-8 -*-
"""Helpers for MCP connect snippets + Atma non-destructive MCP checks."""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def vimana_repo_root() -> Path:
    env = os.getenv('VIMANA_PATH') or os.getenv('PYTHONPATH', '').split(os.pathsep)[0]
    if env:
        p = Path(env).expanduser().resolve()
        if (p / 'siddhis').is_dir() or (p / 'core').is_dir():
            return p
    here = Path(__file__).resolve()
    # core/api/control/mcp_connect.py → repo root
    return here.parents[3]


# Portable token Cursor interpolates to the project that owns .cursor/mcp.json.
# Never bake host-absolute paths into the copyable / documentable snippet.
_CURSOR_WORKSPACE = '${workspaceFolder}'


def python_executable(repo: Optional[Path] = None) -> str:
    """Absolute interpreter for this host (runtime only — not for mcp.json templates)."""
    root = repo or vimana_repo_root()
    venv_py = root / '.venv' / 'bin' / 'python'
    if venv_py.is_file():
        return str(venv_py)
    return sys.executable


def cursor_mcp_snippet(*, portable: bool = True, repo: Optional[Path] = None) -> Dict[str, Any]:
    """
    Project-scoped Cursor mcp.json fragment.

    portable=True (default): uses ${workspaceFolder} — safe to copy, share, and
    commit as an example. Never embeds the developer's machine path.

    portable=False: absolute paths resolved on this host for local convenience
    only (do not commit).
    """
    if portable:
        root_s = _CURSOR_WORKSPACE
        command = f'{_CURSOR_WORKSPACE}/.venv/bin/python'
    else:
        root = repo or vimana_repo_root()
        root_s = str(root)
        command = python_executable(root)
    return {
        'mcpServers': {
            'vimana': {
                'command': command,
                'args': ['-u', '-m', 'core.api.control.mcp_server'],
                'cwd': root_s,
                'env': {
                    'PYTHONPATH': root_s,
                    'VIMANA_PATH': root_s,
                    'VIMANA_MCP': '1',
                    'PYTHONUNBUFFERED': '1',
                },
            }
        }
    }


def mcp_connect_payload() -> Dict[str, Any]:
    root = vimana_repo_root()
    portable = cursor_mcp_snippet(portable=True)
    resolved = cursor_mcp_snippet(portable=False, repo=root)
    return {
        'transport': 'stdio',
        'framing': 'newline-delimited JSON (NDJSON)',
        'cli': 'vimana mcp',
        'module': 'python -u -m core.api.control.mcp_server',
        'cursor': {
            'path_hint': '<project>/.cursor/mcp.json',
            'note': (
                'Copy the portable snippet (${workspaceFolder}). '
                'Cursor resolves it to the project that owns .cursor/mcp.json. '
                'Do not commit host-absolute paths. Prefer project-scoped mcp.json; '
                'avoid duplicating the same server in ~/.cursor/mcp.json when your '
                'home directory is also a workspace root.'
            ),
            # Default / Copy target — never machine-absolute.
            'mcp_json': portable,
            'mcp_json_text': json.dumps(portable, indent=2),
            # Optional local fill-in — runtime only, never the commit surface.
            'resolved_local': {
                'do_not_commit': True,
                'repo': str(root),
                'python': python_executable(root),
                'mcp_json': resolved,
                'mcp_json_text': json.dumps(resolved, indent=2),
            },
        },
        'http_tools': {
            'list': 'GET /v1/tools',
            'call': 'POST /v1/tools/{name}',
        },
        'docs': 'docs/MCP.md',
    }


# --- Atma MCP protocol checks (in-process subprocess, read-only tools) ---

def _send(stdin, obj: dict) -> None:
    from core.api.control.mcp_log import log_mcp
    log_mcp('atma → server', obj, tag='atma-mcp', force=True)
    data = (json.dumps(obj) + '\n').encode('utf-8')
    os.write(stdin.fileno(), data)


def _recv(stdout, timeout: float = 8.0) -> Optional[dict]:
    deadline = time.time() + timeout
    buf = b''
    while time.time() < deadline:
        r, _, _ = select.select([stdout.fileno()], [], [], 0.2)
        if not r:
            continue
        chunk = os.read(stdout.fileno(), 65536)
        if not chunk:
            break
        buf += chunk
        if b'\n' in buf:
            line, _, _ = buf.partition(b'\n')
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line.decode('utf-8'))
            from core.api.control.mcp_log import log_mcp
            log_mcp('atma ← server', msg, tag='atma-mcp', force=True)
            return msg
    return None


def _spawn_mcp() -> Tuple[subprocess.Popen, Dict[str, str]]:
    root = vimana_repo_root()
    py = python_executable(root)
    env = os.environ.copy()
    env.update({
        'PYTHONPATH': str(root),
        'VIMANA_PATH': str(root),
        'VIMANA_MCP': '1',
        'VIMANA_QUIET_CONSOLE': '1',
        'PYTHONUNBUFFERED': '1',
    })
    proc = subprocess.Popen(
        [py, '-u', '-m', 'core.api.control.mcp_server'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(root),
        env=env,
    )
    return proc, env


def run_mcp_check(check_id: str) -> Dict[str, Any]:
    """Run one non-destructive MCP check. Returns status + detail summary."""
    runners = {
        'mcp_initialize': _check_initialize,
        'mcp_tools_list': _check_tools_list,
        'mcp_health': _check_health,
        'mcp_list_plugins': _check_list_plugins,
        'mcp_list_labs': _check_list_labs,
        'mcp_unknown_tool': _check_unknown_tool,
    }
    fn = runners.get(check_id)
    if not fn:
        return {'status': 'skipped', 'error': f'unknown check {check_id}', 'summary': None}
    proc = None
    try:
        proc, _ = _spawn_mcp()
        assert proc.stdin and proc.stdout
        return fn(proc)
    except Exception as exc:
        return {
            'status': 'failed',
            'error': f'{type(exc).__name__}: {exc}',
            'summary': None,
        }
    finally:
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


def _handshake(proc: subprocess.Popen) -> dict:
    _send(proc.stdin, {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'initialize',
        'params': {
            'protocolVersion': '2025-03-26',
            'capabilities': {},
            'clientInfo': {'name': 'vimana-atma', 'version': '1.0'},
        },
    })
    init = _recv(proc.stdout, timeout=12)
    if not init or 'result' not in init:
        raise RuntimeError(f'initialize failed: {init!r}')
    _send(proc.stdin, {'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    return init['result']


def _check_initialize(proc: subprocess.Popen) -> Dict[str, Any]:
    result = _handshake(proc)
    return {
        'status': 'succeeded',
        'error': None,
        'summary': {
            'protocolVersion': result.get('protocolVersion'),
            'server': (result.get('serverInfo') or {}).get('name'),
        },
    }


def _check_tools_list(proc: subprocess.Popen) -> Dict[str, Any]:
    _handshake(proc)
    _send(proc.stdin, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
    resp = _recv(proc.stdout, timeout=12)
    tools = ((resp or {}).get('result') or {}).get('tools') or []
    if not tools:
        return {'status': 'failed', 'error': 'empty tools/list', 'summary': None}
    names = [t.get('name') for t in tools]
    return {
        'status': 'succeeded',
        'error': None,
        'summary': {'tool_count': len(tools), 'sample': names[:5]},
    }


def _call_tool(proc: subprocess.Popen, name: str, arguments: Optional[dict] = None, req_id: int = 3) -> dict:
    _handshake(proc)
    _send(proc.stdin, {
        'jsonrpc': '2.0',
        'id': req_id,
        'method': 'tools/call',
        'params': {'name': name, 'arguments': arguments or {}},
    })
    resp = _recv(proc.stdout, timeout=30)
    if not resp or 'result' not in resp:
        raise RuntimeError(f'tools/call {name} failed: {resp!r}')
    return resp['result']


def _parse_tool_text(result: dict) -> Any:
    content = result.get('content') or []
    if content and isinstance(content[0], dict) and content[0].get('text'):
        try:
            return json.loads(content[0]['text'])
        except json.JSONDecodeError:
            return content[0]['text']
    return result.get('structuredContent')


def _check_health(proc: subprocess.Popen) -> Dict[str, Any]:
    result = _call_tool(proc, 'vimana_health')
    if result.get('isError'):
        return {'status': 'failed', 'error': 'health returned isError', 'summary': None}
    body = _parse_tool_text(result)
    ok = isinstance(body, dict) and body.get('status') == 'ok'
    return {
        'status': 'succeeded' if ok else 'failed',
        'error': None if ok else f'unexpected health payload: {body!r}'[:200],
        'summary': body if isinstance(body, dict) else {'raw': str(body)[:120]},
    }


def _check_list_plugins(proc: subprocess.Popen) -> Dict[str, Any]:
    result = _call_tool(proc, 'vimana_list_plugins')
    body = _parse_tool_text(result)
    plugins = (body or {}).get('plugins') if isinstance(body, dict) else None
    if not isinstance(plugins, list) or not plugins:
        return {'status': 'failed', 'error': 'no plugins in list', 'summary': None}
    return {
        'status': 'succeeded',
        'error': None,
        'summary': {'plugins_loaded': len(plugins)},
    }


def _check_list_labs(proc: subprocess.Popen) -> Dict[str, Any]:
    result = _call_tool(proc, 'vimana_list_labs')
    body = _parse_tool_text(result)
    labs = (body or {}).get('labs') if isinstance(body, dict) else None
    if labs is None:
        return {'status': 'failed', 'error': 'missing labs key', 'summary': None}
    return {
        'status': 'succeeded',
        'error': None,
        'summary': {'labs_listed': len(labs) if isinstance(labs, list) else 0},
    }


def _check_unknown_tool(proc: subprocess.Popen) -> Dict[str, Any]:
    result = _call_tool(proc, 'vimana_not_a_real_tool_atma')
    # Our server returns isError True for LookupError
    if result.get('isError'):
        return {
            'status': 'succeeded',
            'error': None,
            'summary': {'expected_error': True, 'message': (result.get('content') or [{}])[0].get('text', '')[:120]},
        }
    return {
        'status': 'failed',
        'error': 'unknown tool did not set isError',
        'summary': None,
    }


def run_all_mcp_checks(
    on_progress: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Run the full ATMA MCP suite on a single stdio process (faster / cleaner).
    on_progress(check_id, partial_dict) optional callback while running.
    """
    outcomes: List[Dict[str, Any]] = []
    proc = None
    try:
        from core.api.control.mcp_log import log_mcp_banner
        log_mcp_banner(
            'Atma MCP suite — spawning private stdio child '
            '(this is not your idle `vimana mcp` terminal)',
            tag='atma-mcp',
        )
        proc, _ = _spawn_mcp()
        assert proc.stdin and proc.stdout
        # Shared session: initialize once, then list + calls
        sequence = [
            ('mcp_initialize', None),
            ('mcp_tools_list', 'list'),
            ('mcp_health', 'health'),
            ('mcp_list_plugins', 'plugins'),
            ('mcp_list_labs', 'labs'),
            ('mcp_unknown_tool', 'unknown'),
        ]
        init_result = None
        for check_id, kind in sequence:
            if on_progress:
                on_progress(check_id, {'status': 'running'})
            try:
                if kind is None:
                    init_result = _handshake(proc)
                    out = {
                        'id': check_id,
                        'status': 'succeeded',
                        'error': None,
                        'summary': {
                            'protocolVersion': init_result.get('protocolVersion'),
                            'server': (init_result.get('serverInfo') or {}).get('name'),
                        },
                    }
                elif kind == 'list':
                    if init_result is None:
                        init_result = _handshake(proc)
                    _send(proc.stdin, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
                    resp = _recv(proc.stdout, timeout=12)
                    tools = ((resp or {}).get('result') or {}).get('tools') or []
                    if not tools:
                        out = {'id': check_id, 'status': 'failed', 'error': 'empty tools/list', 'summary': None}
                    else:
                        names = [t.get('name') for t in tools]
                        out = {
                            'id': check_id,
                            'status': 'succeeded',
                            'error': None,
                            'summary': {'tool_count': len(tools), 'sample': names[:5]},
                        }
                elif kind == 'health':
                    if init_result is None:
                        init_result = _handshake(proc)
                    # already initialized — call without re-handshake
                    _send(proc.stdin, {
                        'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
                        'params': {'name': 'vimana_health', 'arguments': {}},
                    })
                    resp = _recv(proc.stdout, timeout=30)
                    result = (resp or {}).get('result') or {}
                    body = _parse_tool_text(result)
                    ok = isinstance(body, dict) and body.get('status') == 'ok'
                    out = {
                        'id': check_id,
                        'status': 'succeeded' if ok else 'failed',
                        'error': None if ok else f'unexpected health: {body!r}'[:200],
                        'summary': body if isinstance(body, dict) else None,
                    }
                elif kind == 'plugins':
                    _send(proc.stdin, {
                        'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
                        'params': {'name': 'vimana_list_plugins', 'arguments': {}},
                    })
                    resp = _recv(proc.stdout, timeout=30)
                    result = (resp or {}).get('result') or {}
                    body = _parse_tool_text(result)
                    plugins = (body or {}).get('plugins') if isinstance(body, dict) else None
                    if not isinstance(plugins, list) or not plugins:
                        out = {'id': check_id, 'status': 'failed', 'error': 'no plugins', 'summary': None}
                    else:
                        out = {
                            'id': check_id,
                            'status': 'succeeded',
                            'error': None,
                            'summary': {'plugins_loaded': len(plugins)},
                        }
                elif kind == 'labs':
                    _send(proc.stdin, {
                        'jsonrpc': '2.0', 'id': 5, 'method': 'tools/call',
                        'params': {'name': 'vimana_list_labs', 'arguments': {}},
                    })
                    resp = _recv(proc.stdout, timeout=30)
                    result = (resp or {}).get('result') or {}
                    body = _parse_tool_text(result)
                    labs = (body or {}).get('labs') if isinstance(body, dict) else None
                    if labs is None:
                        out = {'id': check_id, 'status': 'failed', 'error': 'missing labs', 'summary': None}
                    else:
                        out = {
                            'id': check_id,
                            'status': 'succeeded',
                            'error': None,
                            'summary': {'labs_listed': len(labs) if isinstance(labs, list) else 0},
                        }
                else:  # unknown
                    _send(proc.stdin, {
                        'jsonrpc': '2.0', 'id': 6, 'method': 'tools/call',
                        'params': {'name': 'vimana_not_a_real_tool_atma', 'arguments': {}},
                    })
                    resp = _recv(proc.stdout, timeout=20)
                    result = (resp or {}).get('result') or {}
                    if result.get('isError'):
                        msg = ((result.get('content') or [{}])[0] or {}).get('text', '')[:120]
                        out = {
                            'id': check_id,
                            'status': 'succeeded',
                            'error': None,
                            'summary': {'expected_error': True, 'message': msg},
                        }
                    else:
                        out = {
                            'id': check_id,
                            'status': 'failed',
                            'error': 'unknown tool did not set isError',
                            'summary': None,
                        }
            except Exception as exc:
                out = {
                    'id': check_id,
                    'status': 'failed',
                    'error': f'{type(exc).__name__}: {exc}',
                    'summary': None,
                }
            outcomes.append(out)
            if on_progress:
                on_progress(check_id, out)
        return outcomes
    finally:
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass


ATMA_MCP_CHECKS: List[Dict[str, Any]] = [
    {
        'id': 'mcp_initialize',
        'label': 'MCP initialize',
        'blurb': 'NDJSON handshake + protocol negotiation',
        'timeout_sec': 20,
    },
    {
        'id': 'mcp_tools_list',
        'label': 'MCP tools/list',
        'blurb': 'Advertise Control tools to the agent client',
        'timeout_sec': 20,
    },
    {
        'id': 'mcp_health',
        'label': 'MCP vimana_health',
        'blurb': 'Read-only health via tools/call',
        'timeout_sec': 30,
    },
    {
        'id': 'mcp_list_plugins',
        'label': 'MCP vimana_list_plugins',
        'blurb': 'Catalog plugins through MCP',
        'timeout_sec': 30,
    },
    {
        'id': 'mcp_list_labs',
        'label': 'MCP vimana_list_labs',
        'blurb': 'List labs status (no start/stop)',
        'timeout_sec': 30,
    },
    {
        'id': 'mcp_unknown_tool',
        'label': 'MCP unknown tool',
        'blurb': 'Expect isError for nonexistent tool (fail-closed)',
        'timeout_sec': 20,
    },
]
