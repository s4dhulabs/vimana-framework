# -*- coding: utf-8 -*-
"""Pretty MCP traffic logging to stderr (stdout stays NDJSON-clean)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional


def mcp_log_enabled(*, force: Optional[bool] = None) -> bool:
    """
    Traffic log on stderr.

    - VIMANA_MCP_LOG=0|false|off → always off
    - VIMANA_MCP_LOG=1|true|on  → always on
    - force=True → on (unless env explicitly off)
    - default: on when stderr is a TTY (interactive terminals)
    """
    raw = (os.getenv('VIMANA_MCP_LOG') or '').strip().lower()
    if raw in ('0', 'false', 'no', 'off'):
        return False
    if raw in ('1', 'true', 'yes', 'on'):
        return True
    if force is True:
        return True
    if force is False:
        return False
    try:
        return sys.stderr.isatty()
    except Exception:
        return False


def _highlight_json(text: str) -> str:
    try:
        from pygments import highlight
        from pygments.formatters import TerminalFormatter
        from pygments.lexers import JsonLexer
        return highlight(text, JsonLexer(), TerminalFormatter()).rstrip('\n')
    except Exception:
        return text


def _truncate(text: str, limit: int = 2400) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 20] + '\n  … truncated …'


def format_mcp_payload(obj: Any, *, indent: int = 2) -> str:
    try:
        text = json.dumps(obj, indent=indent, ensure_ascii=False, default=str)
    except Exception:
        text = repr(obj)
    return _highlight_json(_truncate(text))


def log_mcp(
    direction: str,
    payload: Any,
    *,
    tag: str = 'mcp',
    force: Optional[bool] = None,
) -> None:
    """
    direction: '←' (inbound / request to server) or '→' (outbound / response)
               or a short label like 'atma←' / 'atma→'
    """
    if not mcp_log_enabled(force=force):
        return
    label = direction
    try:
        from neotermcolor import colored
        arrow = colored(label, 'cyan', attrs=['bold'])
        prefix = colored(f'[{tag}]', 'magenta')
    except Exception:
        arrow = label
        prefix = f'[{tag}]'
    body = format_mcp_payload(payload)
    sys.stderr.write(f'{prefix} {arrow}\n{body}\n')
    sys.stderr.flush()


def log_mcp_banner(message: str, *, tag: str = 'mcp') -> None:
    if not mcp_log_enabled():
        return
    try:
        from neotermcolor import colored
        line = colored(f'[{tag}] {message}', 'yellow')
    except Exception:
        line = f'[{tag}] {message}'
    sys.stderr.write(line + '\n')
    sys.stderr.flush()
