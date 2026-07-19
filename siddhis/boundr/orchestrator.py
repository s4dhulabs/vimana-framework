# -*- coding: utf-8 -*-
# Orchestration entrypoints for boundr.

import asyncio
import sys
from typing import Any, Dict

from siddhis.boundr.engines.auditor import BoundrAuditor
from siddhis.boundr.engines.spec_manager import BoundrSpecManager, SpecResolutionError
from siddhis.boundr.reporters.ci_report import build_report, ci_exit_code, emit_report


def run_spec_scan(handler: dict) -> Dict[str, Any]:
    """Scan and register OpenAPI without upload audit."""
    spec_id, api_specs = BoundrSpecManager(handler).run_scan_sync()
    report = {
        'report_version': '1.0',
        'plugin': 'boundr',
        'action': 'scan',
        'spec_id': spec_id,
        'summary': {'passed': True, 'paths': len(api_specs.get('paths', {}))},
    }
    if handler.get('json_output') or handler.get('ci_mode'):
        import json
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write('\n')
    return report


def run_upload_audit(handler: dict, orchestrator: str = None) -> Dict[str, Any]:
    """
    Run multipart/upload security audit. Callable by future orchestrators.

    Example:
        from siddhis.boundr.orchestrator import run_upload_audit
        report = run_upload_audit(handler, orchestrator='uso')
    """
    audit_handler = dict(handler)
    if orchestrator:
        audit_handler['_orchestrator'] = orchestrator

    auditor = BoundrAuditor(audit_handler)
    raw = asyncio.run(auditor.run_async())

    report = build_report(
        plugin='boundr',
        orchestrator=orchestrator or handler.get('_orchestrator'),
        spec_id=raw.get('spec_id'),
        base_url=raw.get('base_url', ''),
        targets=raw.get('targets', []),
        candidates=raw.get('candidates', []),
        findings=raw.get('findings', []),
    )

    emit_report(report, audit_handler)

    if audit_handler.get('ci_mode'):
        sys.exit(ci_exit_code(report))

    return report
