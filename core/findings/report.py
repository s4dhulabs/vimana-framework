# -*- coding: utf-8 -*-
# Shared CI/JSON report builders for all Vimana auditors.

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from .models import Finding, Report, Summary
from .severity import ExitPolicy, Severity, resolve_exit_code
from .sarif import emit_sarif


REPORT_VERSION = '1.0'


def _as_finding_dicts(findings: List[Any]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for item in findings or []:
        if isinstance(item, Finding):
            result.append(item.to_dict())
        elif isinstance(item, dict):
            # Preserve existing keys; normalize severity
            row = dict(item)
            row['severity'] = Severity.normalize(row.get('severity')).value
            result.append(row)
        else:
            result.append({'target': str(item), 'check': 'unknown', 'severity': 'info', 'detail': str(item), 'evidence': {}})
    return result


def _severity_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}
    for item in findings:
        severity = Severity.normalize(item.get('severity')).value
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
    findings: List[Any],
    orchestrator: str = None,
) -> Dict[str, Any]:
    finding_rows = _as_finding_dicts(findings)
    counts = _severity_counts(finding_rows)
    actionable = [f for f in finding_rows if f.get('severity') in ('high', 'medium')]
    summary = Summary(
        live_targets=len(targets or []),
        candidates=len(candidates or []),
        findings_total=len(finding_rows),
        findings_high=counts['high'],
        findings_medium=counts['medium'],
        findings_low=counts['low'],
        findings_info=counts['info'],
        actionable=len(actionable),
        passed=counts['high'] == 0,
    )
    report = Report(
        report_version=REPORT_VERSION,
        plugin=plugin,
        orchestrator=orchestrator,
        generated_at=datetime.now(timezone.utc).isoformat(),
        spec_id=spec_id,
        base_url=base_url or '',
        summary=summary,
        targets=list(targets or []),
        candidates=list(candidates or []),
        findings=finding_rows,
    )
    return report.to_dict()


def emit_report(report: Dict[str, Any], handler: dict) -> None:
    handler = handler or {}
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

    # Optional SARIF side-channel
    if handler.get('sarif') or handler.get('sarif_output'):
        emit_sarif(report, handler)


def ci_exit_code(
    report: Dict[str, Any],
    policy: Optional[Union[ExitPolicy, str]] = None,
    handler: Optional[dict] = None,
) -> int:
    if isinstance(policy, str):
        policy = ExitPolicy(fail_on=Severity.normalize(policy))
    elif policy is None:
        policy = ExitPolicy.from_handler(handler)
    summary = report.get('summary', {}) if isinstance(report, dict) else {}
    return resolve_exit_code(summary, policy)
