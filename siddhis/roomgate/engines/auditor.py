# -*- coding: utf-8 -*-
# Orchestrates roomgate WebSocket room authz / IDOR workflow.

import asyncio
from typing import Any, Dict, List, Optional

from neotermcolor import colored

from siddhis.roomgate.engines.discovery import resolve_room_pair, resolve_templates
from siddhis.roomgate.engines.idor_auditor import RoomAuthzAuditor, RoomFinding
from siddhis.roomgate.engines.spec_manager import RoomgateSpecManager, SpecResolutionError


class RoomgateAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.spec_manager = RoomgateSpecManager(handler)
        self.room_auditor = RoomAuthzAuditor(handler)
        self.quiet = bool(
            handler.get('ci_mode')
            or handler.get('json_output')
            or handler.get('no_metadata')
            or handler.get('quiet_output')
            or handler.get('_orchestrator')
        )

    async def run_async(self) -> Dict[str, Any]:
        api_specs: Optional[dict] = None
        base_url = ''
        spec_id = None

        try:
            api_specs, base_url, spec_id = await self.spec_manager.resolve()
        except SpecResolutionError:
            base_url = self.spec_manager._resolve_target_url() or ''
            if not base_url and (
                self.handler.get('room_path')
                or self.handler.get('ws_path')
                or self.handler.get('frame_path')
            ):
                raise
            if not base_url:
                raise

        if not base_url:
            raise SpecResolutionError('Could not determine API base URL for room audit')

        room_a, room_b = resolve_room_pair(self.handler)
        templates = resolve_templates(self.handler, api_specs or {}, base_url)
        if not templates:
            raise SpecResolutionError('No room path templates to audit')

        if not self.quiet:
            print(colored(
                f'\n[*] Roomgate: {len(templates)} template(s) on {base_url} '
                f'(rooms {room_a!r} / {room_b!r})',
                'cyan',
            ))

        all_findings: List[RoomFinding] = []
        targets: List[Dict[str, str]] = []

        for template in templates:
            if not self.quiet and self.handler.get('verbose'):
                print(colored(f'  [template] {template}', 'white'))
            findings = await self.room_auditor.audit_template(
                template, base_url, room_a, room_b,
            )
            all_findings.extend(findings)
            targets.append({
                'template': template,
                'room_a': room_a,
                'room_b': room_b,
                'source': 'cli' if self.handler.get('room_path') else 'discovery',
            })

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
            self.room_auditor.print_findings(all_findings)

        if not self.handler.get('no_channels'):
            self.room_auditor.register_channels(all_findings, base_url)

        return {
            'spec_id': spec_id,
            'base_url': base_url,
            'candidates': [{'template': t} for t in templates],
            'targets': targets,
            'findings': findings_payload,
            'rooms': {'a': room_a, 'b': room_b},
        }

    def run(self) -> Dict[str, Any]:
        return asyncio.run(self.run_async())
