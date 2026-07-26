# -*- coding: utf-8 -*-
# HTTP REST object-level authorization & BOLA/IDOR checks.

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import requests
from neotermcolor import colored

from core.vmnf_channels import register_channel
from core.findings import Finding as ObjFinding
from siddhis.objgate.utils import get_hash, join_url, parse_auth_header, render_obj_path


def handler_admin_path(handler: dict) -> Optional[str]:
    raw = handler.get('obj_admin_path')
    if not raw:
        return None
    return str(raw)


_CHECK_CWE = {
    'unauthenticated_object_access': 'CWE-306',
    'cross_tenant_object_idor': 'CWE-639',
    'vertical_privilege_object': 'CWE-269',
    'membership_baseline': 'CWE-284',
    'membership_own_denied': 'CWE-284',
}


class ObjBolaAuditor:
    """
    Probes REST object paths for:
    - unauthenticated object access
    - horizontal IDOR / BOLA (identity A accesses object B)
    - vertical privilege (user → admin resource)
    - membership baseline
    """

    def __init__(self, handler: dict):
        self.handler = handler
        self.timeout = float(handler.get('timeout') or 15)
        self.verbose = bool(handler.get('verbose'))
        self.auth_a = (
            handler.get('obj_auth_a')
            or handler.get('obj_auth_header')
            or 'Bearer user-a-token'
        )
        self.auth_b = handler.get('obj_auth_b') or 'Bearer user-b-token'
        self.checks_mode = (handler.get('obj_checks') or 'all').lower()
        methods = handler.get('obj_methods') or 'GET,PATCH'
        if isinstance(methods, str):
            self.methods = [m.strip().upper() for m in methods.split(',') if m.strip()]
        else:
            self.methods = ['GET']

    def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[dict] = None,
    ) -> Tuple[Optional[requests.Response], Optional[str]]:
        try:
            resp = requests.request(
                method,
                url,
                headers=headers or {},
                json=json_body,
                timeout=self.timeout,
                allow_redirects=False,
            )
            return resp, None
        except Exception as exc:
            return None, str(exc)

    def _is_success(self, resp: Optional[requests.Response]) -> bool:
        if resp is None:
            return False
        return 200 <= resp.status_code < 300

    def _body_snippet(self, resp: Optional[requests.Response], limit: int = 400) -> Any:
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception:
            text = resp.text or ''
            return text[:limit]

    def audit_template(
        self,
        template: str,
        base_url: str,
        obj_a: str,
        obj_b: str,
    ) -> List[ObjFinding]:
        findings: List[ObjFinding] = []
        path_a = render_obj_path(template, obj_a)
        path_b = render_obj_path(template, obj_b)
        url_a = join_url(base_url, path_a)
        url_b = join_url(base_url, path_b)
        headers_a = parse_auth_header(self.auth_a)
        headers_b = parse_auth_header(self.auth_b)
        mode = self.checks_mode
        primary = self.methods[0] if self.methods else 'GET'

        # 1) Unauthenticated access to object A
        if mode in ('all', 'unauth'):
            resp, err = self._request(primary, url_a, headers=None)
            if self._is_success(resp):
                findings.append(ObjFinding(
                    target=url_a,
                    check='unauthenticated_object_access',
                    severity='high',
                    detail=(
                        f'Unauthenticated {primary} succeeded on {path_a} '
                        f'(HTTP {resp.status_code}). Object should require authentication.'
                    ),
                    evidence={
                        'method': primary,
                        'status': resp.status_code,
                        'body': self._body_snippet(resp),
                    },
                ))
            elif self.verbose:
                status = resp.status_code if resp is not None else err
                print(colored(f'  [ok] unauth denied on {path_a}: {status}', 'green'))

        # 2) Horizontal BOLA: identity A accesses object B
        if mode in ('all', 'idor', 'bola', 'horizontal'):
            for method in self.methods:
                body = {'note': 'objgate-probe'} if method in ('PATCH', 'PUT', 'POST') else None
                resp, err = self._request(method, url_b, headers=headers_a, json_body=body)
                if self._is_success(resp):
                    findings.append(ObjFinding(
                        target=url_b,
                        check='cross_tenant_object_idor',
                        severity='high',
                        detail=(
                            f'Identity A ({self.auth_a!r}) {method} object {obj_b!r} '
                            f'via {path_b} (expected isolation to {obj_a!r}). '
                            'Possible BOLA/IDOR on object id.'
                        ),
                        evidence={
                            'method': method,
                            'status': resp.status_code,
                            'auth': self.auth_a,
                            'expected_obj': obj_a,
                            'accessed_obj': obj_b,
                            'body': self._body_snippet(resp),
                        },
                    ))
                elif self.verbose:
                    status = resp.status_code if resp is not None else err
                    print(colored(f'  [ok] IDOR blocked {method} {path_b}: {status}', 'green'))

        # 3) Membership baseline: A→A and B→B
        if mode in ('all', 'membership'):
            resp_a, err_a = self._request(primary, url_a, headers=headers_a)
            resp_b, err_b = self._request(primary, url_b, headers=headers_b)
            if self._is_success(resp_a) and self._is_success(resp_b):
                findings.append(ObjFinding(
                    target=url_a,
                    check='membership_baseline',
                    severity='info',
                    detail=(
                        f'Both identities accessed their respective objects '
                        f'({obj_a} / {obj_b}). Use with IDOR results for context.'
                    ),
                    evidence={
                        'obj_a_status': resp_a.status_code,
                        'obj_b_status': resp_b.status_code,
                    },
                ))
            elif not self._is_success(resp_a):
                findings.append(ObjFinding(
                    target=url_a,
                    check='membership_own_denied',
                    severity='low',
                    detail=(
                        f'Identity A could not access claimed object {obj_a!r}: '
                        f'{resp_a.status_code if resp_a else err_a}. '
                        'Auth header or object mapping may be wrong for this target.'
                    ),
                    evidence={'error': err_a, 'status': getattr(resp_a, 'status_code', None)},
                ))

        # 4) Vertical / BFLA: user A hits admin-looking object path
        if mode in ('all', 'vertical', 'bfla'):
            admin_template = handler_admin_path(self.handler) or '/api/admin/orders/{id}/'
            admin_path = render_obj_path(admin_template, obj_a)
            admin_url = join_url(base_url, admin_path)
            resp, err = self._request(primary, admin_url, headers=headers_a)
            if self._is_success(resp):
                findings.append(ObjFinding(
                    target=admin_url,
                    check='vertical_privilege_object',
                    severity='medium',
                    detail=(
                        f'Non-admin identity accessed privileged-looking path {admin_path} '
                        f'(HTTP {resp.status_code}). Check BFLA / vertical authorization.'
                    ),
                    evidence={
                        'method': primary,
                        'status': resp.status_code,
                        'auth': self.auth_a,
                        'body': self._body_snippet(resp),
                    },
                ))

        for finding in findings:
            if not finding.cwe:
                finding.cwe = _CHECK_CWE.get(finding.check, 'CWE-639')
            if not finding.endpoint and finding.evidence:
                finding.endpoint = finding.evidence.get('endpoint') or finding.target
            if not finding.method and finding.evidence:
                finding.method = finding.evidence.get('method')
        return findings
        if not findings:
            print(colored('\n[+] No object authorization findings.', 'green'))
            return
        print(colored(f'\n[*] Objgate findings: {len(findings)}', 'cyan'))
        for f in findings:
            color = {
                'high': 'red',
                'medium': 'yellow',
                'low': 'white',
                'info': 'blue',
            }.get(f.severity, 'white')
            print(colored(f'  [{f.severity.upper()}] {f.check}', color))
            print(f'      {f.detail}')
            print(f'      target: {f.target}')

    def register_channels(self, findings: List[ObjFinding], base_url: str) -> None:
        for f in findings:
            if f.severity not in ('high', 'medium'):
                continue
            channel_id = 'og' + get_hash(f.target + f.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'HttpObjectAuthz',
                'plugin': 'objgate',
                'target_url': base_url,
                'endpoint': f.target,
                'method': (f.evidence or {}).get('method', 'GET'),
                'payload_template': json.dumps({
                    'check': f.check,
                    'detail': f.detail,
                }),
                'description': f.detail,
                'status': 'active',
                'metadata': {
                    'severity': f.severity,
                    'evidence': f.evidence,
                },
            }, handler=self.handler)
