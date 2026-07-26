# -*- coding: utf-8 -*-
# Orchestration entrypoints for schemage.

import asyncio
import sys
from typing import Any, Dict

from siddhis.schemage.engines.auditor import SchemageAuditor
from siddhis.schemage.engines.spec_manager import SchemageSpecManager, SpecResolutionError
from siddhis.schemage.reporters.ci_report import build_report, ci_exit_code, emit_report


def run_spec_scan(handler: dict) -> Dict[str, Any]:
    spec_id, api_specs = SchemageSpecManager(handler).run_scan_sync()
    report = {
        'report_version': '1.0',
        'plugin': 'schemage',
        'action': 'scan',
        'spec_id': spec_id,
        'summary': {'passed': True, 'paths': len(api_specs.get('paths', {}))},
    }
    if handler.get('json_output') or handler.get('ci_mode'):
        import json
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write('\n')
    return report


def run_gql_audit(handler: dict, orchestrator: str = None) -> Dict[str, Any]:
    audit_handler = dict(handler)
    if orchestrator:
        audit_handler['_orchestrator'] = orchestrator

    raw = asyncio.run(SchemageAuditor(audit_handler).run_async())
    report = build_report(
        plugin='schemage',
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
