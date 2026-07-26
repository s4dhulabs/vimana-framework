# -*- coding: utf-8 -*-
# Canonical finding / report dataclasses.

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from .severity import Severity


@dataclass
class Finding:
    target: str
    check: str
    severity: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    endpoint: Optional[str] = None
    method: Optional[str] = None
    confidence: Optional[str] = None
    cwe: Optional[Union[str, List[str]]] = None

    def normalized_severity(self) -> Severity:
        return Severity.normalize(self.severity)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            'target': self.target,
            'check': self.check,
            'severity': self.normalized_severity().value,
            'detail': self.detail,
            'evidence': dict(self.evidence or {}),
        }
        if self.endpoint:
            payload['endpoint'] = self.endpoint
        if self.method:
            payload['method'] = self.method
        if self.confidence:
            payload['confidence'] = self.confidence
        if self.cwe:
            payload['cwe'] = self.cwe
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Finding':
        return cls(
            target=str(data.get('target') or ''),
            check=str(data.get('check') or ''),
            severity=str(data.get('severity') or 'info'),
            detail=str(data.get('detail') or ''),
            evidence=dict(data.get('evidence') or {}),
            endpoint=data.get('endpoint'),
            method=data.get('method'),
            confidence=data.get('confidence'),
            cwe=data.get('cwe'),
        )


@dataclass
class Summary:
    live_targets: int = 0
    candidates: int = 0
    findings_total: int = 0
    findings_high: int = 0
    findings_medium: int = 0
    findings_low: int = 0
    findings_info: int = 0
    actionable: int = 0
    passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Report:
    report_version: str
    plugin: str
    generated_at: str
    spec_id: Any
    base_url: str
    summary: Summary
    targets: List[Dict[str, Any]] = field(default_factory=list)
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    orchestrator: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_version': self.report_version,
            'plugin': self.plugin,
            'orchestrator': self.orchestrator,
            'generated_at': self.generated_at,
            'spec_id': self.spec_id,
            'base_url': self.base_url,
            'summary': self.summary.to_dict() if isinstance(self.summary, Summary) else dict(self.summary),
            'targets': self.targets,
            'candidates': self.candidates,
            'findings': self.findings,
        }
