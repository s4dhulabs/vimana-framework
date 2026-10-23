# -*- coding: utf-8 -*-
"""Deterministic agent scripts for CI / dogfood e2e (provider=scripted)."""

from __future__ import annotations

from typing import Any, Dict, List

# Boundr: start lab → sync audit → findings → stop
# Requires Docker. Uses $last.* resolved by ScriptedClient from prior tool results.
BOUNDR_E2E: List[Dict[str, Any]] = [
    {'tool': 'vimana_health', 'arguments': {}},
    {'tool': 'vimana_lab_start', 'arguments': {'plugin': 'boundr'}},
    {
        'tool': 'vimana_run_plugin',
        'arguments': {
            'name': 'boundr',
            'async': False,
            'args': {
                'target_url': '$last.url',
                'upload_audit_enabled': True,
                'json_output': True,
                'no_channels': True,
            },
        },
    },
    {
        'tool': 'vimana_get_findings',
        'arguments': {'run_id': '$last.run_id'},
    },
    {'tool': 'vimana_lab_stop', 'arguments': {'plugin': 'boundr'}},
    {
        'content': (
            'E2E boundr complete: lab started, upload audit ran, '
            'findings fetched, lab stopped.'
        ),
    },
]

SCRIPTED_SCENARIOS: Dict[str, List[Dict[str, Any]]] = {
    'boundr': BOUNDR_E2E,
    'deny': [
        {'tool': 'vimana_health', 'arguments': {}},
        {'tool': 'vimana_lab_cleanup', 'arguments': {}},
        {
            'content': (
                'Security smoke: cleanup should have been denied under safe policy.'
            ),
        },
    ],
    # EXECUTE against a remote host must fail under default loopback allowlist
    'remote-deny': [
        {
            'tool': 'vimana_run_plugin',
            'arguments': {
                'name': 'boundr',
                'async': False,
                'args': {
                    'target_url': 'https://example.com',
                    'upload_audit_enabled': True,
                    'json_output': True,
                    'no_channels': True,
                },
            },
        },
        {
            'content': (
                'Security smoke: remote target should have been denied '
                '(loopback allowlist).'
            ),
        },
    ],
}


def get_scenario(name: str) -> List[Dict[str, Any]]:
    key = (name or '').strip().lower()
    if key not in SCRIPTED_SCENARIOS:
        known = ', '.join(sorted(SCRIPTED_SCENARIOS))
        raise ValueError(f'unknown scripted scenario {name!r}; expected one of: {known}')
    # shallow-copy steps so ScriptedClient mutation of index is fine
    return [dict(step) for step in SCRIPTED_SCENARIOS[key]]
