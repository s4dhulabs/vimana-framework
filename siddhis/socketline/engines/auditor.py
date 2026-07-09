# -*- coding: utf-8 -*-
# Orchestrates socketline WebSocket security audit workflow.

import asyncio
from typing import Any, Dict, List, Optional

from neotermcolor import colored

from siddhis.socketline.engines.discovery import resolve_targets
from siddhis.socketline.engines.handshake import HandshakeFinding, WebSocketHandshakeAuditor
from siddhis.socketline.engines.spec_manager import SocketlineSpecManager, SpecResolutionError


class SocketlineAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.spec_manager = SocketlineSpecManager(handler)
        self.handshake = WebSocketHandshakeAuditor(handler)
        self.quiet = bool(
            handler.get('ci_mode')
            or handler.get('json_output')
            or handler.get('no_metadata')
        )

    async def _probe_live_endpoints(
        self,
        candidates: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        live = []
        for target in candidates:
            result = await self.handshake._try_connect(target['url'])
            if result['connected']:
                live.append(target)
                if self.handler.get('verbose') and not self.quiet:
                    print(colored(f'  [live] {target["url"]} ({target["source"]})', 'green'))
        return live

    async def run_async(self) -> Dict[str, Any]:
        api_specs: Optional[dict] = None
        base_url = ''
        spec_id = None
        candidates: List[Dict[str, str]] = []

        try:
            api_specs, base_url, spec_id = await self.spec_manager.resolve()
        except SpecResolutionError:
            base_url = self.spec_manager._resolve_target_url() or ''
            if not base_url and self.handler.get('ws_path'):
                raise
            if not base_url:
                raise

        if not base_url:
            raise SpecResolutionError('Could not determine API base URL for WebSocket audit')

        candidates = resolve_targets(self.handler, api_specs or {}, base_url)
        if not candidates:
            raise SpecResolutionError('No WebSocket candidate paths to audit')

        if not self.quiet:
            print(colored(
                f'\n[*] Probing {len(candidates)} WebSocket candidate(s) on {base_url}',
                'cyan',
            ))

        live_targets = await self._probe_live_endpoints(candidates)

        if not live_targets and self.handler.get('ws_path'):
            live_targets = candidates
        elif not live_targets:
            if not self.quiet:
                print(colored(
                    '[!] No live WebSocket endpoints found. Try --ws-path explicitly.',
                    'yellow',
                ))
            return {
                'spec_id': spec_id,
                'base_url': base_url,
                'candidates': candidates,
                'targets': [],
                'findings': [],
            }

        all_findings: List[HandshakeFinding] = []
        for target in live_targets:
            findings = await self.handshake.audit_endpoint(target)
            all_findings.extend(findings)

        findings_payload = [
            {
                'target': f.target,
                'check': f.check,
                'severity': f.severity,
                'detail': f.detail,
                'evidence': f.evidence,
            }
            for f in all_findings
        ]

        if not self.quiet:
            self.handshake.print_findings(all_findings)

        if not self.handler.get('no_channels'):
            self.handshake.register_channels(all_findings, base_url)

        return {
            'spec_id': spec_id,
            'base_url': base_url,
            'candidates': candidates,
            'targets': live_targets,
            'findings': findings_payload,
        }

    def run(self) -> Dict[str, Any]:
        return asyncio.run(self.run_async())
