# -*- coding: utf-8 -*-
# WSO — WebSockets Orchestrator entrypoints.

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

from core.orchestration import OrchestratorRunner, OrchestratorStep, load_entrypoint
from siddhis.socketline.orchestrator import run_spec_scan as socketline_scan


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
)


def _emit_report(report: Dict[str, Any], handler: dict) -> None:
    payload = json.dumps(report, indent=2, default=str)
    output_path = handler.get('output')
    if output_path:
        with open(output_path, 'w') as handle:
            handle.write(payload)
            handle.write('\n')
    if handler.get('json_output') or handler.get('ci_mode'):
        sys.stdout.write(payload)
        sys.stdout.write('\n')
    elif output_path and not handler.get('quiet_output'):
        print(f'[+] Report saved to {output_path}')


def _ci_exit_code(report: Dict[str, Any]) -> int:
    if report.get('summary', {}).get('findings_high', 0) > 0:
        return 1
    return 0


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
    steps = []
    for step in DEFAULT_STEPS:
        if step.name == 'socketline' and skip_handshake:
            continue
        if step.name == 'framewire' and skip_frames:
            continue
        steps.append(step)
    if not steps:
        raise ValueError(
            'No WSO steps selected (both --wso-skip-handshake and --wso-skip-frames?)'
        )
    return steps


def _align_ws_paths(handler: dict) -> dict:
    """Share explicit WS path across handshake + frame steps when only one is set."""
    h = dict(handler)
    ws_path = h.get('ws_path') or h.get('frame_path')
    if ws_path:
        if not h.get('ws_path'):
            h['ws_path'] = ws_path
        if not h.get('frame_path'):
            h['frame_path'] = ws_path
    h['ws_audit_enabled'] = True
    h['frame_audit_enabled'] = True
    return h


def run_wso(handler: dict) -> Dict[str, Any]:
    """
    Orchestrate WebSocket specialty plugins: socketline (handshake) → framewire (frames).
    """
    work = _align_ws_paths(handler)
    base_url = _resolve_base_url(work)
    if not base_url and not work.get('apispec_enabled'):
        raise ValueError(
            'WSO requires --scan-api URL, --target-url URL, or --apispec ID'
        )

    spec_id = work.get('apispec_enabled')
    if spec_id in (False, 'ENV_FALLBACK', None):
        spec_id = None

    if not work.get('wso_skip_scan') and not spec_id:
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

    if base_url and not work.get('target_url'):
        work['target_url'] = base_url

    runner = OrchestratorRunner(ORCHESTRATOR_NAME, _selected_steps(work))
    report = runner.run(work)

    if base_url and not report.get('base_url'):
        report['base_url'] = base_url
    if spec_id and not report.get('spec_id'):
        report['spec_id'] = spec_id

    _emit_report(report, handler)

    if handler.get('ci_mode'):
        sys.exit(_ci_exit_code(report))

    return report
