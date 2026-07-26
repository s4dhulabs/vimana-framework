# -*- coding: utf-8 -*-
# Severity helpers for Vimana findings.

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterable, Optional


class Severity(str, Enum):
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'

    @classmethod
    def normalize(cls, value: Any, default: 'Severity' = None) -> 'Severity':
        default = default or cls.INFO
        if isinstance(value, cls):
            return value
        if value is None:
            return default
        text = str(value).strip().lower()
        for item in cls:
            if item.value == text:
                return item
        return default


class ExitPolicy:
    """CI exit policy: fail when findings at/above threshold exist."""

    def __init__(self, fail_on: Severity = Severity.HIGH):
        self.fail_on = Severity.normalize(fail_on, Severity.HIGH)

    @classmethod
    def from_handler(cls, handler: Optional[dict] = None) -> 'ExitPolicy':
        handler = handler or {}
        raw = handler.get('ci_fail_on') or handler.get('fail_on_severity') or 'high'
        return cls(fail_on=Severity.normalize(raw, Severity.HIGH))

    def ranks(self) -> Iterable[Severity]:
        order = [Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
        start = order.index(self.fail_on)
        return order[: start + 1]


def resolve_exit_code(summary: Dict[str, Any], policy: Optional[ExitPolicy] = None) -> int:
    policy = policy or ExitPolicy()
    for severity in policy.ranks():
        key = f'findings_{severity.value}'
        if int(summary.get(key, 0) or 0) > 0:
            return 1
    return 0


SARIF_LEVEL = {
    Severity.HIGH: 'error',
    Severity.MEDIUM: 'warning',
    Severity.LOW: 'note',
    Severity.INFO: 'note',
}
