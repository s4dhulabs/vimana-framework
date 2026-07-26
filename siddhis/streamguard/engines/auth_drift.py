# -*- coding: utf-8 -*-
# Streaming endpoint security checks (auth drift, cursor tampering, CRLF, exhaustion).

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from neotermcolor import colored

from core.vmnf_channels import register_channel
from siddhis.streamguard.engines.discovery import build_crlf_probe_url
from siddhis.streamguard.engines.sse_parser import (
    count_ndjson_lines,
    looks_like_stream,
    parse_sse_events,
)
from siddhis.streamguard.utils import get_hash


@dataclass
class StreamFinding:
    target: str
    check: str
    severity: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


class StreamEndpointAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.duration = int(handler.get('stream_duration') or 10)
        self.auth_header = handler.get('stream_auth_header')
        self.custom_cursor = handler.get('stream_cursor')
        self.verbose = bool(handler.get('verbose'))

    def _parse_header(self, raw: Optional[str]) -> Dict[str, str]:
        if not raw:
            return {}
        if ':' in raw:
            key, value = raw.split(':', 1)
            return {key.strip(): value.strip()}
        return {'Authorization': raw}

    def _auth_headers(self) -> Dict[str, str]:
        return self._parse_header(self.auth_header)

    async def _read_stream(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        duration = duration if duration is not None else self.duration
        headers = dict(headers or {})
        headers.setdefault('Accept', 'text/event-stream, application/x-ndjson, */*')

        result = {
            'status': None,
            'content_type': '',
            'body': '',
            'streaming': False,
            'error': None,
        }

        timeout = httpx.Timeout(30.0, connect=10.0, read=float(duration + 5))
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                async with client.stream('GET', url, headers=headers) as response:
                    result['status'] = response.status_code
                    result['content_type'] = response.headers.get('content-type', '')
                    cache_control = response.headers.get('cache-control', '')
                    result['cache_control'] = cache_control

                    if response.status_code >= 400:
                        result['error'] = f'HTTP {response.status_code}'
                        return result

                    chunks: List[bytes] = []
                    started = asyncio.get_running_loop().time()
                    async for chunk in response.aiter_bytes():
                        chunks.append(chunk)
                        if asyncio.get_running_loop().time() - started >= duration:
                            break

                    body = b''.join(chunks).decode('utf-8', errors='replace')[:8000]
                    result['body'] = body
                    result['streaming'] = looks_like_stream(result['content_type'], body)
                    result['event_count'] = len(parse_sse_events(body)) or count_ndjson_lines(body)
        except Exception as exc:
            result['error'] = str(exc)

        return result

    async def _probe_live(self, url: str) -> bool:
        probe = await self._read_stream(url, headers={}, duration=min(3, self.duration))
        return bool(
            probe.get('streaming')
            or (probe.get('status') == 200 and probe.get('body'))
        )

    async def audit_endpoint(self, target: Dict[str, str]) -> List[StreamFinding]:
        url = target['url']
        path = target.get('path', url)
        base_url = url.rsplit(path, 1)[0] if path in url else url
        findings: List[StreamFinding] = []

        unauth = await self._read_stream(url, headers={})
        auth_headers = self._auth_headers()

        if unauth.get('streaming') or (
            unauth.get('status') == 200 and unauth.get('event_count', 0) > 0
        ):
            findings.append(StreamFinding(
                target=url,
                check='unauthenticated_stream',
                severity='high',
                detail='Streaming endpoint returned live data without credentials',
                evidence={
                    'content_type': unauth.get('content_type'),
                    'preview': unauth.get('body', '')[:300],
                    'events': unauth.get('event_count', 0),
                },
            ))

        if auth_headers:
            authed = await self._read_stream(url, headers=auth_headers)
            if authed.get('streaming') and not unauth.get('streaming'):
                findings.append(StreamFinding(
                    target=url,
                    check='auth_required',
                    severity='info',
                    detail='Stream requires authentication',
                ))
            elif authed.get('streaming') and unauth.get('streaming'):
                findings.append(StreamFinding(
                    target=url,
                    check='auth_drift',
                    severity='medium',
                    detail='Authenticated and unauthenticated clients both receive stream data',
                    evidence={
                        'unauth_preview': unauth.get('body', '')[:200],
                        'authed_preview': authed.get('body', '')[:200],
                    },
                ))

        cursor_values = []
        if self.custom_cursor:
            cursor_values.append(self.custom_cursor)
        cursor_values.extend(['user-b-leak', '99999', 'admin-cursor'])

        for cursor in cursor_values:
            cursor_headers = dict(auth_headers)
            cursor_headers['Last-Event-ID'] = cursor
            cursor_probe = await self._read_stream(url, headers=cursor_headers, duration=5)
            body = cursor_probe.get('body', '')
            if cursor_probe.get('streaming') and any(
                token in body.lower()
                for token in ('secret', 'private', 'leak', 'user-b', 'tenant')
            ):
                findings.append(StreamFinding(
                    target=url,
                    check='cursor_tenant_leak',
                    severity='high',
                    detail=f'Last-Event-ID tampering ({cursor}) exposed foreign stream data',
                    evidence={'cursor': cursor, 'preview': body[:300]},
                ))
                break

        crlf_paths = [path]
        if not path.endswith('/search'):
            crlf_paths.append(path.rstrip('/') + '/search')

        for crlf_path in crlf_paths:
            crlf_url = build_crlf_probe_url(base_url, crlf_path)
            crlf_probe = await self._read_stream(crlf_url, headers=auth_headers, duration=5)
            crlf_body = crlf_probe.get('body', '')
            injected_events = parse_sse_events(crlf_body)
            if any('injected' in str(ev).lower() for ev in injected_events):
                findings.append(StreamFinding(
                    target=crlf_url,
                    check='crlf_injection',
                    severity='medium',
                    detail='CRLF sequence in query parameter reflected as SSE event fields',
                    evidence={'events': injected_events[:3]},
                ))
                break

        if unauth.get('streaming'):
            ct = (unauth.get('content_type') or '').lower()
            cache = (unauth.get('cache_control') or '').lower()
            if 'text/event-stream' in ct and 'no-cache' not in cache:
                findings.append(StreamFinding(
                    target=url,
                    check='sse_cache_misconfig',
                    severity='low',
                    detail='SSE response missing Cache-Control: no-cache',
                    evidence={'cache_control': unauth.get('cache_control')},
                ))

        parallel_ok = await self._parallel_probe(url, auth_headers, count=5)
        if parallel_ok >= 4:
            findings.append(StreamFinding(
                target=url,
                check='parallel_streams_allowed',
                severity='low',
                detail=f'{parallel_ok} concurrent stream connections accepted',
                evidence={'connections': parallel_ok},
            ))

        if not findings and unauth.get('error') and not unauth.get('streaming'):
            findings.append(StreamFinding(
                target=url,
                check='stream_unreachable',
                severity='info',
                detail=f'No live stream detected: {unauth.get("error")}',
            ))

        return findings

    async def _parallel_probe(
        self,
        url: str,
        headers: Dict[str, str],
        count: int = 5,
    ) -> int:
        tasks = [self._read_stream(url, headers=headers, duration=2) for _ in range(count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        live = 0
        for item in results:
            if isinstance(item, dict) and item.get('streaming'):
                live += 1
        return live

    def register_channels(self, findings: List[StreamFinding], base_url: str) -> None:
        for finding in findings:
            if finding.severity not in ('high', 'medium'):
                continue
            channel_id = 'sg' + get_hash(finding.target + finding.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'Stream',
                'plugin': 'streamguard',
                'target_url': base_url,
                'endpoint': finding.target,
                'method': 'GET',
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
            }, handler=self.handler)

    def print_findings(self, findings: List[StreamFinding]) -> None:
        if not findings:
            print(colored('[*] No streaming endpoints produced findings.', 'yellow'))
            return

        severity_colors = {
            'high': 'red',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'white',
        }
        print(colored('\n[+] Streaming audit results\n', 'green'))
        for item in findings:
            color = severity_colors.get(item.severity, 'white')
            print(
                f"  [{colored(item.severity.upper(), color)}] "
                f"{item.target} — {item.check}: {item.detail}"
            )
        print()
