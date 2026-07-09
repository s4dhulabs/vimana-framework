# -*- coding: utf-8 -*-
# CI/CD JSON report helpers for socketline.

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List


REPORT_VERSION = '1.0'


def _severity_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}
    for item in findings:
        severity = item.get('severity', 'info')
        if severity in counts:
            counts[severity] += 1
    return counts


def build_report(
    *,
    plugin: str,
    spec_id,
    base_url: str,
    targets: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
    orchestrator: str = None,
) -> Dict[str, Any]:
    counts = _severity_counts(findings)
    actionable = [f for f in findings if f.get('severity') in ('high', 'medium')]

    return {
        'report_version': REPORT_VERSION,
        'plugin': plugin,
        'orchestrator': orchestrator,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'spec_id': spec_id,
        'base_url': base_url,
        'summary': {
            'live_targets': len(targets),
            'candidates': len(candidates),
            'findings_total': len(findings),
            'findings_high': counts['high'],
            'findings_medium': counts['medium'],
            'findings_low': counts['low'],
            'findings_info': counts['info'],
            'actionable': len(actionable),
            'passed': counts['high'] == 0,
        },
        'targets': targets,
        'candidates': candidates,
        'findings': findings,
    }


def emit_report(report: Dict[str, Any], handler: dict) -> None:
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


def ci_exit_code(report: Dict[str, Any]) -> int:
    """Non-zero when high-severity findings exist (CI gate)."""
    if report.get('summary', {}).get('findings_high', 0) > 0:
        return 1
    return 0
