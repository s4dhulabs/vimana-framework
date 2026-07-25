# -*- coding: utf-8 -*-
# Orchestrates fetchbane SSRF audit workflow.

import asyncio
from typing import Any, Dict, List, Optional

from neotermcolor import colored

from siddhis.fetchbane.engines.discovery import resolve_endpoints
from siddhis.fetchbane.engines.spec_manager import FetchbaneSpecManager, SpecResolutionError
from siddhis.fetchbane.engines.ssrf_auditor import SsrfAuditor, SsrfFinding


class FetchbaneAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.spec_manager = FetchbaneSpecManager(handler)
        self.ssrf = SsrfAuditor(handler)
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
            if not base_url and self.handler.get('ssrf_endpoint'):
                raise
            if not base_url:
                raise

        if not base_url:
            raise SpecResolutionError('Could not determine API base URL for SSRF audit')

        endpoints = resolve_endpoints(self.handler, api_specs or {})
        if not endpoints:
            raise SpecResolutionError('No SSRF candidate endpoints')

        if not self.quiet:
            print(colored(
                f'\n[*] Fetchbane: {len(endpoints)} endpoint(s) on {base_url}',
                'cyan',
            ))

        all_findings: List[SsrfFinding] = []
        targets = []
        for ep in endpoints:
            if not self.quiet and self.handler.get('verbose'):
                print(colored(f'  [endpoint] {ep}', 'white'))
            findings = self.ssrf.audit_endpoint(ep, base_url)
            all_findings.extend(findings)
            targets.append({
                'endpoint': ep,
                'source': 'cli' if self.handler.get('ssrf_endpoint') else 'discovery',
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
            self.ssrf.print_findings(all_findings)

        if not self.handler.get('no_channels'):
            self.ssrf.register_channels(all_findings, base_url)

        return {
            'spec_id': spec_id,
            'base_url': base_url,
            'candidates': [{'endpoint': e} for e in endpoints],
            'targets': targets,
            'findings': findings_payload,
        }

    def run(self) -> Dict[str, Any]:
        return asyncio.run(self.run_async())
