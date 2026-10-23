# -*- coding: utf-8 -*-
"""
Native agentic loop for Vimana (Fase 2.2).

CLI: vimana agent

Consumes Control tools in-process (same surface as MCP / HTTP /v1/tools).
LLM providers: ollama (OpenAI-compat), openai, scripted (smoke).

Security: fail-closed tool policy (see core.agentic.policy).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional
from uuid import uuid4

from core.agentic.llm import AgentLLMError, ScriptedClient, build_client
from core.agentic.loop import AgentResult, AgentTurn, run_agent
from core.agentic.intent import parse_agent_intent
from core.agentic.format_info import (
    format_about_answer,
    format_analyze_answer,
    format_plugin_answer,
)
from core.agentic.logfmt import AgentLog
from core.agentic.policy import DEFAULT_POLICY, VALID_POLICIES, AgentPolicy, ToolRisk
from core.agentic.scenarios import SCRIPTED_SCENARIOS, get_scenario
from core.api.control.tools import call_tool


def _agent_store_dir() -> Path:
    root = Path(os.path.expanduser(os.getenv('VIMANA_HOME') or '~/.vimana'))
    path = root / 'control' / 'agent'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_transcript(prompt: str, result: AgentResult, meta: dict) -> Optional[str]:
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]
    path = _agent_store_dir() / f'{run_id}.json'
    payload = {
        'run_id': run_id,
        'prompt': prompt,
        'meta': meta,
        'final': result.final,
        'tool_calls': result.tool_calls,
        'denied_calls': result.denied_calls,
        'policy': result.policy,
        'stopped_reason': result.stopped_reason,
        'turns': [
            {
                'role': t.role,
                'content': t.content,
                'tool_name': t.tool_name,
                'tool_args': t.tool_args,
                'denied': t.denied,
                'deny_reason': t.deny_reason,
            }
            for t in result.turns
        ],
    }
    path.write_text(json.dumps(payload, default=str, ensure_ascii=False, indent=2), encoding='utf-8')
    return str(path)


def _ns_str(handler_ns: Any, attr: str, *fallbacks: str) -> str:
    """Read attr; treat argparse False placeholders as unset."""
    val = getattr(handler_ns, attr, None)
    if val is False or val is None or val == '':
        for fb in fallbacks:
            env = os.getenv(fb)
            if env:
                return env
        return ''
    return str(val)


def _csv_set(raw: Any) -> List[str]:
    if raw is False or raw is None or raw == '':
        return []
    parts: List[str] = []
    if isinstance(raw, (list, tuple, set)):
        for x in raw:
            parts.extend(str(x).split(','))
    else:
        parts.extend(str(raw).split(','))
    return [p.strip() for p in parts if p.strip()]


def _build_policy(handler_ns: Any) -> AgentPolicy:
    name = _ns_str(handler_ns, 'agent_policy', 'VIMANA_AGENT_POLICY') or DEFAULT_POLICY
    allow = _csv_set(getattr(handler_ns, 'agent_allow_tools', None))
    deny = _csv_set(getattr(handler_ns, 'agent_deny_tools', None))
    targets = _csv_set(getattr(handler_ns, 'agent_allow_targets', None))
    env_allow = os.getenv('VIMANA_AGENT_ALLOW_TOOLS') or ''
    env_deny = os.getenv('VIMANA_AGENT_DENY_TOOLS') or ''
    env_targets = os.getenv('VIMANA_AGENT_ALLOW_TARGETS') or ''
    allow = list(dict.fromkeys(allow + _csv_set(env_allow)))
    deny = list(dict.fromkeys(deny + _csv_set(env_deny)))
    targets = list(dict.fromkeys(targets + _csv_set(env_targets)))

    allow_any = bool(getattr(handler_ns, 'agent_allow_any_target', False))
    if os.getenv('VIMANA_AGENT_ALLOW_ANY_TARGET', '').strip().lower() in (
        '1', 'true', 'yes', 'on',
    ):
        allow_any = True

    require_confirm = bool(getattr(handler_ns, 'agent_confirm', False))
    # --yes / scripted / env disables confirmation even if --confirm was set
    yes = bool(getattr(handler_ns, 'agent_yes', False))
    if os.getenv('VIMANA_AGENT_YES', '').strip().lower() in ('1', 'true', 'yes', 'on'):
        yes = True
    if yes:
        require_confirm = False

    return AgentPolicy.from_parts(
        name=name,
        allow=allow,
        deny=deny,
        targets=targets,
        allow_any_target=allow_any,
        require_confirm=require_confirm,
    )


def _confirm_execute(tool: str, arguments: dict) -> bool:
    preview = json.dumps(arguments or {}, ensure_ascii=False)[:300]
    print(
        f'\n[agent] CONFIRM EXECUTE {tool}\n  args={preview}\n  Proceed? [y/N] ',
        file=sys.stderr,
        end='',
    )
    try:
        answer = input().strip().lower()
    except EOFError:
        return False
    return answer in ('y', 'yes')


def _known_plugin_names() -> set:
    try:
        from core.api.control import services
        return {str(p.get('name') or '').lower() for p in services.list_plugins() if p.get('name')}
    except Exception:
        return set()


def _as_agent_log(log) -> AgentLog:
    if isinstance(log, AgentLog):
        return log
    return AgentLog(emit=log)


def _run_analyze_playbook(
    prompt: str,
    intent,
    *,
    policy: AgentPolicy,
    confirm_fn,
    alog: AgentLog,
    auto: bool = False,
) -> AgentResult:
    """Multi-stage analyze target with colored progress."""
    from core.api.control.analyze import analyze_target

    args = dict(intent.arguments or {})
    if auto:
        args['auto'] = True
        args['follow_up'] = True

    history = [AgentTurn(role='user', content=prompt)]
    decision = policy.check_args(intent.tool, args)
    if not decision.allowed:
        payload = {
            'error': 'tool_denied',
            'tool': intent.tool,
            'policy': decision.policy,
            'risk': decision.risk,
            'reason': decision.reason,
            'intent': intent.kind,
            'hint': (
                'Remote targets need --policy run and '
                '--allow-target <host> (or --allow-any-target).'
            ),
        }
        alog.deny(intent.tool, decision.reason)
        history.append(AgentTurn(
            role='tool',
            content=json.dumps(payload, ensure_ascii=False),
            tool_name=intent.tool,
            tool_args=args,
            tool_result=payload,
            denied=True,
            deny_reason=decision.reason,
        ))
        return AgentResult(
            final=json.dumps(payload, ensure_ascii=False, indent=2),
            turns=history,
            tool_calls=1,
            denied_calls=1,
            stopped_reason='playbook_denied',
            policy=policy.name,
        )

    if (
        policy.require_confirm
        and confirm_fn is not None
        and not confirm_fn(intent.tool, dict(args))
    ):
        reason = 'human declined EXECUTE confirmation'
        payload = {
            'error': 'tool_denied',
            'tool': intent.tool,
            'reason': reason,
            'intent': intent.kind,
        }
        alog.deny(intent.tool, reason)
        history.append(AgentTurn(
            role='tool',
            content=json.dumps(payload, ensure_ascii=False),
            tool_name=intent.tool,
            tool_args=args,
            tool_result=payload,
            denied=True,
            deny_reason=reason,
        ))
        return AgentResult(
            final=json.dumps(payload, ensure_ascii=False, indent=2),
            turns=history,
            tool_calls=1,
            denied_calls=1,
            stopped_reason='playbook_denied',
            policy=policy.name,
        )

    target = str(args.get('target_url') or '')
    mode = 'auto' if args.get('auto') else 'recommend'
    alog.stage('analyze', f'{mode} → {target}', status='run')
    alog.line(f'matched: {intent.matched}')

    def on_progress(stage: str, detail: str, extra: dict) -> None:
        st = 'run'
        low = detail.lower()
        if stage == 'fingerprint' and low.startswith('ok'):
            st = 'ok'
        elif stage in ('fingerprint', 'follow-up', 'auto') and (
            low.startswith('fail') or ' fail' in f' {low}'
        ):
            st = 'fail'
        elif stage in ('framework', 'triage') and 'candidate' in low:
            st = 'ok'
        elif stage == 'recommend':
            st = 'skip'
        elif stage in ('framework', 'triage') and not low.startswith('matching'):
            st = 'ok'
        alog.stage(stage, detail, status=st)

    try:
        payload = analyze_target(
            target,
            follow_up=bool(args.get('follow_up')),
            follow_up_limit=int(args.get('follow_up_limit') or 2),
            include_fuzzers=bool(args.get('include_fuzzers')),
            auto=bool(args.get('auto')),
            fingerprint_plugin=str(args.get('fingerprint_plugin') or 'framewalk'),
            on_progress=on_progress,
        )
    except Exception as exc:
        payload = {
            'ok': False,
            'error': f'{type(exc).__name__}: {exc}',
            'target_url': target,
            'stage': 'analyze',
        }
        alog.stage('analyze', f'fail: {exc}', status='fail')

    tool_calls_n = 1 + len((payload or {}).get('follow_ups') or []) if isinstance(payload, dict) else 1
    history.append(AgentTurn(
        role='tool',
        content=json.dumps(payload, default=str, ensure_ascii=False)[:16000],
        tool_name=intent.tool,
        tool_args=args,
        tool_result=payload,
    ))
    final = format_analyze_answer(payload if isinstance(payload, dict) else {})
    history.append(AgentTurn(role='assistant', content=final))
    alog.done(reason='playbook', policy=policy.name, tools=tool_calls_n)
    return AgentResult(
        final=final,
        turns=history,
        tool_calls=tool_calls_n,
        denied_calls=0,
        stopped_reason='playbook',
        policy=policy.name,
    )


def _run_intent_playbook(
    prompt: str,
    *,
    policy: AgentPolicy,
    confirm_fn,
    log,
    auto: bool = False,
) -> Optional[AgentResult]:
    """
    Deterministic short-circuit for short NL commands.
    Returns AgentResult when handled; None to fall through to the LLM.
    """
    intent = parse_agent_intent(prompt, known_plugins=_known_plugin_names())
    if intent is None:
        return None

    alog = _as_agent_log(log)
    if intent.kind == 'analyze_target':
        return _run_analyze_playbook(
            prompt, intent, policy=policy, confirm_fn=confirm_fn, alog=alog,
            auto=auto,
        )

    decision = policy.check_args(intent.tool, intent.arguments)
    history = [AgentTurn(role='user', content=prompt)]
    if not decision.allowed:
        payload = {
            'error': 'tool_denied',
            'tool': intent.tool,
            'policy': decision.policy,
            'risk': decision.risk,
            'reason': decision.reason,
            'intent': intent.kind,
            'plugin': intent.plugin,
        }
        alog.deny(intent.tool, decision.reason)
        history.append(AgentTurn(
            role='tool',
            content=json.dumps(payload, ensure_ascii=False),
            tool_name=intent.tool,
            tool_args=intent.arguments,
            tool_result=payload,
            denied=True,
            deny_reason=decision.reason,
        ))
        return AgentResult(
            final=json.dumps(payload, ensure_ascii=False, indent=2),
            turns=history,
            tool_calls=1,
            denied_calls=1,
            stopped_reason='playbook_denied',
            policy=policy.name,
        )

    risk = policy.risk_for(intent.tool)
    if (
        risk == ToolRisk.EXECUTE
        and policy.require_confirm
        and confirm_fn is not None
        and not confirm_fn(intent.tool, dict(intent.arguments))
    ):
        reason = 'human declined EXECUTE confirmation'
        payload = {
            'error': 'tool_denied',
            'tool': intent.tool,
            'reason': reason,
            'intent': intent.kind,
            'plugin': intent.plugin,
        }
        alog.deny(intent.tool, reason)
        history.append(AgentTurn(
            role='tool',
            content=json.dumps(payload, ensure_ascii=False),
            tool_name=intent.tool,
            tool_args=intent.arguments,
            tool_result=payload,
            denied=True,
            deny_reason=reason,
        ))
        return AgentResult(
            final=json.dumps(payload, ensure_ascii=False, indent=2),
            turns=history,
            tool_calls=1,
            denied_calls=1,
            stopped_reason='playbook_denied',
            policy=policy.name,
        )

    alog.stage(
        intent.kind,
        f"{intent.tool}({json.dumps(intent.arguments, ensure_ascii=False)}) [{intent.matched}]",
        status='run',
    )
    try:
        payload = call_tool(intent.tool, intent.arguments)
    except Exception as exc:
        payload = {
            'ok': False,
            'error': f'{type(exc).__name__}: {exc}',
            'tool': intent.tool,
            'plugin': intent.plugin,
            'intent': intent.kind,
        }

    history.append(AgentTurn(
        role='tool',
        content=json.dumps(payload, default=str, ensure_ascii=False)[:12000],
        tool_name=intent.tool,
        tool_args=intent.arguments,
        tool_result=payload,
    ))

    if intent.kind == 'about':
        final = format_about_answer(payload if isinstance(payload, dict) else {})
    elif intent.kind in ('plugin_info', 'plugin_usage'):
        final = format_plugin_answer(payload if isinstance(payload, dict) else {})
    elif intent.kind == 'lab_only':
        final = (
            f"Lab-only playbook for '{intent.plugin}': started via {intent.tool}. "
            f"ok={payload.get('ok') if isinstance(payload, dict) else None} "
            f"running={payload.get('running') if isinstance(payload, dict) else None} "
            f"url={payload.get('url') if isinstance(payload, dict) else None}"
        )
    else:
        run = payload.get('run') if isinstance(payload, dict) else None
        run_id = run.get('run_id') if isinstance(run, dict) else None
        final = (
            f"Run playbook for '{intent.plugin}' via {intent.tool} "
            f"(mode={payload.get('mode') if isinstance(payload, dict) else None}). "
            f"ok={payload.get('ok') if isinstance(payload, dict) else None} "
            f"run_id={run_id} url={payload.get('url') if isinstance(payload, dict) else None} "
            f"lab_stopped={payload.get('lab_stopped') if isinstance(payload, dict) else None}"
        )
    history.append(AgentTurn(role='assistant', content=final))
    alog.done(reason='playbook', policy=policy.name, tools=1)
    return AgentResult(
        final=final,
        turns=history,
        tool_calls=1,
        denied_calls=0,
        stopped_reason='playbook',
        policy=policy.name,
    )


def run_agent_cli(handler_ns: Any) -> AgentResult:
    show_policy = bool(getattr(handler_ns, 'agent_show_policy', False))
    policy = _build_policy(handler_ns)

    if show_policy:
        print(json.dumps(policy.describe(), indent=2, ensure_ascii=False))
        sys.exit(0)

    # Keep plugin Rich/banners out of the agent TTY (playbook + LLM paths).
    os.environ.setdefault('VIMANA_QUIET_CONSOLE', '1')
    os.environ.setdefault('VIMANA_MCP', '1')

    prompt = (
        getattr(handler_ns, 'agent_prompt', None)
        or getattr(handler_ns, 'prompt', None)
        or ''
    )
    if prompt is False:
        prompt = ''
    prompt = str(prompt).strip()
    if not prompt:
        print('[agent] missing prompt — usage: vimana agent "your goal"', file=sys.stderr)
        print(
            f'[agent] policies: {", ".join(VALID_POLICIES)} (default={DEFAULT_POLICY})',
            file=sys.stderr,
        )
        sys.exit(2)

    provider = _ns_str(handler_ns, 'agent_provider', 'VIMANA_AGENT_PROVIDER') or 'ollama'
    model = _ns_str(handler_ns, 'agent_model', 'VIMANA_AGENT_MODEL')
    base_url = _ns_str(handler_ns, 'agent_base_url', 'VIMANA_AGENT_BASE_URL') or None
    api_key = _ns_str(handler_ns, 'agent_api_key', 'VIMANA_AGENT_API_KEY') or 'ollama'

    max_turns_raw = getattr(handler_ns, 'agent_max_turns', None)
    if max_turns_raw is False or max_turns_raw is None:
        max_turns = int(os.getenv('VIMANA_AGENT_MAX_TURNS') or 8)
    else:
        max_turns = int(max_turns_raw)

    as_json = bool(getattr(handler_ns, 'agent_json', False))
    quiet = bool(getattr(handler_ns, 'agent_quiet', False))
    no_save = bool(getattr(handler_ns, 'agent_no_save', False))

    # Optional scripted scenarios (deny smoke / boundr e2e)
    scripted_deny = bool(getattr(handler_ns, 'agent_scripted_deny', False))
    scenario_raw = getattr(handler_ns, 'agent_scripted_scenario', None)
    scenario = '' if scenario_raw is False or scenario_raw is None else str(scenario_raw).strip()
    if provider == 'scripted' and scripted_deny and not scenario:
        scenario = 'deny'
    if provider == 'scripted' and scenario:
        try:
            client = ScriptedClient(get_scenario(scenario))
        except ValueError as exc:
            print(f'[agent] {exc}', file=sys.stderr)
            sys.exit(2)
        # Boundr e2e needs room for lab + run + findings + stop
        if scenario == 'boundr' and max_turns < 10:
            max_turns = 10
    else:
        client = build_client(
            str(provider),
            model=str(model),
            base_url=base_url,
            api_key=str(api_key),
        )
        # Surface resolved model (auto-pick may differ from argparse default)
        resolved_model = getattr(client, 'model', model) or model
        if resolved_model and resolved_model != model:
            model = str(resolved_model)
    def _emit(msg: str) -> None:
        if not quiet and not as_json:
            print(msg, file=sys.stderr)

    alog = AgentLog(emit=_emit)
    alog.line(f'policy={policy.name} allowed={len(policy.allowed_tool_names())}')
    if provider != 'scripted':
        alog.line(f'provider={provider} model={model or getattr(client, "model", "?")}')
    if policy.allow_any_target:
        alog.line('targets=ANY')
    else:
        alog.line(f'targets={sorted(policy.effective_target_hosts())}')
    if policy.require_confirm:
        alog.line('confirm=on (EXECUTE will prompt)')

    confirm_fn = _confirm_execute if policy.require_confirm else None
    # Scripted / --yes never prompts even if somehow require_confirm stayed on
    if provider == 'scripted' or bool(getattr(handler_ns, 'agent_yes', False)):
        confirm_fn = None
        policy.require_confirm = False

    agent_auto = bool(getattr(handler_ns, 'agent_auto', False))
    if os.getenv('VIMANA_AGENT_AUTO', '').strip().lower() in ('1', 'true', 'yes', 'on'):
        agent_auto = True
    if agent_auto:
        alog.line('auto=on (analyze will run full triage queue)')

    # Deterministic NL playbook (skip when a scripted scenario drives the client)
    result: Optional[AgentResult] = None
    if not (provider == 'scripted' and scenario):
        result = _run_intent_playbook(
            prompt, policy=policy, confirm_fn=confirm_fn, log=alog, auto=agent_auto,
        )

    try:
        if result is None:
            result = run_agent(
                prompt, client, max_turns=max_turns, policy=policy,
                log=alog.line, confirm=confirm_fn,
            )
    except AgentLLMError as exc:
        print(f'[agent] {exc}', file=sys.stderr)
        sys.exit(1)
    transcript = None
    if not no_save:
        try:
            transcript = _save_transcript(prompt, result, {
                'provider': str(provider),
                'model': str(model),
                'base_url': base_url,
                'max_turns': max_turns,
                'policy': policy.name,
                'extra_allow': sorted(policy.extra_allow),
                'extra_deny': sorted(policy.extra_deny),
                'allow_any_target': policy.allow_any_target,
                'target_hosts': sorted(policy.target_hosts),
                'effective_target_hosts': sorted(policy.effective_target_hosts()),
                'require_confirm': policy.require_confirm,
            })
        except OSError as exc:
            alog.line(f'transcript save failed: {exc}')

    if as_json:
        print(json.dumps({
            'final': result.final,
            'tool_calls': result.tool_calls,
            'denied_calls': result.denied_calls,
            'policy': result.policy,
            'stopped_reason': result.stopped_reason,
            'transcript': transcript,
            'turns': [
                {
                    'role': t.role,
                    'content': t.content[:2000] if t.content else '',
                    'tool_name': t.tool_name,
                    'tool_args': t.tool_args,
                    'denied': t.denied,
                    'deny_reason': t.deny_reason,
                }
                for t in result.turns
            ],
        }, default=str, ensure_ascii=False, indent=2))
    else:
        print()
        print(result.final)
        print(file=sys.stderr)
        extra = f' transcript={transcript}' if transcript else ''
        alog.line(
            f'policy={result.policy} tools={result.tool_calls} '
            f'denied={result.denied_calls} reason={result.stopped_reason}{extra}'
        )
    return result


__all__ = [
    'run_agent',
    'run_agent_cli',
    'AgentResult',
    'AgentPolicy',
    'build_client',
    'SCRIPTED_SCENARIOS',
    'get_scenario',
    'parse_agent_intent',
]