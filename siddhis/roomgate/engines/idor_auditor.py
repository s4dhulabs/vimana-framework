# -*- coding: utf-8 -*-
# Room / channel authorization & IDOR checks over WebSocket.

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from neotermcolor import colored

from core.vmnf_channels import register_channel
from siddhis.roomgate.utils import get_hash, join_ws_url, render_room_path


@dataclass
class RoomFinding:
    target: str
    check: str
    severity: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


def _parse_auth_header(raw) -> Dict[str, str]:
    if not raw:
        return {}
    raw = str(raw)
    if ':' in raw and not raw.lower().startswith('bearer '):
        # "Authorization: Bearer x" or "X-User: a"
        key, value = raw.split(':', 1)
        return {key.strip(): value.strip()}
    return {'Authorization': raw}


class RoomAuthzAuditor:
    """
    Probes WebSocket room paths for:
    - unauthenticated join
    - horizontal IDOR (identity A joins room B)
    - membership / tenant isolation failures
    """

    def __init__(self, handler: dict):
        self.handler = handler
        self.timeout = aiohttp.ClientTimeout(total=handler.get('timeout', 15))
        self.verbose = bool(handler.get('verbose'))
        self.auth_a = (
            handler.get('room_auth_a')
            or handler.get('room_auth_header')
            or handler.get('ws_auth_header')
            or 'Bearer user-a'
        )
        self.auth_b = handler.get('room_auth_b') or 'Bearer user-b'
        self.checks_mode = (handler.get('room_checks') or 'all').lower()

    async def _attempt_join(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        expect_open: bool = True,
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Try WS connect + read first message.
        Returns (opened, close_reason_or_error, first_payload).
        """
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            ws = await session.ws_connect(url, headers=headers or {})
            payload = None
            try:
                msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        import json
                        payload = json.loads(msg.data)
                    except Exception:
                        payload = {'raw': msg.data}
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    await ws.close()
                    await session.close()
                    return False, msg.data or 'closed', None
            except asyncio.TimeoutError:
                payload = {'note': 'no_welcome_message'}
            await ws.close()
            await session.close()
            return True, None, payload
        except Exception as exc:
            await session.close()
            return False, str(exc), None

    async def audit_template(
        self,
        template: str,
        base_url: str,
        room_a: str,
        room_b: str,
    ) -> List[RoomFinding]:
        findings: List[RoomFinding] = []
        path_a = render_room_path(template, room_a)
        path_b = render_room_path(template, room_b)
        url_a = join_ws_url(base_url, path_a)
        url_b = join_ws_url(base_url, path_b)
        headers_a = _parse_auth_header(self.auth_a)
        headers_b = _parse_auth_header(self.auth_b)

        mode = self.checks_mode

        # 1) Unauthenticated join of room A
        if mode in ('all', 'unauth'):
            opened, err, payload = await self._attempt_join(url_a, headers=None)
            if opened:
                findings.append(RoomFinding(
                    target=url_a,
                    check='unauthenticated_room_join',
                    severity='high',
                    detail=(
                        f'Unauthenticated client joined room {room_a!r} via {path_a}. '
                        'Room membership should require authentication.'
                    ),
                    evidence={
                        'path': path_a,
                        'room_id': room_a,
                        'welcome': payload,
                    },
                ))
            elif self.verbose:
                print(colored(f'  [ok] unauth denied on {path_a}: {err}', 'green'))

        # 2) Horizontal IDOR: identity A joins room B
        if mode in ('all', 'idor', 'horizontal'):
            opened, err, payload = await self._attempt_join(url_b, headers=headers_a)
            if opened:
                # Confirm identity A is not supposed to own room B — if welcome
                # acknowledges join, treat as IDOR (lab + typical BOLA).
                findings.append(RoomFinding(
                    target=url_b,
                    check='cross_tenant_room_idor',
                    severity='high',
                    detail=(
                        f'Identity A ({self.auth_a!r}) joined room {room_b!r} '
                        f'(expected isolation to {room_a!r}). Possible BOLA/IDOR on room_id.'
                    ),
                    evidence={
                        'path': path_b,
                        'room_id': room_b,
                        'auth': self.auth_a,
                        'welcome': payload,
                        'expected_room': room_a,
                    },
                ))
            elif self.verbose:
                print(colored(f'  [ok] IDOR blocked on {path_b}: {err}', 'green'))

        # 3) Dual-identity sanity: A can join own room (info if fails — misconfig)
        if mode in ('all', 'membership'):
            opened_own, err_own, payload_own = await self._attempt_join(url_a, headers=headers_a)
            opened_peer, err_peer, _ = await self._attempt_join(url_b, headers=headers_b)

            if opened_own and opened_peer:
                # Both identities work on their rooms — baseline ok (info)
                findings.append(RoomFinding(
                    target=url_a,
                    check='membership_baseline',
                    severity='info',
                    detail=(
                        f'Both identities joined their respective rooms '
                        f'({room_a} / {room_b}). Use with IDOR results for context.'
                    ),
                    evidence={
                        'room_a_ok': True,
                        'room_b_ok': True,
                        'welcome_a': payload_own,
                    },
                ))
            elif not opened_own:
                findings.append(RoomFinding(
                    target=url_a,
                    check='membership_own_denied',
                    severity='low',
                    detail=(
                        f'Identity A could not join claimed room {room_a!r}: {err_own}. '
                        'Auth header or room mapping may be wrong for this target.'
                    ),
                    evidence={'error': err_own, 'auth': self.auth_a},
                ))

        # 4) Guest / weak token on admin-ish room id
        if mode in ('all', 'vertical'):
            admin_path = render_room_path(template, 'admin')
            admin_url = join_ws_url(base_url, admin_path)
            opened, err, payload = await self._attempt_join(admin_url, headers=headers_a)
            if opened:
                findings.append(RoomFinding(
                    target=admin_url,
                    check='vertical_privilege_room',
                    severity='medium',
                    detail=(
                        f'Non-admin identity joined privileged-looking room path {admin_path}. '
                        'Check vertical authorization on room identifiers.'
                    ),
                    evidence={'path': admin_path, 'welcome': payload, 'auth': self.auth_a},
                ))

        return findings

    def print_findings(self, findings: List[RoomFinding]) -> None:
        if not findings:
            print(colored('\n[+] No room authorization findings.', 'green'))
            return
        print(colored(f'\n[*] Roomgate findings: {len(findings)}', 'cyan'))
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

    def register_channels(self, findings: List[RoomFinding], base_url: str) -> None:
        import json
        for f in findings:
            if f.severity not in ('high', 'medium'):
                continue
            channel_id = 'rg' + get_hash(f.target + f.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'WebSocketRoomAuthz',
                'plugin': 'roomgate',
                'target_url': base_url,
                'endpoint': f.target,
                'method': 'WS',
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
