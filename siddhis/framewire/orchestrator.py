# -*- coding: utf-8 -*-
# Orchestration entrypoints for framewire (WSO-ready).

import asyncio
import sys
from typing import Any, Dict

from siddhis.framewire.engines.auditor import FramewireAuditor
from siddhis.framewire.engines.spec_manager import FramewireSpecManager, SpecResolutionError
from siddhis.framewire.reporters.ci_report import build_report, ci_exit_code, emit_report


def run_spec_scan(handler: dict) -> Dict[str, Any]:
    """Scan and register OpenAPI without frame fuzz."""
    spec_id, api_specs = FramewireSpecManager(handler).run_scan_sync()
    report = {
        'report_version': '1.0',
        'plugin': 'framewire',
        'action': 'scan',
        'spec_id': spec_id,
        'summary': {'passed': True, 'paths': len(api_specs.get('paths', {}))},
    }
    if handler.get('json_output') or handler.get('ci_mode'):
        import json
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write('\n')
    return report


def run_frame_audit(handler: dict, orchestrator: str = None) -> Dict[str, Any]:
    """
    Run post-handshake WebSocket frame/message fuzz.
    Callable by future WSO orchestrator.

    Example:
        from siddhis.framewire.orchestrator import run_frame_audit
        report = run_frame_audit(handler, orchestrator='wso')
    """
    audit_handler = dict(handler)
    if orchestrator:
        audit_handler['_orchestrator'] = orchestrator

    auditor = FramewireAuditor(audit_handler)
    raw = asyncio.run(auditor.run_async())

    report = build_report(
        plugin='framewire',
        orchestrator=orchestrator or handler.get('_orchestrator'),
        spec_id=raw.get('spec_id'),
        base_url=raw.get('base_url', ''),
        targets=raw.get('targets', []),
        candidates=raw.get('candidates', []),
        findings=raw.get('findings', []),
    )

    emit_report(report, audit_handler)

    if audit_handler.get('ci_mode') and not audit_handler.get('_orchestrator'):
        sys.exit(ci_exit_code(report))

    return report
