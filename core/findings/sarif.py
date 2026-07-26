# -*- coding: utf-8 -*-
# SARIF 2.1.0 exporter for Vimana audit reports.

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .severity import SARIF_LEVEL, Severity


_CWE_RE = re.compile(r'(CWE-?\d+)', re.IGNORECASE)


def _extract_cwes(finding: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    raw = finding.get('cwe')
    if isinstance(raw, list):
        values.extend(str(v) for v in raw)
    elif raw:
        values.append(str(raw))

    # Also scrape CWE ids from check/detail text
    blob = ' '.join(
        str(finding.get(k) or '') for k in ('check', 'detail', 'target')
    )
    values.extend(_CWE_RE.findall(blob))

    normalized = []
    seen = set()
    for value in values:
        match = _CWE_RE.search(str(value))
        if not match:
            continue
        token = match.group(1).upper()
        digits = re.sub(r'\D', '', token)
        if not digits:
            continue
        cwe = f'CWE-{digits}'
        if cwe not in seen:
            seen.add(cwe)
            normalized.append(cwe)
    return normalized


def _rule_id(finding: Dict[str, Any], plugin: str) -> str:
    check = str(finding.get('check') or 'finding').strip().replace(' ', '_')
    return f'{plugin}.{check}'


def _physical_location(finding: Dict[str, Any], base_url: str) -> Dict[str, Any]:
    endpoint = finding.get('endpoint')
    if not endpoint:
        evidence = finding.get('evidence') or {}
        endpoint = evidence.get('endpoint') or evidence.get('url') or finding.get('target')
    uri = str(endpoint or base_url or '')
    if uri and not uri.startswith(('http://', 'https://', 'ws://', 'wss://')):
        if base_url:
            uri = base_url.rstrip('/') + '/' + uri.lstrip('/')
    parsed = urlparse(uri)
    if not parsed.scheme and base_url:
        uri = base_url
    return {
        'artifactLocation': {'uri': uri or 'about:blank'},
    }


def to_sarif(report: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Vimana CI report dict into a SARIF 2.1.0 document."""
    plugin = str(report.get('plugin') or 'vimana')
    base_url = str(report.get('base_url') or '')
    findings = list(report.get('findings') or [])

    rules_by_id: Dict[str, Dict[str, Any]] = {}
    results: List[Dict[str, Any]] = []

    for finding in findings:
        severity = Severity.normalize(finding.get('severity'))
        rule_id = _rule_id(finding, plugin)
        if rule_id not in rules_by_id:
            cwes = _extract_cwes(finding)
            rule = {
                'id': rule_id,
                'name': str(finding.get('check') or rule_id),
                'shortDescription': {'text': str(finding.get('check') or rule_id)},
                'fullDescription': {'text': str(finding.get('detail') or finding.get('check') or rule_id)},
                'defaultConfiguration': {'level': SARIF_LEVEL[severity]},
                'properties': {
                    'tags': ['security', plugin, severity.value],
                    'precision': finding.get('confidence') or 'medium',
                },
            }
            if cwes:
                rule['properties']['cwe'] = cwes
                rule['relationships'] = [
                    {
                        'target': {
                            'id': cwe,
                            'toolComponent': {'name': 'CWE'},
                        },
                        'kinds': ['superset'],
                    }
                    for cwe in cwes
                ]
            rules_by_id[rule_id] = rule

        result = {
            'ruleId': rule_id,
            'level': SARIF_LEVEL[severity],
            'message': {'text': str(finding.get('detail') or finding.get('check') or '')},
            'locations': [
                {
                    'physicalLocation': _physical_location(finding, base_url),
                }
            ],
            'properties': {
                'severity': severity.value,
                'check': finding.get('check'),
                'target': finding.get('target'),
                'evidence': finding.get('evidence') or {},
            },
        }
        cwes = _extract_cwes(finding)
        if cwes:
            result['properties']['cwe'] = cwes
        results.append(result)

    return {
        'version': '2.1.0',
        '$schema': 'https://json.schemastore.org/sarif-2.1.0.json',
        'runs': [
            {
                'tool': {
                    'driver': {
                        'name': f'vimana-{plugin}',
                        'informationUri': 'https://github.com/s4dhulabs/vimana-framework',
                        'rules': list(rules_by_id.values()),
                    }
                },
                'results': results,
                'properties': {
                    'plugin': plugin,
                    'spec_id': report.get('spec_id'),
                    'base_url': base_url,
                    'summary': report.get('summary') or {},
                    'orchestrator': report.get('orchestrator'),
                    'generated_at': report.get('generated_at'),
                },
            }
        ],
    }


def emit_sarif(report: Dict[str, Any], handler: Optional[dict] = None) -> str:
    """Write SARIF to handler['sarif_output'] or handler['sarif'] path; return payload."""
    handler = handler or {}
    document = to_sarif(report)
    payload = json.dumps(document, indent=2, default=str)
    path = handler.get('sarif_output') or handler.get('sarif')
    if path and path is not True:
        with open(str(path), 'w') as handle:
            handle.write(payload)
            handle.write('\n')
        if not handler.get('quiet_output') and not handler.get('json_output') and not handler.get('ci_mode'):
            print(f'[+] SARIF report saved to {path}')
    return payload
