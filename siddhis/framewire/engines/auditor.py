# -*- coding: utf-8 -*-
# Orchestrates framewire post-handshake WebSocket message fuzz workflow.

import asyncio
from typing import Any, Dict, List, Optional

from neotermcolor import colored

from siddhis.framewire.engines.discovery import resolve_targets
from siddhis.framewire.engines.message_fuzzer import FrameFinding, FrameMessageAuditor
from siddhis.framewire.engines.spec_manager import FramewireSpecManager, SpecResolutionError


class FramewireAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.spec_manager = FramewireSpecManager(handler)
        self.frame_auditor = FrameMessageAuditor(handler)
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
            if await self.frame_auditor._try_connect(target['url']):
                live.append(target)
                if self.handler.get('verbose') and not self.quiet:
                    print(colored(
                        f'  [live] {target["url"]} ({target["source"]})',
                        'green',
                    ))
        return live

    async def run_async(self) -> Dict[str, Any]:
        api_specs: Optional[dict] = None
        base_url = ''
        spec_id = None

        try:
            api_specs, base_url, spec_id = await self.spec_manager.resolve()
        except SpecResolutionError:
            base_url = self.spec_manager._resolve_target_url() or ''
            if not base_url and (self.handler.get('frame_path') or self.handler.get('ws_path')):
                raise
            if not base_url:
                raise

        if not base_url:
            raise SpecResolutionError('Could not determine API base URL for frame audit')

        candidates = resolve_targets(self.handler, api_specs or {}, base_url)
        if not candidates:
            raise SpecResolutionError('No WebSocket candidate paths to fuzz')

        if not self.quiet:
            print(colored(
                f'\n[*] Probing {len(candidates)} WebSocket candidate(s) for frame fuzz on {base_url}',
                'cyan',
            ))

        live_targets = await self._probe_live_endpoints(candidates)

        if not live_targets and (self.handler.get('frame_path') or self.handler.get('ws_path')):
            live_targets = candidates
        elif not live_targets:
            if not self.quiet:
                print(colored(
                    '[!] No live WebSocket endpoints found. Try --frame-path explicitly.',
                    'yellow',
                ))
            return {
                'spec_id': spec_id,
                'base_url': base_url,
                'candidates': candidates,
                'targets': [],
                'findings': [],
            }

        all_findings: List[FrameFinding] = []
        for target in live_targets:
            findings = await self.frame_auditor.audit_endpoint(target)
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
            self.frame_auditor.print_findings(all_findings)

        if not self.handler.get('no_channels'):
            self.frame_auditor.register_channels(all_findings, base_url)

        return {
            'spec_id': spec_id,
            'base_url': base_url,
            'candidates': candidates,
            'targets': live_targets,
            'findings': findings_payload,
        }

    def run(self) -> Dict[str, Any]:
        return asyncio.run(self.run_async())
