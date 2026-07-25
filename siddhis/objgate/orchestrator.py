# -*- coding: utf-8 -*-
# Orchestration entrypoints for objgate.

import asyncio
import sys
from typing import Any, Dict

from siddhis.objgate.engines.auditor import ObjgateAuditor
from siddhis.objgate.engines.spec_manager import ObjgateSpecManager, SpecResolutionError
from siddhis.objgate.reporters.ci_report import build_report, ci_exit_code, emit_report


def run_spec_scan(handler: dict) -> Dict[str, Any]:
    """Scan and register OpenAPI without object authz audit."""
    spec_id, api_specs = ObjgateSpecManager(handler).run_scan_sync()
    report = {
        'report_version': '1.0',
        'plugin': 'objgate',
        'action': 'scan',
        'spec_id': spec_id,
        'summary': {'passed': True, 'paths': len(api_specs.get('paths', {}))},
    }
    if handler.get('json_output') or handler.get('ci_mode'):
        import json
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write('\n')
    return report


def run_obj_audit(handler: dict, orchestrator: str = None) -> Dict[str, Any]:
    """
    Run HTTP REST object-level authorization / BOLA audit.

    Example:
        from siddhis.objgate.orchestrator import run_obj_audit
        report = run_obj_audit(handler)
    """
    audit_handler = dict(handler)
    if orchestrator:
        audit_handler['_orchestrator'] = orchestrator

    auditor = ObjgateAuditor(audit_handler)
    raw = asyncio.run(auditor.run_async())

    report = build_report(
        plugin='objgate',
        orchestrator=orchestrator or handler.get('_orchestrator'),
        spec_id=raw.get('spec_id'),
        base_url=raw.get('base_url', ''),
        targets=raw.get('targets', []),
        candidates=raw.get('candidates', []),
        findings=raw.get('findings', []),
    )
    if raw.get('objects'):
        report['objects'] = raw['objects']

    emit_report(report, audit_handler)

    if audit_handler.get('ci_mode') and not audit_handler.get('_orchestrator'):
        sys.exit(ci_exit_code(report))

    return report
