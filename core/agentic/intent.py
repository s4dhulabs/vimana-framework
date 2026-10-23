# -*- coding: utf-8 -*-
"""
Natural-language intent → deterministic playbook for the agent.

Short prompts map to Control tools without requiring a strong LLM:

  about the framework           →  vimana_about
  what is / how to use plugin X →  vimana_explain_plugin
  analyze this target http://…  →  vimana_analyze_target (fingerprint + triage)
  run plugin / siddhi / bare    →  vimana_run  (lab+test, stop lab after)
  run / start lab X             →  vimana_lab_start  (lab only)

Longer free-form prompts return None and fall through to the LLM loop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import FrozenSet, Optional, Set
from urllib.parse import urlparse


@dataclass(frozen=True)
class AgentIntent:
    """Resolved user intent for a short-circuit playbook."""

    kind: str  # about | plugin_info | plugin_usage | analyze_target | run_plugin | lab_only
    plugin: str = ''
    tool: str = ''
    arguments: dict = field(default_factory=dict)
    matched: str = ''


_URL = re.compile(r'(?i)\bhttps?://[^\s<>\'\"]+')

# "Analyze this target http://…" / "analise o target …" / bare analyze URL
_ANALYZE = re.compile(
    r'(?is)^\s*(?:please\s+|por\s+favor\s+)?'
    r'(?:'
    r'analyze|analyse|analise|analisar|scan|fingerprint|recon|triage'
    r'|audita|auditar|inspect|inspecionar'
    r')\b'
    r'.{0,160}?'
    r'(https?://[^\s<>\'\"]+)'
    r'(?:\s+with\s+follow[- ]?up)?'
    r'\s*[?.!]?\s*$'
)


_ABOUT = re.compile(
    r'(?is)^\s*(?:please\s+|por\s+favor\s+)?'
    r'(?:'
    r'(?:o\s+)?que\s+(?:é|e|eh)\s+(?:a\s+|o\s+)?vimana\??'
    r'|what\s+(?:is|\'?s)\s+(?:the\s+)?vimana(?:\s+framework)?\??'
    r'|tell\s+me\s+about\s+(?:the\s+)?vimana(?:\s+framework)?'
    r'|about\s+(?:the\s+)?vimana(?:\s+framework)?'
    r'|vimana\s+about'
    r'|explique\s+(?:a\s+|o\s+)?vimana'
    r'|sobre\s+(?:a\s+|o\s+)?vimana'
    r')\s*[?.!]?\s*$'
)

# "o que é o plugin framewalk" / "what is boundr" / "what does fetchbane do"
_PLUGIN_INFO = re.compile(
    r'(?is)^\s*(?:please\s+|por\s+favor\s+)?'
    r'(?:'
    r'(?:o\s+)?que\s+(?:é|e|eh)\s+(?:o\s+|a\s+)?'
    r'(?:(?:plugin|siddhi|module|módulo|modulo)\s+)?'
    r'|what\s+(?:is|\'?s)\s+(?:the\s+)?'
    r'(?:(?:plugin|siddhi|module)\s+)?'
    r'|what\s+does\s+(?:the\s+)?'
    r'(?:(?:plugin|siddhi|module)\s+)?'
    r'|explain\s+(?:the\s+)?'
    r'(?:(?:plugin|siddhi|module)\s+)?'
    r'|explique\s+(?:o\s+|a\s+)?'
    r'(?:(?:plugin|siddhi|module|módulo|modulo)\s+)?'
    r'|describe\s+(?:the\s+)?'
    r'(?:(?:plugin|siddhi|module)\s+)?'
    r'|info\s+(?:(?:on|about|do|da)\s+)?'
    r'(?:(?:plugin|siddhi)\s+)?'
    r'|vimana_explain_plugin\s+'
    r')'
    r'([a-zA-Z][\w-]*)'
    r'(?:\s+do|\s+plugin|\s+siddhi)?'
    r'\s*[?.!]?\s*$'
)

# "como usar o plugin X" / "how to use Y" / "guide for Z"
_PLUGIN_USAGE = re.compile(
    r'(?is)^\s*(?:please\s+|por\s+favor\s+)?'
    r'(?:'
    r'como\s+(?:usar|uso|rodar|executar|correr)\s+(?:o\s+|a\s+)?'
    r'(?:(?:plugin|siddhi|module|módulo|modulo)\s+)?'
    r'|how\s+(?:do\s+i\s+|to\s+|can\s+i\s+)?'
    r'(?:use|run|execute)\s+(?:the\s+)?'
    r'(?:(?:plugin|siddhi|module)\s+)?'
    r'|guide\s+(?:for|to)\s+(?:the\s+)?'
    r'(?:(?:plugin|siddhi|module)\s+)?'
    r'|help\s+(?:with|for)\s+(?:the\s+)?'
    r'(?:(?:plugin|siddhi|module)\s+)?'
    r'|args?\s+(?:(?:for|do|da|of)\s+)?'
    r'(?:(?:plugin|siddhi)\s+)?'
    r'|exemplos?\s+(?:(?:de|do|da|for)\s+)?'
    r'(?:(?:plugin|siddhi)\s+)?'
    r')'
    r'([a-zA-Z][\w-]*)'
    r'\s*[?.!]?\s*$'
)

# Lab-only patterns (checked before run-plugin).
_LAB_ONLY_PATTERNS = (
    re.compile(
        r'(?is)^\s*(?:please\s+|por\s+favor\s+)?'
        r'(?:rode|roda|rodar|start|iniciar|suba|sobe|subir|run|bring\s+up)\s+'
        r'(?:o\s+|a\s+|the\s+)?'
        r'lab\s+(?:do\s+|da\s+|de\s+|for\s+|of\s+|named\s+)?'
        r'([a-zA-Z][\w-]*)'
        r'\s*[.!]?\s*$'
    ),
    re.compile(
        r'(?is)^\s*(?:please\s+|por\s+favor\s+)?'
        r'(?:start|run|bring\s+up|iniciar|suba|sobe)\s+'
        r'(?:o\s+|a\s+|the\s+)?'
        r'([a-zA-Z][\w-]*)\s+lab'
        r'\s*[.!]?\s*$'
    ),
    re.compile(
        r'(?is)^\s*(?:lab_start|vimana_lab_start)\s+([a-zA-Z][\w-]*)\s*[.!]?\s*$'
    ),
)

_RUN_PLUGIN = re.compile(
    r'(?is)^\s*(?:please\s+|por\s+favor\s+)?'
    r'(?:'
    r'(?:rode|roda|rodar|run|execute|executar|executa|scan|fuzz|test|teste|testar)\s+'
    r'(?:o\s+|a\s+|the\s+)?'
    r'(?:(?:plugin|siddhi|module|módulo|modulo|auditor|tool)\s+)?'
    r'(?:(?:named|chamado|chamada)\s+)?'
    r'|vimana_run(?:_plugin)?\s+'
    r'|vimana_lab_test\s+'
    r')'
    r'([a-zA-Z][\w-]*)'
    r'(?:\s+(?:plugin|siddhi|module|against\s+(?:its\s+)?lab|no\s+lab)?)?'
    r'\s*[.!]?\s*$'
)

_BARE_NAME = re.compile(r'(?is)^\s*([a-zA-Z][\w-]*)\s*[.!]?\s*$')

_BARE_STOP: FrozenSet[str] = frozenset({
    'help', 'health', 'status', 'list', 'labs', 'plugins', 'lab', 'plugin',
    'siddhi', 'run', 'start', 'stop', 'ok', 'yes', 'no', 'oi', 'ola', 'olá',
    'vimana', 'about', 'info', 'guide',
})


def parse_agent_intent(
    prompt: str,
    *,
    known_plugins: Optional[Set[str]] = None,
) -> Optional[AgentIntent]:
    """
    Return a playbook intent when the prompt is a short, unambiguous command.
    Otherwise None (use the LLM planner).
    """
    text = (prompt or '').strip()
    # Allow slightly longer analyze prompts; free-form goals still fall through.
    if not text or len(text) > 400:
        return None

    known = {p.lower() for p in (known_plugins or set())}

    if _ABOUT.match(text):
        return AgentIntent(
            kind='about',
            tool='vimana_about',
            arguments={},
            matched='framework about / what is vimana',
        )

    m = _ANALYZE.match(text)
    if m:
        url = m.group(1).rstrip('.,);]')
        follow = bool(re.search(r'(?i)follow[- ]?up|continuar|siga|run\s+audits?', text))
        auto = bool(re.search(r'(?i)\bauto\b|full\s+suite|run\s+all', text))
        return AgentIntent(
            kind='analyze_target',
            tool='vimana_analyze_target',
            arguments={
                'target_url': url,
                'follow_up': follow or auto,
                'auto': auto,
            },
            matched='analyze / fingerprint target URL',
        )

    # URL + analyze-ish verb anywhere short (e.g. "http://x.com analyze stack")
    urls = _URL.findall(text)
    if urls and re.search(
        r'(?i)\b(analyze|analyse|analise|analisar|fingerprint|recon|triage)\b',
        text,
    ):
        url = urls[0].rstrip('.,);]')
        host = (urlparse(url).hostname or '').lower()
        if host:
            follow = bool(re.search(r'(?i)follow[- ]?up|continuar|run\s+audits?', text))
            auto = bool(re.search(r'(?i)\bauto\b|full\s+suite|run\s+all', text))
            return AgentIntent(
                kind='analyze_target',
                tool='vimana_analyze_target',
                arguments={
                    'target_url': url,
                    'follow_up': follow or auto,
                    'auto': auto,
                },
                matched='target URL + analyze verb',
            )

    m = _PLUGIN_USAGE.match(text)
    if m:
        plugin = m.group(1).lower()
        if plugin not in ('lab', 'plugin', 'siddhi', 'vimana'):
            low = text.lower()
            focus = 'args' if re.match(r'(?is)^\s*(?:please\s+|por\s+favor\s+)?args?\b', low) else 'usage'
            return AgentIntent(
                kind='plugin_usage',
                plugin=plugin,
                tool='vimana_explain_plugin',
                arguments={'name': plugin, 'focus': focus},
                matched='how to use / guide phrase',
            )

    m = _PLUGIN_INFO.match(text)
    if m:
        plugin = m.group(1).lower()
        if plugin not in ('lab', 'plugin', 'siddhi', 'vimana'):
            return AgentIntent(
                kind='plugin_info',
                plugin=plugin,
                tool='vimana_explain_plugin',
                arguments={'name': plugin, 'focus': 'overview'},
                matched='what is plugin / explain phrase',
            )

    for pat in _LAB_ONLY_PATTERNS:
        m = pat.match(text)
        if m:
            plugin = m.group(1).lower()
            if plugin == 'lab':
                continue
            return AgentIntent(
                kind='lab_only',
                plugin=plugin,
                tool='vimana_lab_start',
                arguments={'plugin': plugin},
                matched='lab-only phrase (no plugin run)',
            )

    m = _RUN_PLUGIN.match(text)
    if m:
        plugin = m.group(1).lower()
        if plugin == 'lab':
            return None
        return AgentIntent(
            kind='run_plugin',
            plugin=plugin,
            tool='vimana_run',
            arguments={'name': plugin, 'stop_lab_after': True},
            matched='run plugin / siddhi phrase',
        )

    m = _BARE_NAME.match(text)
    if m and known:
        token = m.group(1).lower()
        if token in _BARE_STOP:
            return None
        if token in known:
            return AgentIntent(
                kind='run_plugin',
                plugin=token,
                tool='vimana_run',
                arguments={'name': token, 'stop_lab_after': True},
                matched='bare plugin name',
            )

    return None
