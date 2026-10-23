# -*- coding: utf-8 -*-
"""
Tool descriptors + in-process dispatch for Control API / MCP (Fase 2.1).

Agents call these tools; implementations reuse core.api.control.services
(and related modules) — no parallel plugin engine.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.api.control import services
from core.api.control.runs import RUN_STORE

ToolHandler = Callable[[Dict[str, Any]], Any]


def _tool(
    name: str,
    description: str,
    properties: Dict[str, Any],
    required: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        'name': name,
        'description': description,
        'inputSchema': {
            'type': 'object',
            'properties': properties,
            'required': required or [],
            'additionalProperties': False,
        },
    }


TOOL_DESCRIPTORS: List[Dict[str, Any]] = [
    _tool(
        'vimana_health',
        'Control API / framework health (version, plugins loaded).',
        {},
    ),
    _tool(
        'vimana_about',
        'What is Vimana? Framework overview (same spirit as `vimana about`): '
        'summary, capabilities, version, CLI/docs pointers. Use for informational '
        'questions like "o que é a vimana?" / "what is vimana?".',
        {},
    ),
    _tool(
        'vimana_list_plugins',
        'List Vimana plugins (name, type, category, lab/orchestrator flags).',
        {},
    ),
    _tool(
        'vimana_get_plugin',
        'Full plugin detail from the catalog (description, guide args/examples/labs, form). '
        'Prefer vimana_explain_plugin for short Q&A.',
        {'name': {'type': 'string', 'description': 'Plugin name'}},
        ['name'],
    ),
    _tool(
        'vimana_explain_plugin',
        'Explain a plugin using its built-in guide (info, args, examples, labs, CLI hints). '
        'Use for "o que é o plugin X?", "how to use Y?", "como usar o siddhi Z?". '
        'focus=overview|usage|args.',
        {
            'name': {'type': 'string', 'description': 'Plugin / siddhi name'},
            'focus': {
                'type': 'string',
                'description': 'overview (default) | usage | args',
                'default': 'overview',
            },
        },
        ['name'],
    ),
    _tool(
        'vimana_analyze_target',
        'Analyze a live http(s) target: run fingerprint (framewalk) against target_url, '
        'extract frameworks, triage plugins in deterministic playbook order '
        '(FastAPI: jcolt→fff→pyserial→…; Django: sttinger→dmt→d4m8→…). '
        'Does NOT start Docker labs. Default recommend-only; auto=true runs the full queue. '
        'Remote hosts require agent --allow-target / --allow-any-target.',
        {
            'target_url': {
                'type': 'string',
                'description': 'http(s) URL of the API / web target',
            },
            'auto': {
                'type': 'boolean',
                'description': 'Run full triage queue after fingerprint (default false)',
                'default': False,
            },
            'follow_up': {
                'type': 'boolean',
                'description': 'Run candidates (limited); prefer auto for full queue',
                'default': False,
            },
            'follow_up_limit': {
                'type': 'integer',
                'description': 'Max plugins when follow_up=true and auto=false (0=all)',
                'default': 2,
            },
            'include_fuzzers': {
                'type': 'boolean',
                'description': 'Include fuzzer category in triage (auto enables this)',
                'default': False,
            },
            'fingerprint_plugin': {
                'type': 'string',
                'description': 'Fingerprint plugin (default framewalk)',
                'default': 'framewalk',
            },
        },
        ['target_url'],
    ),
    _tool(
        'vimana_run_plugin',
        'Run a plugin. Default async=true returns queued run (poll vimana_get_run). '
        'Pass specialty flags in args (e.g. target_url, upload_audit_enabled). '
        'For unknown stacks prefer vimana_analyze_target first.',
        {
            'name': {'type': 'string', 'description': 'Plugin name'},
            'args': {
                'type': 'object',
                'description': 'Handler args / specialty flags',
                'additionalProperties': True,
            },
            'async': {
                'type': 'boolean',
                'description': 'Enqueue background run (default true)',
                'default': True,
            },
        },
        ['name'],
    ),
    _tool(
        'vimana_list_runs',
        'List recent plugin runs (newest first).',
        {
            'limit': {
                'type': 'integer',
                'description': 'Max runs (1–200)',
                'default': 20,
            },
        },
    ),
    _tool(
        'vimana_get_run',
        'Get run status, report, stdout/stderr, and artifacts.',
        {'run_id': {'type': 'string'}},
        ['run_id'],
    ),
    _tool(
        'vimana_get_findings',
        'Findings slice for a completed run.',
        {'run_id': {'type': 'string'}},
        ['run_id'],
    ),
    _tool(
        'vimana_list_labs',
        'List all plugin labs and status (ready/running/invalid + URL).',
        {},
    ),
    _tool(
        'vimana_lab_status',
        'Status for one plugin lab.',
        {'plugin': {'type': 'string'}},
        ['plugin'],
    ),
    _tool(
        'vimana_lab_start',
        'Start a plugin lab (Docker) ONLY — does not run the plugin. '
        'Use when the user asks to start/run the lab (not the plugin/siddhi).',
        {'plugin': {'type': 'string'}},
        ['plugin'],
    ),
    _tool(
        'vimana_lab_stop',
        'Stop a plugin lab.',
        {'plugin': {'type': 'string'}},
        ['plugin'],
    ),
    _tool(
        'vimana_lab_cleanup',
        'Stop all running labs (global cleanup).',
        {},
    ),
    _tool(
        'vimana_lab_test',
        'Start lab if needed and run the plugin via composition.lab.run_hint '
        '(same as: vimana run --lab <plugin> --test). Requires the plugin to have a lab.',
        {'plugin': {'type': 'string', 'description': 'Plugin / siddhi name'}},
        ['plugin'],
    ),
    _tool(
        'vimana_run',
        'PREFERRED one-shot when the user says "run <plugin/siddhi>" / "rode o plugin X". '
        'If the plugin has a lab: start it (if needed), run against it via run_hint '
        '(--lab X --test), then stop the lab by default (avoids leftover Docker labs). '
        'If it has no lab: run the plugin directly (sync). '
        'Pass stop_lab_after=false to leave the lab running. '
        'Do NOT use this for lab-only requests — use vimana_lab_start instead.',
        {
            'name': {
                'type': 'string',
                'description': 'Plugin / siddhi name (e.g. framewalk, boundr)',
            },
            'stop_lab_after': {
                'type': 'boolean',
                'description': (
                    'Stop the lab after a lab-backed run (default true). '
                    'Set false to keep the lab up for follow-up work.'
                ),
                'default': True,
            },
        },
        ['name'],
    ),
    _tool(
        'vimana_list_specs',
        'List shared OpenAPI specs registered in the framework (_SPECS_).',
        {},
    ),
    _tool(
        'vimana_get_spec',
        'Load one OpenAPI spec metadata (+ body when include_body true).',
        {
            'spec_id': {'type': 'string'},
            'include_body': {
                'type': 'boolean',
                'default': False,
                'description': 'Include full OpenAPI JSON (can be large)',
            },
        },
        ['spec_id'],
    ),
    _tool(
        'vimana_list_channels',
        'List shared vulnerability channels (_CHANNELS_).',
        {
            'plugin': {'type': 'string'},
            'type': {'type': 'string'},
            'status': {'type': 'string'},
        },
    ),
    _tool(
        'vimana_list_cases',
        'List saved cases (_CASES_).',
        {},
    ),
    _tool(
        'vimana_run_case',
        'Replay a saved case via Control run (async by default).',
        {
            'case_id': {'type': 'string'},
            'async': {'type': 'boolean', 'default': True},
        },
        ['case_id'],
    ),
]


def list_tools() -> List[Dict[str, Any]]:
    return list(TOOL_DESCRIPTORS)


def get_tool(name: str) -> Optional[Dict[str, Any]]:
    for t in TOOL_DESCRIPTORS:
        if t['name'] == name:
            return t
    return None


def _run_to_dict(run: Any, *, include_report: bool = True) -> Dict[str, Any]:
    if run is None:
        return {'error': 'no run record'}
    return run.to_dict(include_report=include_report)


def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
    """Execute a tool by name; returns JSON-serializable payload."""
    args = dict(arguments or {})
    handlers: Dict[str, ToolHandler] = {
        'vimana_health': lambda a: services.health(),
        'vimana_about': lambda a: services.about(),
        'vimana_list_plugins': lambda a: {'plugins': services.list_plugins()},
        'vimana_get_plugin': _get_plugin,
        'vimana_explain_plugin': _explain_plugin,
        'vimana_analyze_target': _analyze_target,
        'vimana_run_plugin': _run_plugin,
        'vimana_list_runs': lambda a: {
            'runs': [
                r.to_dict(include_report=False)
                for r in RUN_STORE.list(limit=int(a.get('limit') or 20))
            ],
        },
        'vimana_get_run': _get_run,
        'vimana_get_findings': _get_findings,
        'vimana_list_labs': lambda a: {'labs': services.list_labs()},
        'vimana_lab_status': lambda a: services.lab_status(str(a['plugin'])),
        'vimana_lab_start': lambda a: services.lab_start(str(a['plugin'])),
        'vimana_lab_stop': lambda a: services.lab_stop(str(a['plugin'])),
        'vimana_lab_cleanup': lambda a: services.lab_cleanup(),
        'vimana_lab_test': lambda a: services.lab_test(str(a['plugin'])),
        'vimana_run': _run_playbook,
        'vimana_list_specs': _list_specs,
        'vimana_get_spec': _get_spec,
        'vimana_list_channels': _list_channels,
        'vimana_list_cases': _list_cases,
        'vimana_run_case': _run_case,
    }
    fn = handlers.get(name)
    if not fn:
        raise LookupError(f'unknown tool: {name}')
    return fn(args)


def _get_plugin(a: Dict[str, Any]) -> Any:
    detail = services.get_plugin(str(a['name']))
    if not detail:
        raise LookupError(f'plugin not found: {a["name"]}')
    return detail


def _explain_plugin(a: Dict[str, Any]) -> Any:
    return services.explain_plugin(str(a['name']), focus=str(a.get('focus') or 'overview'))


def _analyze_target(a: Dict[str, Any]) -> Any:
    from core.api.control.analyze import analyze_target

    return analyze_target(
        str(a['target_url']),
        fingerprint_plugin=str(a.get('fingerprint_plugin') or 'framewalk'),
        follow_up=bool(a.get('follow_up') or False),
        follow_up_limit=int(a.get('follow_up_limit') or 2),
        include_fuzzers=bool(a.get('include_fuzzers') or False),
        auto=bool(a.get('auto') or False),
    )


def _run_plugin(a: Dict[str, Any]) -> Any:
    async_job = a.get('async', True)
    if async_job is None:
        async_job = True
    run = services.run_plugin(
        str(a['name']),
        dict(a.get('args') or {}),
        async_job=bool(async_job),
    )
    return _run_to_dict(run, include_report=not async_job)


def _run_playbook(a: Dict[str, Any]) -> Any:
    # Default True: one-shot NL/agent runs should not leave Docker labs behind.
    stop = a.get('stop_lab_after')
    if stop is None:
        stop = True
    return services.run_plugin_playbook(
        str(a['name']),
        stop_lab_after=bool(stop),
    )


def _get_run(a: Dict[str, Any]) -> Any:
    run = RUN_STORE.get(str(a['run_id']))
    if not run:
        raise LookupError(f'run not found: {a["run_id"]}')
    return run.to_dict(include_report=True)


def _get_findings(a: Dict[str, Any]) -> Any:
    run = RUN_STORE.get(str(a['run_id']))
    if not run:
        raise LookupError(f'run not found: {a["run_id"]}')
    report = run.report or {}
    findings = report.get('findings')
    if findings is None and isinstance(report.get('summary'), dict):
        findings = report.get('summary', {}).get('findings')
    return {
        'run_id': run.run_id,
        'plugin': run.plugin,
        'status': run.status,
        'findings': findings if findings is not None else [],
        'summary': report.get('summary'),
    }


def _list_specs(a: Dict[str, Any]) -> Any:
    from core.api.control import resources as res
    return {'specs': res.list_specs()}


def _get_spec(a: Dict[str, Any]) -> Any:
    from core.api.control import resources as res
    include_body = bool(a.get('include_body'))
    detail = res.get_spec(str(a['spec_id']), include_body=include_body)
    if not detail:
        raise LookupError(f'spec not found: {a["spec_id"]}')
    return detail


def _list_channels(a: Dict[str, Any]) -> Any:
    from core.api.control import resources as res
    return {
        'channels': res.list_channels(
            plugin=a.get('plugin'),
            channel_type=a.get('type'),
            status=a.get('status'),
        ),
    }


def _list_cases(a: Dict[str, Any]) -> Any:
    from core.api.control import resources as res
    return {'cases': res.list_cases()}


def _run_case(a: Dict[str, Any]) -> Any:
    from core.api.control import resources as res
    async_job = a.get('async', True)
    if async_job is None:
        async_job = True
    run = res.run_case(str(a['case_id']), async_job=bool(async_job))
    return _run_to_dict(run, include_report=not async_job)
