# -*- coding: utf-8 -*-
"""
Agent tool security policy (fail-closed).

Vimana is a security framework — the native agent must demonstrate
least privilege for LLM tool use (OWASP LLM Top 10 / agent over-reach).

Enforcement is dual:
  1) only allowed tools are advertised to the model
  2) every tool call is re-checked before dispatch (defense in depth)

Profiles (ascending privilege):
  safe  — read/orient only (DEFAULT)
  lab   — safe + start/stop individual labs
  run   — lab + run_plugin / run_case
  full  — all Control tools (incl. lab_cleanup); explicit opt-in only

EXECUTE also gated by:
  - target host allowlist (loopback by default; --allow-target / --allow-any-target)
  - optional human confirmation (--confirm) before dispatch
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import urlparse


class ToolRisk(str, Enum):
    READ = 'read'
    LAB = 'lab'              # start/stop one lab
    LAB_GLOBAL = 'lab_global'  # cleanup all
    EXECUTE = 'execute'      # run plugin / case


# Canonical risk map — unknown tools are DENIED (fail closed).
TOOL_RISK: Dict[str, ToolRisk] = {
    'vimana_health': ToolRisk.READ,
    'vimana_about': ToolRisk.READ,
    'vimana_list_plugins': ToolRisk.READ,
    'vimana_get_plugin': ToolRisk.READ,
    'vimana_explain_plugin': ToolRisk.READ,
    'vimana_analyze_target': ToolRisk.EXECUTE,
    'vimana_list_runs': ToolRisk.READ,
    'vimana_get_run': ToolRisk.READ,
    'vimana_get_findings': ToolRisk.READ,
    'vimana_list_labs': ToolRisk.READ,
    'vimana_lab_status': ToolRisk.READ,
    'vimana_list_specs': ToolRisk.READ,
    'vimana_get_spec': ToolRisk.READ,
    'vimana_list_channels': ToolRisk.READ,
    'vimana_list_cases': ToolRisk.READ,
    'vimana_lab_start': ToolRisk.LAB,
    'vimana_lab_stop': ToolRisk.LAB,
    'vimana_lab_cleanup': ToolRisk.LAB_GLOBAL,
    'vimana_lab_test': ToolRisk.EXECUTE,
    'vimana_run': ToolRisk.EXECUTE,
    'vimana_run_plugin': ToolRisk.EXECUTE,
    'vimana_run_case': ToolRisk.EXECUTE,
}

# What each profile may invoke
_PROFILE_RISKS: Dict[str, Set[ToolRisk]] = {
    'safe': {ToolRisk.READ},
    'lab': {ToolRisk.READ, ToolRisk.LAB},
    'run': {ToolRisk.READ, ToolRisk.LAB, ToolRisk.EXECUTE},
    'full': {ToolRisk.READ, ToolRisk.LAB, ToolRisk.LAB_GLOBAL, ToolRisk.EXECUTE},
}

DEFAULT_POLICY = 'safe'
VALID_POLICIES = tuple(_PROFILE_RISKS.keys())

# Default EXECUTE targets when allowlist not widened
LOOPBACK_HOSTS: Set[str] = {
    'localhost',
    '127.0.0.1',
    '::1',
    '[::1]',
    '0.0.0.0',
}

_TARGET_ARG_KEYS = (
    'target_url',
    'target',
    'endpoint_url',
    'url',
    'base_url',
    'host',
)

# Short notes for --show-policy / learning (agent & LLM security)
THREAT_NOTES = [
    {
        'id': 'LLM01',
        'title': 'Prompt injection → tool over-reach',
        'mitigation': 'Advertise only allowed tools; re-check every call; default policy=safe',
    },
    {
        'id': 'LLM06',
        'title': 'Excessive agency',
        'mitigation': 'Profiles escalate privilege intentionally (safe→lab→run→full)',
    },
    {
        'id': 'LLM08',
        'title': 'Unbounded consumption / noisy side effects',
        'mitigation': 'max_turns cap; lab_cleanup never in safe/lab/run',
    },
    {
        'id': 'AGENT-TARGET',
        'title': 'Unrestricted network targets from EXECUTE',
        'mitigation': (
            'Loopback-only host allowlist by default; '
            '--allow-target / --allow-any-target to widen'
        ),
    },
    {
        'id': 'AGENT-CONFIRM',
        'title': 'Silent EXECUTE without human gate',
        'mitigation': '--confirm prompts before EXECUTE (run / lab_test / run_plugin / run_case); --yes skips (CI)',
    },
    {
        'id': 'AGENT-AUDIT',
        'title': 'Accountability',
        'mitigation': 'Transcript records denied calls + policy profile',
    },
]


@dataclass
class PolicyDecision:
    allowed: bool
    tool: str
    risk: Optional[str]
    reason: str
    policy: str


def _normalize_host(value: str) -> str:
    raw = (value or '').strip().lower()
    if not raw:
        return ''
    if '://' in raw:
        parsed = urlparse(raw)
        host = (parsed.hostname or '').lower()
        return host
    # bare host or host:port
    if raw.startswith('[') and ']' in raw:
        return raw[1:raw.index(']')].lower()
    if '/' in raw:
        raw = raw.split('/', 1)[0]
    if ':' in raw and raw.count(':') == 1:
        raw = raw.split(':', 1)[0]
    return raw.rstrip('.')


def extract_target_hosts(arguments: Optional[Dict[str, Any]]) -> List[str]:
    """Pull hostnames from EXECUTE tool arguments (top-level + nested args)."""
    args = dict(arguments or {})
    nested = args.get('args') if isinstance(args.get('args'), dict) else {}
    blobs: List[Any] = []
    for key in _TARGET_ARG_KEYS:
        if key in args and args[key] not in (None, False, ''):
            blobs.append(args[key])
        if key in nested and nested[key] not in (None, False, ''):
            blobs.append(nested[key])
    hosts: List[str] = []
    for blob in blobs:
        host = _normalize_host(str(blob))
        if host:
            hosts.append(host)
    return hosts


@dataclass
class AgentPolicy:
    """Fail-closed tool gate for the native agent."""

    name: str = DEFAULT_POLICY
    extra_allow: Set[str] = field(default_factory=set)
    extra_deny: Set[str] = field(default_factory=set)
    # Host allowlist for EXECUTE. Empty + allow_any_target=False → loopback default.
    target_hosts: Set[str] = field(default_factory=set)
    allow_any_target: bool = False
    # When True, loop requires a confirm callback for EXECUTE tools.
    require_confirm: bool = False

    def __post_init__(self) -> None:
        name = (self.name or DEFAULT_POLICY).strip().lower()
        if name not in _PROFILE_RISKS:
            raise ValueError(
                f'unknown agent policy {self.name!r}; '
                f'expected one of {", ".join(VALID_POLICIES)}'
            )
        self.name = name
        self.extra_allow = {t.strip() for t in self.extra_allow if t and str(t).strip()}
        self.extra_deny = {t.strip() for t in self.extra_deny if t and str(t).strip()}
        normalized: Set[str] = set()
        for h in self.target_hosts:
            nh = _normalize_host(str(h))
            if nh:
                normalized.add(nh)
        self.target_hosts = normalized

    @classmethod
    def from_parts(
        cls,
        name: Optional[str] = None,
        allow: Optional[Iterable[str]] = None,
        deny: Optional[Iterable[str]] = None,
        targets: Optional[Iterable[str]] = None,
        allow_any_target: bool = False,
        require_confirm: bool = False,
    ) -> 'AgentPolicy':
        return cls(
            name=(name or DEFAULT_POLICY),
            extra_allow=set(allow or []),
            extra_deny=set(deny or []),
            target_hosts=set(targets or []),
            allow_any_target=bool(allow_any_target),
            require_confirm=bool(require_confirm),
        )

    def effective_target_hosts(self) -> Set[str]:
        if self.allow_any_target:
            return set()
        # --allow-target widens the default loopback set (does not replace it)
        if self.target_hosts:
            return set(LOOPBACK_HOSTS) | set(self.target_hosts)
        return set(LOOPBACK_HOSTS)

    def risk_for(self, tool: str) -> Optional[ToolRisk]:
        return TOOL_RISK.get(tool)

    def check(self, tool: str) -> PolicyDecision:
        tool = (tool or '').strip()
        if not tool:
            return PolicyDecision(False, tool, None, 'empty tool name', self.name)

        if tool in self.extra_deny:
            return PolicyDecision(
                False, tool,
                (self.risk_for(tool) or ToolRisk.EXECUTE).value,
                'explicitly denied (--deny-tool / policy deny list)',
                self.name,
            )

        risk = self.risk_for(tool)
        if risk is None:
            return PolicyDecision(
                False, tool, None,
                'unknown tool (fail-closed; not in TOOL_RISK map)',
                self.name,
            )

        if tool in self.extra_allow:
            return PolicyDecision(
                True, tool, risk.value,
                'explicitly allowed (--allow-tool)',
                self.name,
            )

        if risk in _PROFILE_RISKS[self.name]:
            return PolicyDecision(
                True, tool, risk.value,
                f'allowed by policy={self.name}',
                self.name,
            )

        return PolicyDecision(
            False, tool, risk.value,
            f'risk={risk.value} not permitted under policy={self.name}',
            self.name,
        )

    def check_args(self, tool: str, arguments: Optional[Dict[str, Any]] = None) -> PolicyDecision:
        """Second gate: EXECUTE target hosts must match allowlist."""
        base = self.check(tool)
        if not base.allowed:
            return base

        risk = self.risk_for(tool)
        if risk != ToolRisk.EXECUTE:
            return base

        if self.allow_any_target:
            return PolicyDecision(
                True, tool, ToolRisk.EXECUTE.value,
                'target check skipped (--allow-any-target)',
                self.name,
            )

        hosts = extract_target_hosts(arguments)
        allowed = self.effective_target_hosts()

        # No target in args — host allowlist not applicable (e.g. case-only runs).
        if not hosts:
            return PolicyDecision(
                True, tool, ToolRisk.EXECUTE.value,
                'no network target in args; host allowlist not applied',
                self.name,
            )

        bad = [h for h in hosts if h not in allowed]
        if bad:
            return PolicyDecision(
                False, tool, ToolRisk.EXECUTE.value,
                (
                    f'target host(s) not allowed: {", ".join(bad)} '
                    f'(allowed={sorted(allowed)}; use --allow-target / --allow-any-target)'
                ),
                self.name,
            )

        return PolicyDecision(
            True, tool, ToolRisk.EXECUTE.value,
            f'target host(s) allowed: {", ".join(hosts)}',
            self.name,
        )

    def is_allowed(self, tool: str) -> bool:
        return self.check(tool).allowed

    def allowed_tool_names(self) -> List[str]:
        names = [n for n in TOOL_RISK if self.is_allowed(n)]
        for n in sorted(self.extra_allow):
            if n not in names and n not in self.extra_deny and n in TOOL_RISK:
                if self.is_allowed(n):
                    names.append(n)
        return sorted(set(names))

    def filter_descriptors(self, descriptors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        allowed = set(self.allowed_tool_names())
        return [d for d in descriptors if d.get('name') in allowed]

    def describe(self) -> Dict[str, Any]:
        by_risk: Dict[str, List[str]] = {}
        for name, risk in sorted(TOOL_RISK.items()):
            by_risk.setdefault(risk.value, []).append(name)
        decisions = {n: self.check(n).__dict__ for n in sorted(TOOL_RISK)}
        return {
            'policy': self.name,
            'default': DEFAULT_POLICY,
            'profiles': {k: sorted(r.value for r in v) for k, v in _PROFILE_RISKS.items()},
            'extra_allow': sorted(self.extra_allow),
            'extra_deny': sorted(self.extra_deny),
            'target_hosts': sorted(self.target_hosts),
            'effective_target_hosts': sorted(self.effective_target_hosts()),
            'allow_any_target': self.allow_any_target,
            'require_confirm': self.require_confirm,
            'loopback_default': sorted(LOOPBACK_HOSTS),
            'tools_by_risk': by_risk,
            'allowed_tools': self.allowed_tool_names(),
            'decisions': decisions,
            'threat_notes': THREAT_NOTES,
            'principles': [
                'fail-closed on unknown tools',
                'deny list always wins over allow / profile',
                'advertise ⊆ enforce (model never sees denied tools)',
                'full privilege requires explicit --policy full',
                'EXECUTE targets default to loopback unless --allow-target / --allow-any-target',
                'optional --confirm before EXECUTE; --yes for non-interactive CI',
            ],
        }
