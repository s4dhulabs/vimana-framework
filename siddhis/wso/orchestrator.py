# -*- coding: utf-8 -*-
# WSO — WebSockets Orchestrator entrypoints.

from __future__ import annotations

import sys
from typing import Any, Dict, List

from core.orchestration import OrchestratorRunner, OrchestratorStep, StepResult, load_entrypoint
from core.findings import ci_exit_code, emit_report
from siddhis.socketline.orchestrator import run_spec_scan as socketline_scan
from siddhis.wso import presentation as ui


ORCHESTRATOR_NAME = 'wso'

DEFAULT_STEPS = (
    OrchestratorStep(
        name='socketline',
        entrypoint=load_entrypoint('siddhis.socketline.orchestrator:run_ws_audit'),
    ),
    OrchestratorStep(
        name='framewire',
        entrypoint=load_entrypoint('siddhis.framewire.orchestrator:run_frame_audit'),
    ),
    OrchestratorStep(
        name='roomgate',
        entrypoint=load_entrypoint('siddhis.roomgate.orchestrator:run_room_audit'),
    ),
)


def _emit_report(report: Dict[str, Any], handler: dict) -> None:
    """Preserve WSO interactive presentation; otherwise use core findings emitter."""
    quiet_json = handler.get('json_output') or handler.get('ci_mode')
    if ui.is_interactive(handler) and not quiet_json:
        output_path = handler.get('output')
        if output_path:
            import json as _json
            with open(output_path, 'w') as handle:
                handle.write(_json.dumps(report, indent=2, default=str))
                handle.write('\n')
        ui.print_report(report)
        if output_path:
            print(f'[+] JSON report saved to {output_path}')
        if handler.get('sarif_output') or handler.get('sarif'):
            from core.findings import emit_sarif
            emit_sarif(report, handler)
        return
    emit_report(report, handler)


def _resolve_base_url(handler: dict) -> str:
    scan = handler.get('api_scan_enabled')
    if scan and scan not in (False, 'ENV_FALLBACK'):
        return str(scan).rstrip('/')
    target = handler.get('target_url')
    if target:
        return str(target).rstrip('/')
    return ''


def _selected_steps(handler: dict) -> List[OrchestratorStep]:
    skip_handshake = bool(handler.get('wso_skip_handshake'))
    skip_frames = bool(handler.get('wso_skip_frames'))
    skip_rooms = bool(handler.get('wso_skip_rooms'))
    steps = []
    for step in DEFAULT_STEPS:
        if step.name == 'socketline' and skip_handshake:
            continue
        if step.name == 'framewire' and skip_frames:
            continue
        if step.name == 'roomgate' and skip_rooms:
            continue
        steps.append(step)
    if not steps:
        raise ValueError(
            'No WSO steps selected (check --wso-skip-handshake / --wso-skip-frames / --wso-skip-rooms)'
        )
    return steps


def _align_ws_paths(handler: dict) -> dict:
    """Share concrete WS paths across steps; keep room templates for roomgate."""
    h = dict(handler)

    concrete = None
    for key in ('ws_path', 'frame_path'):
        val = h.get(key)
        if val and '{' not in str(val):
            concrete = val
            break

    room_path = h.get('room_path')
    if room_path and '{' not in str(room_path) and concrete is None:
        concrete = room_path

    if concrete:
        if not h.get('ws_path'):
            h['ws_path'] = concrete
        if not h.get('frame_path'):
            h['frame_path'] = concrete
        if not h.get('room_path'):
            # Derive a room template when path looks like /ws/room/<id>
            path = str(concrete)
            if any(seg in path for seg in ('/room/', '/channel/', '/secure/')):
                parts = path.rstrip('/').split('/')
                parts[-1] = '{id}'
                h['room_path'] = '/'.join(parts)

    h['ws_audit_enabled'] = True
    h['frame_audit_enabled'] = True
    h['room_audit_enabled'] = True
    return h


def run_wso(handler: dict) -> Dict[str, Any]:
    """
    Orchestrate WebSocket specialty plugins:
    socketline (handshake) → framewire (frames) → roomgate (room authz/IDOR).
    """
    interactive = ui.is_interactive(handler)
    work = _align_ws_paths(handler)
    base_url = _resolve_base_url(work)
    if not base_url and not work.get('apispec_enabled'):
        raise ValueError(
            'WSO requires --scan-api URL, --target-url URL, or --apispec ID'
        )

    steps = _selected_steps(work)

    spec_id = work.get('apispec_enabled')
    if spec_id in (False, 'ENV_FALLBACK', None):
        spec_id = None

    if interactive:
        ui.print_run_header(base_url, [s.name for s in steps], spec_id=spec_id)

    if not work.get('wso_skip_scan') and not spec_id:
        if interactive:
            ui.print_scan_start(base_url)
        scan_handler = dict(work)
        scan_handler['ci_mode'] = False
        scan_handler['json_output'] = False
        scan_handler['quiet_output'] = True
        scan_handler['no_metadata'] = True
        scan_handler['_orchestrator'] = ORCHESTRATOR_NAME
        scan_handler.pop('output', None)
        if base_url and not scan_handler.get('api_scan_enabled'):
            scan_handler['api_scan_enabled'] = base_url
        scan_report = socketline_scan(scan_handler)
        spec_id = scan_report.get('spec_id')
        if spec_id:
            work['apispec_enabled'] = spec_id
            if interactive:
                ui.print_scan_done(spec_id)

    if base_url and not work.get('target_url'):
        work['target_url'] = base_url

    def _on_start(name: str, index: int, total: int) -> None:
        if interactive:
            ui.print_step_start(name, index, total)

    def _on_done(result: StepResult, index: int, total: int) -> None:
        if interactive:
            summary = (result.report or {}).get('summary') or {}
            ui.print_step_done(result.name, step_summary=summary, error=result.error)

    runner = OrchestratorRunner(ORCHESTRATOR_NAME, steps)
    report = runner.run(work, on_step_start=_on_start, on_step_done=_on_done)

    if base_url and not report.get('base_url'):
        report['base_url'] = base_url
    if spec_id and not report.get('spec_id'):
        report['spec_id'] = spec_id

    _emit_report(report, handler)

    if handler.get('ci_mode'):
        sys.exit(ci_exit_code(report, handler=handler))

    return report
