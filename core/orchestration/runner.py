# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# Generic in-process orchestrator runner for Vimana.
# New orchestrators (WSO, and future SSO/USO) should use this — not jcolt-style
# hardcoded imports / handler mutation / sys.exit mid-chain.

from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence


Entrypoint = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class OrchestratorStep:
    """One leaf plugin step in an orchestration chain."""

    name: str
    entrypoint: Entrypoint
    """Callable(handler, orchestrator=name) -> report dict."""


@dataclass
class StepResult:
    name: str
    report: Dict[str, Any]
    error: Optional[str] = None


def load_entrypoint(path: str) -> Entrypoint:
    """
    Load 'package.module:function' as a callable.
    Keeps orchestrator config declarative without hardcoded imports in core.
    """
    if ':' not in path:
        raise ValueError(f'Invalid entrypoint path (expected module:function): {path}')
    module_name, func_name = path.split(':', 1)
    module = importlib.import_module(module_name)
    func = getattr(module, func_name, None)
    if not callable(func):
        raise ValueError(f'Entrypoint not callable: {path}')
    return func


def prepare_child_handler(handler: dict, orchestrator: str) -> dict:
    """
    Build an isolated handler for a leaf step.

    - Shallow copy (no shared mutation)
    - Disable ci_mode / json_output so children do not sys.exit or flood stdout
    - Stamp orchestrator id for report metadata
    """
    child = dict(handler)
    child['ci_mode'] = False
    child['json_output'] = False
    child['quiet_output'] = True
    child['no_metadata'] = True
    child.pop('output', None)
    child['_orchestrator'] = orchestrator
    return child


def aggregate_reports(
    *,
    orchestrator: str,
    base_url: str,
    spec_id: Any,
    step_results: Sequence[StepResult],
) -> Dict[str, Any]:
    """Merge leaf ci_report-shaped dicts into one orchestrator report."""
    findings: List[Dict[str, Any]] = []
    targets: List[Dict[str, Any]] = []
    candidates: List[Dict[str, Any]] = []
    steps_payload: List[Dict[str, Any]] = []

    counts = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}

    for step in step_results:
        report = step.report or {}
        step_findings = report.get('findings') or []
        findings.extend(step_findings)
        targets.extend(report.get('targets') or [])
        candidates.extend(report.get('candidates') or [])

        for item in step_findings:
            sev = item.get('severity', 'info')
            if sev in counts:
                counts[sev] += 1

        summary = report.get('summary') or {}
        steps_payload.append({
            'name': step.name,
            'plugin': report.get('plugin', step.name),
            'error': step.error,
            'spec_id': report.get('spec_id'),
            'summary': {
                'findings_total': summary.get('findings_total', len(step_findings)),
                'findings_high': summary.get('findings_high', 0),
                'findings_medium': summary.get('findings_medium', 0),
                'passed': summary.get('passed', step.error is None),
            },
        })

    actionable = counts['high'] + counts['medium']

    return {
        'report_version': '1.0',
        'plugin': orchestrator,
        'orchestrator': orchestrator,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'spec_id': spec_id,
        'base_url': base_url,
        'summary': {
            'steps': len(step_results),
            'steps_failed': sum(1 for s in step_results if s.error),
            'live_targets': len(targets),
            'candidates': len(candidates),
            'findings_total': len(findings),
            'findings_high': counts['high'],
            'findings_medium': counts['medium'],
            'findings_low': counts['low'],
            'findings_info': counts['info'],
            'actionable': actionable,
            'passed': counts['high'] == 0 and all(s.error is None for s in step_results),
        },
        'steps': steps_payload,
        'targets': targets,
        'candidates': candidates,
        'findings': findings,
    }


class OrchestratorRunner:
    """
    Sequential in-process runner for declared OrchestratorStep lists.

    Does not inherit jcolt patterns: no shared-handler mutation, no sys.argv
    sniffing, no post-init attribute poking, no YAML that doesn't execute.
    """

    def __init__(self, name: str, steps: Sequence[OrchestratorStep]):
        if not name:
            raise ValueError('orchestrator name is required')
        if not steps:
            raise ValueError('orchestrator requires at least one step')
        self.name = name
        self.steps = list(steps)

    def run(self, handler: dict) -> Dict[str, Any]:
        child = prepare_child_handler(handler, self.name)
        base_url = (
            child.get('api_scan_enabled')
            if child.get('api_scan_enabled') not in (False, None, 'ENV_FALLBACK')
            else child.get('target_url')
        ) or ''
        if isinstance(base_url, str):
            base_url = base_url.rstrip('/')

        step_results: List[StepResult] = []
        spec_id = child.get('apispec_enabled') or None
        if spec_id in (False, 'ENV_FALLBACK'):
            spec_id = None

        for step in self.steps:
            try:
                report = step.entrypoint(child, orchestrator=self.name)
                if not isinstance(report, dict):
                    raise TypeError(f'{step.name} entrypoint must return a dict report')
                if report.get('spec_id') and not spec_id:
                    spec_id = report['spec_id']
                    child['apispec_enabled'] = spec_id
                if report.get('base_url') and not base_url:
                    base_url = report['base_url']
                step_results.append(StepResult(name=step.name, report=report))
            except SystemExit as exc:
                step_results.append(StepResult(
                    name=step.name,
                    report={},
                    error=f'{step.name} called sys.exit({exc.code})',
                ))
            except Exception as exc:
                step_results.append(StepResult(
                    name=step.name,
                    report={},
                    error=str(exc),
                ))

        return aggregate_reports(
            orchestrator=self.name,
            base_url=base_url or '',
            spec_id=spec_id,
            step_results=step_results,
        )
