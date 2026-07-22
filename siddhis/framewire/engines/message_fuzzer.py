# -*- coding: utf-8 -*-
# Post-handshake WebSocket message / frame fuzz vectors and checks.

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from neotermcolor import colored

from core.vmnf_channels import register_channel
from siddhis.framewire.utils import get_hash


@dataclass
class FrameFinding:
    target: str
    check: str
    severity: str
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)


def select_vectors(mode: str, max_bytes: int) -> List[Tuple[str, Any, str]]:
    """
    Return list of (tag, payload, send_mode).
    send_mode: 'text' | 'bytes' | 'json'
    """
    mode = (mode or 'all').lower()
    vectors: List[Tuple[str, Any, str]] = []

    if mode in ('all', 'malformed'):
        vectors.extend([
            ('malformed_json', '{not json', 'text'),
            ('truncated_json', '{"type":"ping"', 'text'),
            ('empty_text', '', 'text'),
            ('null_bytes', 'framewire\x00probe', 'text'),
        ])

    if mode in ('all', 'type'):
        vectors.extend([
            ('type_confusion_array', [1, 2, 3], 'json'),
            ('type_confusion_null', None, 'json'),
            ('type_confusion_number', 42, 'json'),
            ('type_confusion_bool', True, 'json'),
            ('prototype_pollution', {'__proto__': {'admin': True}, 'type': 'msg'}, 'json'),
            ('deep_nesting', {'a': {'b': {'c': {'d': {'e': 'framewire'}}}}}, 'json'),
        ])

    if mode in ('all', 'oversized'):
        size = max(1024, int(max_bytes))
        vectors.extend([
            ('oversized_text', 'A' * size, 'text'),
            ('oversized_json', {'blob': 'B' * size, 'type': 'bulk'}, 'json'),
        ])

    if mode in ('all', 'cross_session'):
        vectors.append(('cross_session_marker', {'type': 'framewire_leak', 'secret': 'tenant-a-secret'}, 'json'))

    if not vectors:
        vectors = select_vectors('all', max_bytes)

    return vectors


class FrameMessageAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.timeout = aiohttp.ClientTimeout(total=handler.get('timeout', 20))
        self.vectors_mode = handler.get('frame_vectors') or 'all'
        self.max_bytes = int(handler.get('frame_max_bytes') or 65536)
        self.auth_header = handler.get('frame_auth_header') or handler.get('ws_auth_header')
        self.verbose = bool(handler.get('verbose'))

    def _base_headers(self) -> Dict[str, str]:
        headers = {}
        raw = self.auth_header
        if not raw:
            return headers
        if ':' in str(raw):
            key, value = str(raw).split(':', 1)
            headers[key.strip()] = value.strip()
        else:
            headers['Authorization'] = str(raw)
        return headers

    async def _connect(self, url: str):
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            ws = await session.ws_connect(url, headers=self._base_headers())
            return session, ws
        except Exception:
            await session.close()
            raise

    async def _try_connect(self, url: str) -> bool:
        try:
            session, ws = await self._connect(url)
            await ws.close()
            await session.close()
            return True
        except Exception:
            return False

    async def _send_payload(self, ws, payload: Any, send_mode: str) -> None:
        if send_mode == 'json':
            await ws.send_json(payload)
        elif send_mode == 'bytes':
            data = payload if isinstance(payload, (bytes, bytearray)) else str(payload).encode()
            await ws.send_bytes(data)
        else:
            await ws.send_str(str(payload))

    async def _recv_once(self, ws, wait: float = 2.0) -> Optional[Any]:
        try:
            msg = await asyncio.wait_for(ws.receive(), timeout=wait)
            if msg.type == aiohttp.WSMsgType.TEXT:
                return msg.data
            if msg.type == aiohttp.WSMsgType.BINARY:
                return msg.data
            if msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                return {'__closed__': True, 'code': msg.data, 'extra': msg.extra}
            if msg.type == aiohttp.WSMsgType.ERROR:
                return {'__error__': str(ws.exception())}
        except asyncio.TimeoutError:
            return None
        return None

    async def audit_endpoint(self, target: Dict[str, str]) -> List[FrameFinding]:
        url = target['url']
        findings: List[FrameFinding] = []
        vectors = select_vectors(self.vectors_mode, self.max_bytes)

        # Baseline: connection must work for frame fuzz
        try:
            session, ws = await self._connect(url)
        except Exception as exc:
            findings.append(FrameFinding(
                target=url,
                check='handshake_unavailable',
                severity='info',
                detail=f'Cannot open WebSocket for frame fuzz: {exc}',
            ))
            return findings

        try:
            # Drain welcome message if any
            await self._recv_once(ws, wait=1.0)

            for tag, payload, send_mode in vectors:
                if tag == 'cross_session_marker':
                    continue  # handled separately

                try:
                    await self._send_payload(ws, payload, send_mode)
                    reply = await self._recv_once(ws, wait=2.0)

                    if isinstance(reply, dict) and reply.get('__closed__'):
                        findings.append(FrameFinding(
                            target=url,
                            check='frame_closed_on_payload',
                            severity='info',
                            detail=f'Server closed connection on {tag}',
                            evidence={'tag': tag, 'close': reply},
                        ))
                        # reconnect for remaining vectors
                        await ws.close()
                        await session.close()
                        session, ws = await self._connect(url)
                        await self._recv_once(ws, wait=1.0)
                        continue

                    if isinstance(reply, dict) and reply.get('__error__'):
                        findings.append(FrameFinding(
                            target=url,
                            check='frame_protocol_error',
                            severity='medium',
                            detail=f'Protocol error after {tag}',
                            evidence={'tag': tag, 'error': reply['__error__']},
                        ))
                        continue

                    # Echo / accept of malformed or oversized payloads
                    if reply is not None and tag.startswith('malformed'):
                        findings.append(FrameFinding(
                            target=url,
                            check='malformed_payload_accepted',
                            severity='medium',
                            detail=f'Server accepted/reflected malformed payload ({tag})',
                            evidence={'tag': tag, 'reply_preview': str(reply)[:300]},
                        ))
                    elif reply is not None and tag.startswith('type_confusion'):
                        findings.append(FrameFinding(
                            target=url,
                            check='type_confusion_accepted',
                            severity='medium',
                            detail=f'Server accepted non-object JSON payload ({tag})',
                            evidence={'tag': tag, 'reply_preview': str(reply)[:300]},
                        ))
                    elif reply is not None and tag.startswith('oversized'):
                        findings.append(FrameFinding(
                            target=url,
                            check='oversized_frame_accepted',
                            severity='high',
                            detail=f'Server accepted oversized frame (~{self.max_bytes} bytes)',
                            evidence={'tag': tag, 'size': self.max_bytes, 'reply_preview': str(reply)[:200]},
                        ))
                    elif reply is not None and tag in ('prototype_pollution', 'deep_nesting'):
                        findings.append(FrameFinding(
                            target=url,
                            check='unsafe_json_shape_accepted',
                            severity='low',
                            detail=f'Server processed atypical JSON shape ({tag})',
                            evidence={'tag': tag, 'reply_preview': str(reply)[:300]},
                        ))
                    elif reply is None and tag.startswith('oversized'):
                        # timeout after oversized — possible hang / DoS signal
                        findings.append(FrameFinding(
                            target=url,
                            check='oversized_frame_hang',
                            severity='medium',
                            detail='No response within timeout after oversized frame (possible hang)',
                            evidence={'tag': tag, 'size': self.max_bytes},
                        ))

                    if self.verbose:
                        preview = str(reply)[:80] if reply is not None else 'timeout'
                        print(colored(f'  [{tag}] → {preview}', 'cyan'))

                except Exception as exc:
                    findings.append(FrameFinding(
                        target=url,
                        check='frame_send_error',
                        severity='low',
                        detail=f'Error sending {tag}: {exc}',
                        evidence={'tag': tag},
                    ))
                    try:
                        await ws.close()
                    except Exception:
                        pass
                    try:
                        await session.close()
                    except Exception:
                        pass
                    try:
                        session, ws = await self._connect(url)
                        await self._recv_once(ws, wait=1.0)
                    except Exception:
                        break
        finally:
            try:
                await ws.close()
            except Exception:
                pass
            try:
                await session.close()
            except Exception:
                pass

        # Cross-session message leak (room-style broadcast)
        if self.vectors_mode in ('all', 'cross_session'):
            leak = await self._cross_session_test(url)
            if leak:
                findings.append(leak)

        if not findings:
            findings.append(FrameFinding(
                target=url,
                check='no_frame_issues',
                severity='info',
                detail='No actionable frame/message findings for selected vectors',
            ))

        return findings

    async def _cross_session_test(self, url: str) -> Optional[FrameFinding]:
        """Two concurrent clients — marker from A should not appear on B unless shared room by design.
        For echo endpoints B won't see it; for broadcast rooms without auth, B will — HIGH.
        """
        marker = {'type': 'framewire_leak', 'secret': 'tenant-a-secret-9f3c'}
        try:
            session_a, ws_a = await self._connect(url)
            session_b, ws_b = await self._connect(url)
        except Exception:
            return None

        try:
            await self._recv_once(ws_a, wait=1.0)
            await self._recv_once(ws_b, wait=1.0)
            await ws_a.send_json(marker)
            # Give broadcast time
            leaked = None
            for _ in range(3):
                reply = await self._recv_once(ws_b, wait=1.5)
                if reply is None:
                    continue
                text = reply if isinstance(reply, str) else str(reply)
                if 'tenant-a-secret-9f3c' in text or 'framewire_leak' in text:
                    leaked = text
                    break

            if leaked:
                return FrameFinding(
                    target=url,
                    check='cross_session_message_leak',
                    severity='high',
                    detail='Message from session A was delivered to session B (cross-session leak)',
                    evidence={'marker': marker, 'preview': leaked[:400]},
                )
        except Exception as exc:
            return FrameFinding(
                target=url,
                check='cross_session_test_error',
                severity='info',
                detail=str(exc),
            )
        finally:
            for ws, session in ((ws_a, session_a), (ws_b, session_b)):
                try:
                    await ws.close()
                except Exception:
                    pass
                try:
                    await session.close()
                except Exception:
                    pass
        return None

    def register_channels(self, findings: List[FrameFinding], base_url: str) -> None:
        for finding in findings:
            if finding.severity not in ('high', 'medium'):
                continue
            channel_id = 'fw' + get_hash(finding.target + finding.check)[:6]
            register_channel({
                'channel_id': channel_id,
                'type': 'WebSocketFrame',
                'plugin': 'framewire',
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

    def print_findings(self, findings: List[FrameFinding]) -> None:
        if not findings:
            print(colored('[*] No frame/message findings.', 'yellow'))
            return

        severity_colors = {
            'high': 'red',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'white',
        }
        print(colored('\n[+] Frame/message fuzz results\n', 'green'))
        for item in findings:
            color = severity_colors.get(item.severity, 'white')
            print(
                f"  [{colored(item.severity.upper(), color)}] "
                f"{item.target} — {item.check}: {item.detail}"
            )
        print()
