# -*- coding: utf-8 -*-
"""Colored, stage-aware agent logging (stderr)."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Optional


def _color_enabled() -> bool:
    raw = (os.getenv('VIMANA_AGENT_COLOR') or '').strip().lower()
    if raw in ('0', 'false', 'no', 'off'):
        return False
    if raw in ('1', 'true', 'yes', 'on'):
        return True
    try:
        return sys.stderr.isatty()
    except Exception:
        return False


def _c(text: str, color: str, *, attrs: Optional[list] = None) -> str:
    if not _color_enabled():
        return text
    try:
        from neotermcolor import colored
        return colored(text, color, attrs=attrs or [])
    except Exception:
        return text


def _highlight_json(obj: Any, *, limit: int = 900) -> str:
    try:
        text = json.dumps(obj, ensure_ascii=False, default=str, indent=2)
    except Exception:
        text = repr(obj)
    if len(text) > limit:
        text = text[: limit - 20] + '\n  … truncated …'
    if not _color_enabled():
        return text
    try:
        from pygments import highlight
        from pygments.formatters import TerminalFormatter
        from pygments.lexers import JsonLexer
        return highlight(text, JsonLexer(), TerminalFormatter()).rstrip('\n')
    except Exception:
        return text


class AgentLog:
    """
    Structured agent progress lines:

      [agent] stage fingerprint → running framewalk on http://…
      [agent] ok framework → FastAPI (confidence=87)
      [agent] DENY …
    """

    def __init__(self, emit: Optional[Callable[[str], None]] = None) -> None:
        self._emit = emit or (lambda m: print(m, file=sys.stderr))

    def line(self, msg: str) -> None:
        text = (msg or '').rstrip('\n')
        # Accept legacy callers that already prefix "[agent]"
        if text.startswith('[agent]'):
            text = text[len('[agent]'):].lstrip()
        prefix = _c('[agent]', 'magenta', attrs=['bold'])
        # Color common keywords in free-form lines
        low = text.lower()
        if low.startswith('deny ') or ' deny ' in f' {low}':
            text = _c(text, 'red')
        elif low.startswith('done') or low.startswith('playbook'):
            text = _c(text, 'cyan') if low.startswith('playbook') else _c(text, 'green')
        self._emit(f'{prefix} {text}')

    def stage(self, name: str, detail: str = '', *, status: str = 'run') -> None:
        """status: run | ok | skip | fail | warn"""
        colors = {
            'run': 'cyan',
            'ok': 'green',
            'skip': 'yellow',
            'fail': 'red',
            'warn': 'yellow',
            'deny': 'red',
        }
        tag = _c(f'stage {name}', colors.get(status, 'cyan'), attrs=['bold'])
        arrow = _c('→', 'white')
        body = detail.strip()
        self.line(f'{tag} {arrow} {body}' if body else f'{tag}')

    def tool(self, name: str, args_preview: str = '') -> None:
        t = _c(f'tool {name}', 'blue', attrs=['bold'])
        if args_preview:
            self.line(f'{t}({args_preview})')
        else:
            self.line(str(t))

    def deny(self, tool: str, reason: str) -> None:
        d = _c('DENY', 'red', attrs=['bold'])
        self.line(f'{d} {tool} ({reason})')

    def result(self, label: str, payload: Any) -> None:
        lab = _c(label, 'green')
        self.line(f'{lab}')
        for row in _highlight_json(payload).splitlines():
            self._emit(f'  {row}')

    def done(self, *, reason: str = '', policy: str = '', tools: int = 0, denied: int = 0) -> None:
        parts = ['done']
        if reason:
            parts.append(f'reason={reason}')
        if policy:
            parts.append(f'policy={policy}')
        if tools:
            parts.append(f'tools={tools}')
        if denied:
            parts.append(f'denied={denied}')
        self.line(_c(' '.join(parts), 'green'))
