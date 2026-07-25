# -*- coding: utf-8 -*-
# SSRF probe engine for fetchbane.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests
from neotermcolor import colored

from core.vmnf_channels import register_channel
from siddhis.fetchbane.engines.discovery import (
    build_vectors,
    resolve_canary,
    resolve_endpoints,
    resolve_param,
)
from siddhis.fetchbane.utils import CANARY_MARKER, get_hash, join_url


@dataclass
class SsrfFinding:
    target: str
    check: str
    severity: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


class SsrfAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.timeout = float(handler.get('timeout') or 12)
        self.verbose = bool(handler.get('verbose'))
        self.param = resolve_param(handler)
        self.vectors_mode = handler.get('ssrf_vectors') or 'all'

    def _probe(
        self,
        method: str,
        url: str,
        payload_url: str,
    ) -> Tuple[Optional[requests.Response], Optional[str]]:
        try:
            if method == 'GET':
                full = f'{url}?{urlencode({self.param: payload_url})}'
                resp = requests.get(full, timeout=self.timeout, allow_redirects=False)
            else:
                resp = requests.post(
                    url,
                    json={self.param: payload_url},
                    timeout=self.timeout,
                    allow_redirects=False,
                )
            return resp, None
        except Exception as exc:
            return None, str(exc)

    def _body_text(self, resp: Optional[requests.Response], limit: int = 800) -> str:
        if resp is None:
            return ''
        return (resp.text or '')[:limit]

    def audit_endpoint(self, endpoint: str, base_url: str) -> List[SsrfFinding]:
        findings: List[SsrfFinding] = []
        target = join_url(base_url, endpoint)
        canary = resolve_canary(self.handler, base_url)
        vectors = build_vectors(canary, self.vectors_mode)

        for tag, payload, severity in vectors:
            # Prefer GET for query-style, also try POST for webhook-like paths
            methods = ['GET']
            if 'webhook' in endpoint or 'fetch' in endpoint:
                methods.append('POST')

            for method in methods:
                resp, err = self._probe(method, target, payload)
                body = self._body_text(resp)
                status = resp.status_code if resp is not None else None

                hit = False
                check = f'ssrf_{tag}'
                detail = ''

                if CANARY_MARKER in body:
                    hit = True
                    check = 'ssrf_canary_reflection'
                    detail = (
                        f'{method} {endpoint} fetched attacker-controlled URL and reflected '
                        f'canary marker in response (payload={payload!r}). Confirmed SSRF.'
                    )
                    severity = 'high'
                elif tag.startswith('aws_') or tag.startswith('gcp_'):
                    # Treat 200 with metadata-like body OR lab echoing fetched content length
                    if resp is not None and status and 200 <= status < 400:
                        if any(k in body.lower() for k in ('ami-id', 'instance-id', 'meta-data', 'computeMetadata'.lower())):
                            hit = True
                            check = 'ssrf_cloud_metadata'
                            detail = (
                                f'{method} {endpoint} appears to have reached cloud metadata '
                                f'via {payload!r} (HTTP {status}).'
                            )
                        elif 'fetched' in body.lower() and status == 200 and len(body) > 40:
                            # lab may proxy body; treat as medium if non-empty fetch of metadata URL
                            hit = True
                            check = 'ssrf_metadata_fetch_attempt'
                            severity = 'medium'
                            detail = (
                                f'{method} {endpoint} accepted metadata URL {payload!r} '
                                f'and returned HTTP {status} with body content.'
                            )
                elif tag.startswith('file_') and resp is not None and status and 200 <= status < 400:
                    if 'root:' in body or '/bin/' in body or 'passwd' in body.lower():
                        hit = True
                        check = 'ssrf_file_scheme'
                        detail = f'{method} {endpoint} appears to have read local file via {payload!r}.'

                if hit:
                    findings.append(SsrfFinding(
                        target=f'{target} ({method})',
                        check=check,
                        severity=severity,
                        detail=detail,
                        evidence={
                            'method': method,
                            'endpoint': endpoint,
                            'param': self.param,
                            'payload': payload,
                            'status': status,
                            'body_snippet': body[:400],
                            'vector': tag,
                        },
                    ))
                    break  # one hit per vector tag is enough
                elif self.verbose and err:
                    print(colored(f'  [skip] {tag} {method}: {err}', 'white'))

        # Deduplicate by check+endpoint
        uniq = []
        seen = set()
        for f in findings:
            key = (f.check, f.evidence.get('endpoint'), f.evidence.get('payload'))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(f)
        return uniq

    def print_findings(self, findings: List[SsrfFinding]) -> None:
        if not findings:
            print(colored('\n[+] No SSRF findings.', 'green'))
            return
        print(colored(f'\n[*] Fetchbane findings: {len(findings)}', 'cyan'))
        for f in findings:
            color = {'high': 'red', 'medium': 'yellow', 'low': 'white', 'info': 'blue'}.get(f.severity, 'white')
            print(colored(f'  [{f.severity.upper()}] {f.check}', color))
            print(f'      {f.detail}')
            print(f'      target: {f.target}')

    def register_channels(self, findings: List[SsrfFinding], base_url: str) -> None:
        for f in findings:
            if f.severity not in ('high', 'medium'):
                continue
            channel_id = 'fb' + get_hash(f.target + f.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'SSRF',
                'plugin': 'fetchbane',
                'target_url': base_url,
                'endpoint': f.target,
                'method': (f.evidence or {}).get('method', 'GET'),
                'payload_template': json.dumps({
                    'check': f.check,
                    'payload': (f.evidence or {}).get('payload'),
                }),
                'description': f.detail,
                'status': 'active',
                'metadata': {'severity': f.severity, 'evidence': f.evidence},
            })
