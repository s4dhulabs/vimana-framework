# -*- coding: utf-8 -*-
# Orchestration entrypoints for fetchbane.

import asyncio
import sys
from typing import Any, Dict

from siddhis.fetchbane.engines.auditor import FetchbaneAuditor
from siddhis.fetchbane.engines.spec_manager import FetchbaneSpecManager, SpecResolutionError
from siddhis.fetchbane.reporters.ci_report import build_report, ci_exit_code, emit_report


def run_spec_scan(handler: dict) -> Dict[str, Any]:
    spec_id, api_specs = FetchbaneSpecManager(handler).run_scan_sync()
    report = {
        'report_version': '1.0',
        'plugin': 'fetchbane',
        'action': 'scan',
        'spec_id': spec_id,
        'summary': {'passed': True, 'paths': len(api_specs.get('paths', {}))},
    }
    if handler.get('json_output') or handler.get('ci_mode'):
        import json
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write('\n')
    return report


def run_ssrf_audit(handler: dict, orchestrator: str = None) -> Dict[str, Any]:
    audit_handler = dict(handler)
    if orchestrator:
        audit_handler['_orchestrator'] = orchestrator

    raw = asyncio.run(FetchbaneAuditor(audit_handler).run_async())
    report = build_report(
        plugin='fetchbane',
        orchestrator=orchestrator or handler.get('_orchestrator'),
        spec_id=raw.get('spec_id'),
        base_url=raw.get('base_url', ''),
        targets=raw.get('targets', []),
        candidates=raw.get('candidates', []),
        findings=raw.get('findings', []),
    )
    emit_report(report, audit_handler)
    if audit_handler.get('ci_mode') and not audit_handler.get('_orchestrator'):
        sys.exit(ci_exit_code(report, handler=audit_handler))
    return report
