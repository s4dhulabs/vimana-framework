# -*- coding: utf-8 -*-
# Orchestrates schemage GraphQL audit workflow.

import asyncio
from typing import Any, Dict, List, Optional

from neotermcolor import colored

from siddhis.schemage.engines.gql_auditor import GraphQLAuditor, GqlFinding
from siddhis.schemage.engines.spec_manager import SchemageSpecManager, SpecResolutionError


class SchemageAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.spec_manager = SchemageSpecManager(handler)
        self.gql = GraphQLAuditor(handler)
        self.quiet = bool(
            handler.get('ci_mode')
            or handler.get('json_output')
            or handler.get('no_metadata')
            or handler.get('quiet_output')
            or handler.get('_orchestrator')
        )

    async def run_async(self) -> Dict[str, Any]:
        base_url = ''
        spec_id = None
        try:
            _, base_url, spec_id = await self.spec_manager.resolve()
        except SpecResolutionError:
            base_url = self.spec_manager._resolve_target_url() or ''
            if not base_url and self.handler.get('gql_path'):
                raise
            if not base_url:
                raise

        if not base_url:
            raise SpecResolutionError('Could not determine API base URL for GraphQL audit')

        path = str(self.handler.get('gql_path') or '/graphql')
        if not self.quiet:
            print(colored(f'\n[*] Schemage: auditing {base_url}{path}', 'cyan'))

        findings = self.gql.audit(base_url)
        findings_payload = [
            {
                'target': f.target,
                'check': f.check,
                'severity': f.severity,
                'detail': f.detail,
                'evidence': f.evidence,
            }
            for f in findings
        ]

        if not self.quiet:
            self.gql.print_findings(findings)

        if not self.handler.get('no_channels'):
            self.gql.register_channels(findings, base_url)

        return {
            'spec_id': spec_id,
            'base_url': base_url,
            'candidates': [{'path': path}],
            'targets': [{'path': path, 'source': 'cli'}],
            'findings': findings_payload,
        }

    def run(self) -> Dict[str, Any]:
        return asyncio.run(self.run_async())
