# -*- coding: utf-8 -*-
# WebSocket handshake security checks.

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp
from neotermcolor import colored

from core.vmnf_channels import register_channel
from siddhis.socketline.utils import get_hash


@dataclass
class HandshakeFinding:
    target: str
    check: str
    severity: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


class WebSocketHandshakeAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.timeout = aiohttp.ClientTimeout(total=handler.get('timeout', 15))
        self.auth_header = handler.get('ws_auth_header')
        self.custom_origin = handler.get('ws_origin')
        self.dual_session = bool(handler.get('ws_dual_session'))
        self.verbose = bool(handler.get('verbose'))

    def _base_headers(self) -> Dict[str, str]:
        headers = {}
        if self.auth_header:
            if ':' in self.auth_header:
                key, value = self.auth_header.split(':', 1)
                headers[key.strip()] = value.strip()
            else:
                headers['Authorization'] = self.auth_header
        return headers

    async def _try_connect(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        origin: Optional[str] = None,
    ) -> Dict[str, Any]:
        session_headers = dict(headers or {})
        if origin:
            session_headers['Origin'] = origin

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.ws_connect(url, headers=session_headers) as ws:
                    await ws.send_str(json.dumps({'type': 'ping', 'probe': 'socketline'}))
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=3)
                        payload = msg.data if msg.type == aiohttp.WSMsgType.TEXT else str(msg.data)
                    except asyncio.TimeoutError:
                        payload = None
                    return {
                        'connected': True,
                        'error': None,
                        'response': payload,
                    }
        except Exception as exc:
            return {
                'connected': False,
                'error': str(exc),
                'response': None,
            }

    async def audit_endpoint(self, target: Dict[str, str]) -> List[HandshakeFinding]:
        url = target['url']
        findings: List[HandshakeFinding] = []

        unauth = await self._try_connect(url, headers={})
        if unauth['connected']:
            findings.append(HandshakeFinding(
                target=url,
                check='unauthenticated_handshake',
                severity='high',
                detail='WebSocket accepted connection without credentials',
                evidence={'response': unauth.get('response')},
            ))

        auth_headers = self._base_headers()
        if auth_headers:
            authed = await self._try_connect(url, headers=auth_headers)
            if authed['connected'] and not unauth['connected']:
                findings.append(HandshakeFinding(
                    target=url,
                    check='auth_required',
                    severity='info',
                    detail='Endpoint requires authentication on handshake',
                ))

        evil_origin = self.custom_origin or 'http://evil.socketline.local'
        origin_probe = await self._try_connect(
            url,
            headers=auth_headers,
            origin=evil_origin,
        )
        if origin_probe['connected']:
            findings.append(HandshakeFinding(
                target=url,
                check='origin_validation_missing',
                severity='medium',
                detail=f'Handshake accepted spoofed Origin: {evil_origin}',
                evidence={'origin': evil_origin},
            ))

        if self.dual_session and auth_headers:
            first = await self._try_connect(url, headers=auth_headers)
            second = await self._try_connect(url, headers=auth_headers)
            if first['connected'] and second['connected']:
                findings.append(HandshakeFinding(
                    target=url,
                    check='dual_session_allowed',
                    severity='low',
                    detail='Multiple concurrent authenticated sessions accepted',
                ))

        if not findings and not unauth['connected'] and not auth_headers:
            findings.append(HandshakeFinding(
                target=url,
                check='handshake_rejected',
                severity='info',
                detail=f'No open handshake: {unauth.get("error")}',
            ))

        return findings

    def register_channels(self, findings: List[HandshakeFinding], base_url: str) -> None:
        for finding in findings:
            if finding.severity not in ('high', 'medium'):
                continue
            channel_id = 'sl' + get_hash(finding.target + finding.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'WebSocket',
                'plugin': 'socketline',
                'target_url': base_url,
                'endpoint': finding.target,
                'method': 'WS',
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

    def print_findings(self, findings: List[HandshakeFinding]) -> None:
        if not findings:
            print(colored('[*] No WebSocket endpoints produced findings.', 'yellow'))
            return

        severity_colors = {
            'high': 'red',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'white',
        }
        print(colored('\n[+] WebSocket audit results\n', 'green'))
        for item in findings:
            color = severity_colors.get(item.severity, 'white')
            print(
                f"  [{colored(item.severity.upper(), color)}] "
                f"{item.target} — {item.check}: {item.detail}"
            )
        print()
