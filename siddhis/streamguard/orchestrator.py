# -*- coding: utf-8 -*-
# Orchestration entrypoints for streamguard (orchestrator-ready).

import asyncio
import sys
from typing import Any, Dict

from siddhis.streamguard.engines.auditor import StreamguardAuditor
from siddhis.streamguard.engines.spec_manager import SpecResolutionError, StreamguardSpecManager
from siddhis.streamguard.reporters.ci_report import build_report, ci_exit_code, emit_report


def run_spec_scan(handler: dict) -> Dict[str, Any]:
    """Scan and register OpenAPI without streaming audit."""
    spec_id, api_specs = StreamguardSpecManager(handler).run_scan_sync()
    report = {
        'report_version': '1.0',
        'plugin': 'streamguard',
        'action': 'scan',
        'spec_id': spec_id,
        'summary': {'passed': True, 'paths': len(api_specs.get('paths', {}))},
    }
    if handler.get('json_output') or handler.get('ci_mode'):
        import json
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write('\n')
    return report


def run_stream_audit(handler: dict, orchestrator: str = None) -> Dict[str, Any]:
    """
    Run SSE/streaming security audit. Callable by future orchestrators.

    Example (future):
        from siddhis.streamguard.orchestrator import run_stream_audit
        report = run_stream_audit(handler, orchestrator='sso')
    """
    audit_handler = dict(handler)
    if orchestrator:
        audit_handler['_orchestrator'] = orchestrator

    auditor = StreamguardAuditor(audit_handler)
    raw = asyncio.run(auditor.run_async())

    report = build_report(
        plugin='streamguard',
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
