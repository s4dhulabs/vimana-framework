# -*- coding: utf-8 -*-
# Orchestration entrypoints for roomgate (WSO-ready).

import asyncio
import sys
from typing import Any, Dict

from siddhis.roomgate.engines.auditor import RoomgateAuditor
from siddhis.roomgate.engines.spec_manager import RoomgateSpecManager, SpecResolutionError
from siddhis.roomgate.reporters.ci_report import build_report, ci_exit_code, emit_report


def run_spec_scan(handler: dict) -> Dict[str, Any]:
    """Scan and register OpenAPI without room authz audit."""
    spec_id, api_specs = RoomgateSpecManager(handler).run_scan_sync()
    report = {
        'report_version': '1.0',
        'plugin': 'roomgate',
        'action': 'scan',
        'spec_id': spec_id,
        'summary': {'passed': True, 'paths': len(api_specs.get('paths', {}))},
    }
    if handler.get('json_output') or handler.get('ci_mode'):
        import json
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write('\n')
    return report


def run_room_audit(handler: dict, orchestrator: str = None) -> Dict[str, Any]:
    """
    Run WebSocket room/channel authorization & IDOR audit.
    Callable by WSO orchestrator.

    Example:
        from siddhis.roomgate.orchestrator import run_room_audit
        report = run_room_audit(handler, orchestrator='wso')
    """
    audit_handler = dict(handler)
    if orchestrator:
        audit_handler['_orchestrator'] = orchestrator

    auditor = RoomgateAuditor(audit_handler)
    raw = asyncio.run(auditor.run_async())

    report = build_report(
        plugin='roomgate',
        orchestrator=orchestrator or handler.get('_orchestrator'),
        spec_id=raw.get('spec_id'),
        base_url=raw.get('base_url', ''),
        targets=raw.get('targets', []),
        candidates=raw.get('candidates', []),
        findings=raw.get('findings', []),
    )
    if raw.get('rooms'):
        report['rooms'] = raw['rooms']

    emit_report(report, audit_handler)

    if audit_handler.get('ci_mode') and not audit_handler.get('_orchestrator'):
        sys.exit(ci_exit_code(report))

    return report
