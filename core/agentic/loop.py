# -*- coding: utf-8 -*-
"""Native agent loop — LLM planner + Control tools in-process."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from core.agentic.llm import LLMClient, tools_openai_schema
from core.agentic.policy import AgentPolicy, DEFAULT_POLICY, ToolRisk
from core.agentic.prompts import SYSTEM_PROMPT
from core.api.control.tools import call_tool, list_tools

LogFn = Callable[[str], None]
# Return True to proceed with EXECUTE; False denies the call.
ConfirmFn = Callable[[str, Dict[str, Any]], bool]


@dataclass
class AgentTurn:
    role: str
    content: str = ''
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Any = None
    denied: bool = False
    deny_reason: Optional[str] = None


@dataclass
class AgentResult:
    final: str
    turns: List[AgentTurn] = field(default_factory=list)
    tool_calls: int = 0
    denied_calls: int = 0
    stopped_reason: str = 'completed'
    policy: str = DEFAULT_POLICY


def _truncate(obj: Any, limit: int = 12000) -> str:
    """Serialize tool payload for the model; keep identity keys when shrinking."""
    text = obj if isinstance(obj, str) else json.dumps(obj, default=str, ensure_ascii=False)
    if len(text) <= limit:
        return text

    if isinstance(obj, dict):
        keep = (
            'run_id', 'plugin', 'status', 'url', 'ok', 'error', 'summary',
            'ports', 'running', 'valid', 'lab_path',
        )
        slim: Dict[str, Any] = {k: obj[k] for k in keep if k in obj}
        findings = obj.get('findings')
        if isinstance(findings, list):
            slim['findings_count'] = len(findings)
        elif findings is not None:
            slim['findings'] = findings
        report = obj.get('report')
        if isinstance(report, dict):
            slim['report_summary'] = report.get('summary')
            if 'findings' in report and isinstance(report['findings'], list):
                slim['report_findings_count'] = len(report['findings'])
        args = obj.get('args')
        if isinstance(args, dict):
            slim['args'] = {
                k: args[k] for k in ('target_url', 'upload_audit_enabled', 'name')
                if k in args
            }
        slim['_truncated'] = True
        text2 = json.dumps(slim, default=str, ensure_ascii=False)
        if len(text2) <= limit:
            return text2
        text = text2

    return text[: limit - 20] + '\n…[truncated]'


def run_agent(
    prompt: str,
    client: LLMClient,
    *,
    max_turns: int = 8,
    system: str = SYSTEM_PROMPT,
    policy: Optional[AgentPolicy] = None,
    log: Optional[LogFn] = None,
    confirm: Optional[ConfirmFn] = None,
) -> AgentResult:
    """Run tool-calling loop until the model stops or max_turns is hit."""
    os.environ.setdefault('VIMANA_QUIET_CONSOLE', '1')
    os.environ.setdefault('VIMANA_MCP', '1')

    _log = log or (lambda _m: None)
    pol = policy or AgentPolicy()
    descriptors = pol.filter_descriptors(list_tools())
    tools = tools_openai_schema(descriptors)
    hosts = sorted(pol.effective_target_hosts())
    target_note = (
        'EXECUTE targets: any (--allow-any-target).'
        if pol.allow_any_target
        else f'EXECUTE target hosts allowed: {", ".join(hosts) or "(none)"}.'
    )
    confirm_note = (
        ' Human confirmation required before EXECUTE.'
        if pol.require_confirm
        else ''
    )
    policy_note = (
        f'\n\nActive tool policy: {pol.name}. '
        f'Allowed tools ({len(descriptors)}): '
        + ', '.join(d['name'] for d in descriptors)
        + f'. {target_note}{confirm_note}'
    )
    messages: List[Dict[str, Any]] = [
        {'role': 'system', 'content': system + policy_note},
        {'role': 'user', 'content': prompt},
    ]
    history: List[AgentTurn] = [AgentTurn(role='user', content=prompt)]
    tool_calls_n = 0
    denied_n = 0

    for turn_i in range(max_turns):
        _log(f'[agent] turn {turn_i + 1}/{max_turns} policy={pol.name} → model')
        result = client.chat(messages, tools)

        if result.tool_calls:
            assistant_msg: Dict[str, Any] = {
                'role': 'assistant',
                'content': result.content or None,
                'tool_calls': [
                    {
                        'id': tc.id,
                        'type': 'function',
                        'function': {
                            'name': tc.name,
                            'arguments': json.dumps(tc.arguments or {}),
                        },
                    }
                    for tc in result.tool_calls
                ],
            }
            messages.append(assistant_msg)
            if result.content:
                history.append(AgentTurn(role='assistant', content=result.content))

            for tc in result.tool_calls:
                tool_calls_n += 1
                args_preview = json.dumps(tc.arguments or {}, ensure_ascii=False)[:200]
                decision = pol.check_args(tc.name, tc.arguments)

                if not decision.allowed:
                    denied_n += 1
                    payload = {
                        'error': 'tool_denied',
                        'tool': tc.name,
                        'policy': decision.policy,
                        'risk': decision.risk,
                        'reason': decision.reason,
                    }
                    _log(f'[agent] DENY {tc.name} ({decision.reason})')
                    text = _truncate(payload)
                    history.append(AgentTurn(
                        role='tool',
                        content=text,
                        tool_name=tc.name,
                        tool_args=tc.arguments,
                        tool_result=payload,
                        denied=True,
                        deny_reason=decision.reason,
                    ))
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tc.id,
                        'content': text,
                    })
                    continue

                risk = pol.risk_for(tc.name)
                if (
                    risk == ToolRisk.EXECUTE
                    and pol.require_confirm
                    and confirm is not None
                    and not confirm(tc.name, dict(tc.arguments or {}))
                ):
                    denied_n += 1
                    reason = 'human declined EXECUTE confirmation'
                    payload = {
                        'error': 'tool_denied',
                        'tool': tc.name,
                        'policy': pol.name,
                        'risk': risk.value,
                        'reason': reason,
                    }
                    _log(f'[agent] DENY {tc.name} ({reason})')
                    text = _truncate(payload)
                    history.append(AgentTurn(
                        role='tool',
                        content=text,
                        tool_name=tc.name,
                        tool_args=tc.arguments,
                        tool_result=payload,
                        denied=True,
                        deny_reason=reason,
                    ))
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tc.id,
                        'content': text,
                    })
                    continue

                _log(f'[agent] tool {tc.name}({args_preview})')
                try:
                    raw = call_tool(tc.name, tc.arguments or {})
                    payload = raw
                    is_err = False
                except Exception as exc:
                    payload = {'error': f'{type(exc).__name__}: {exc}'}
                    is_err = True
                text = _truncate(payload)
                history.append(AgentTurn(
                    role='tool',
                    content=text,
                    tool_name=tc.name,
                    tool_args=tc.arguments,
                    tool_result=payload,
                ))
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tc.id,
                    'content': text if not is_err else json.dumps(payload),
                })
            continue

        final = (result.content or '').strip()
        history.append(AgentTurn(role='assistant', content=final))
        messages.append({'role': 'assistant', 'content': final})
        _log('[agent] done')
        return AgentResult(
            final=final,
            turns=history,
            tool_calls=tool_calls_n,
            denied_calls=denied_n,
            stopped_reason='completed',
            policy=pol.name,
        )

    return AgentResult(
        final='(max turns reached)',
        turns=history,
        tool_calls=tool_calls_n,
        denied_calls=denied_n,
        stopped_reason='max_turns',
        policy=pol.name,
    )
