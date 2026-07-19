# -*- coding: utf-8 -*-
# Multipart upload probing and response analysis for boundr.

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from neotermcolor import colored

from core.vmnf_channels import register_channel
from siddhis.boundr.engines.filename_vectors import baseline_vector, select_vectors
from siddhis.boundr.utils import get_hash


@dataclass
class UploadFinding:
    target: str
    check: str
    severity: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


TRAVERSAL_HINTS = re.compile(
    r'(/etc/passwd|/tmp/boundr|win\.ini|traversal|saved.?as|wrote.?to|path[:\s])',
    re.I,
)
PATH_REFLECT_RE = re.compile(
    r'(/[^\s"\']+\.(?:txt|bin|php|html|svg|jpg|png)|uploads?/[^\s"\']+|tmp/[^\s"\']+)',
    re.I,
)


class UploadEndpointAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.vectors_mode = handler.get('upload_vectors') or 'all'
        self.auth_header = handler.get('upload_auth_header')
        self.verbose = bool(handler.get('verbose'))
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def _auth_headers(self) -> Dict[str, str]:
        raw = self.auth_header
        if not raw:
            return {}
        if ':' in raw:
            key, value = raw.split(':', 1)
            return {key.strip(): value.strip()}
        return {'Authorization': raw}

    async def _upload(
        self,
        url: str,
        method: str,
        field: str,
        filename: str,
        content_type: str,
        body: bytes,
        extra_fields: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        result = {
            'status': None,
            'body': '',
            'headers': {},
            'error': None,
            'filename': filename,
            'content_type': content_type,
            'size': len(body),
        }
        headers = self._auth_headers()
        files = {field: (filename, body, content_type)}
        data = extra_fields or {}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.request(
                    method.upper(),
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                )
                result['status'] = response.status_code
                result['body'] = response.text[:4000]
                result['headers'] = dict(response.headers)
        except Exception as exc:
            result['error'] = str(exc)

        return result

    async def _probe_live(self, target: Dict[str, str]) -> bool:
        filename, ctype, body, _ = baseline_vector()
        probe = await self._upload(
            target['url'],
            target.get('method', 'POST'),
            target.get('field', 'file'),
            filename,
            ctype,
            body,
        )
        if probe.get('error'):
            return False
        status = probe.get('status')
        # 2xx/4xx (validation) means endpoint exists; 404/405 = miss
        return status is not None and status not in (404, 405, 501)

    def _analyze_response(
        self,
        target: Dict[str, str],
        vector_tag: str,
        filename: str,
        response: Dict[str, Any],
    ) -> List[UploadFinding]:
        findings: List[UploadFinding] = []
        url = target['url']
        status = response.get('status')
        body = response.get('body') or ''
        error = response.get('error')

        if error:
            return findings

        if vector_tag == 'baseline':
            if status and 200 <= status < 300:
                findings.append(UploadFinding(
                    target=url,
                    check='upload_accepted',
                    severity='info',
                    detail='Baseline upload accepted',
                    evidence={'status': status, 'preview': body[:200]},
                ))
            return findings

        # Path traversal accepted
        if vector_tag.startswith('path_traversal') or vector_tag in ('absolute_path', 'nested_traversal'):
            if status and 200 <= status < 300:
                severity = 'high'
                detail = f'Traversal filename accepted: {filename!r}'
                if TRAVERSAL_HINTS.search(body) or PATH_REFLECT_RE.search(body):
                    detail += ' — response reflects filesystem path'
                    severity = 'high'
                findings.append(UploadFinding(
                    target=url,
                    check='path_traversal',
                    severity=severity,
                    detail=detail,
                    evidence={'filename': filename, 'status': status, 'preview': body[:300]},
                ))
            return findings

        # MIME spoof / polyglot
        if vector_tag.startswith('mime_spoof') or vector_tag in ('polyglot', 'svg_xxe'):
            if status and 200 <= status < 300:
                findings.append(UploadFinding(
                    target=url,
                    check='mime_validation_weak',
                    severity='medium' if vector_tag != 'svg_xxe' else 'high',
                    detail=f'Upload with mismatched MIME/extension accepted ({vector_tag})',
                    evidence={
                        'filename': filename,
                        'declared_type': response.get('content_type'),
                        'status': status,
                        'preview': body[:300],
                    },
                ))
                if vector_tag == 'svg_xxe' and ('root:' in body or 'passwd' in body.lower()):
                    findings.append(UploadFinding(
                        target=url,
                        check='svg_xxe_leak',
                        severity='high',
                        detail='SVG XXE payload appears to have leaked file contents',
                        evidence={'preview': body[:400]},
                    ))
            return findings

        # Size / policy
        if vector_tag == 'oversized_2mb':
            if status and 200 <= status < 300:
                findings.append(UploadFinding(
                    target=url,
                    check='size_limit_missing',
                    severity='medium',
                    detail='2MB oversized upload accepted without rejection',
                    evidence={'status': status, 'size': response.get('size')},
                ))
            return findings

        if vector_tag == 'empty_file':
            if status and 200 <= status < 300:
                findings.append(UploadFinding(
                    target=url,
                    check='empty_file_accepted',
                    severity='low',
                    detail='Empty file upload accepted',
                    evidence={'status': status},
                ))
            return findings

        if vector_tag == 'oversized_filename':
            if status and 200 <= status < 300:
                findings.append(UploadFinding(
                    target=url,
                    check='oversized_filename_accepted',
                    severity='low',
                    detail='Extremely long filename accepted',
                    evidence={'filename_len': len(filename), 'status': status},
                ))
            return findings

        # Reserved / null byte
        if vector_tag.startswith('reserved') or vector_tag.startswith('null_byte'):
            if status and 200 <= status < 300:
                findings.append(UploadFinding(
                    target=url,
                    check='dangerous_filename_accepted',
                    severity='medium',
                    detail=f'Dangerous filename accepted: {filename!r} ({vector_tag})',
                    evidence={'filename': filename, 'status': status, 'preview': body[:200]},
                ))
            return findings

        # Generic path reflection on any successful upload
        if status and 200 <= status < 300 and PATH_REFLECT_RE.search(body):
            findings.append(UploadFinding(
                target=url,
                check='path_reflected',
                severity='medium',
                detail='Upload response reflects stored filesystem path',
                evidence={'filename': filename, 'preview': body[:300]},
            ))

        return findings

    async def audit_endpoint(self, target: Dict[str, str]) -> List[UploadFinding]:
        url = target['url']
        method = target.get('method', 'POST')
        field = target.get('field') or self.handler.get('upload_field') or 'file'
        findings: List[UploadFinding] = []

        vectors = select_vectors(self.vectors_mode)
        for filename, content_type, body, vector_tag in vectors:
            response = await self._upload(url, method, field, filename, content_type, body)
            findings.extend(self._analyze_response(target, vector_tag, filename, response))

            if self.verbose and response.get('status'):
                print(colored(
                    f'  [{vector_tag}] {filename} → HTTP {response["status"]}',
                    'cyan',
                ))

        # Unauthenticated check if auth header provided
        if self.auth_header:
            filename, ctype, body, _ = baseline_vector()
            # Temporarily clear auth
            saved = self.auth_header
            self.auth_header = None
            unauth = await self._upload(url, method, field, filename, ctype, body)
            self.auth_header = saved
            if unauth.get('status') and 200 <= unauth['status'] < 300:
                findings.append(UploadFinding(
                    target=url,
                    check='unauthenticated_upload',
                    severity='high',
                    detail='Upload endpoint accepts files without credentials',
                    evidence={'status': unauth['status']},
                ))

        if not findings:
            findings.append(UploadFinding(
                target=url,
                check='no_issues_detected',
                severity='info',
                detail='No actionable upload findings for selected vectors',
            ))

        return findings

    def register_channels(self, findings: List[UploadFinding], base_url: str) -> None:
        for finding in findings:
            if finding.severity not in ('high', 'medium'):
                continue
            channel_id = 'bd' + get_hash(finding.target + finding.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'Upload',
                'plugin': 'boundr',
                'target_url': base_url,
                'endpoint': finding.target,
                'method': 'POST',
                'payload_template': json.dumps({
                    'check': finding.check,
                    'detail': finding.detail,
                }),
                'description': finding.detail,
                'status': 'active',
                'metadata': {
                    'severity': finding.severity,
                    'evidence': finding.evidence,
                },
            })

    def print_findings(self, findings: List[UploadFinding]) -> None:
        if not findings:
            print(colored('[*] No upload endpoints produced findings.', 'yellow'))
            return

        severity_colors = {
            'high': 'red',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'white',
        }
        print(colored('\n[+] Upload audit results\n', 'green'))
        for item in findings:
            color = severity_colors.get(item.severity, 'white')
            print(
                f"  [{colored(item.severity.upper(), color)}] "
                f"{item.target} — {item.check}: {item.detail}"
            )
        print()
