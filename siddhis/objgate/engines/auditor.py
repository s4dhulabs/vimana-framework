# -*- coding: utf-8 -*-
# Orchestrates objgate HTTP REST object authz / BOLA workflow.

import asyncio
from typing import Any, Dict, List, Optional

from neotermcolor import colored

from siddhis.objgate.engines.bola_auditor import ObjBolaAuditor, ObjFinding
from siddhis.objgate.engines.discovery import build_targets, resolve_obj_pair, resolve_templates
from siddhis.objgate.engines.spec_manager import ObjgateSpecManager, SpecResolutionError


class ObjgateAuditor:
    def __init__(self, handler: dict):
        self.handler = handler
        self.spec_manager = ObjgateSpecManager(handler)
        self.bola_auditor = ObjBolaAuditor(handler)
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
            if not base_url and self.handler.get('obj_path'):
                raise
            if not base_url:
                raise

        if not base_url:
            raise SpecResolutionError('Could not determine API base URL for object audit')

        obj_a, obj_b = resolve_obj_pair(self.handler)
        templates = resolve_templates(self.handler, api_specs or {})
        if not templates:
            raise SpecResolutionError('No object path templates to audit')

        if not self.quiet:
            print(colored(
                f'\n[*] Objgate: {len(templates)} template(s) on {base_url} '
                f'(objects {obj_a!r} / {obj_b!r})',
                'cyan',
            ))

        all_findings: List[ObjFinding] = []
        targets = build_targets(templates, base_url, obj_a, obj_b)
        if self.handler.get('obj_path'):
            for t in targets:
                t['source'] = 'cli'
        else:
            for t in targets:
                t['source'] = 'discovery'

        for template in templates:
            if not self.quiet and self.handler.get('verbose'):
                print(colored(f'  [template] {template}', 'white'))
            findings = self.bola_auditor.audit_template(
                template, base_url, obj_a, obj_b,
            )
            all_findings.extend(findings)

        findings_payload = [f.to_dict() for f in all_findings]

        if not self.quiet:
            self.bola_auditor.print_findings(all_findings)

        if not self.handler.get('no_channels'):
            self.bola_auditor.register_channels(all_findings, base_url)

        return {
            'spec_id': spec_id,
            'base_url': base_url,
            'candidates': [{'template': t} for t in templates],
            'targets': targets,
            'findings': findings_payload,
            'objects': {'a': obj_a, 'b': obj_b},
        }

    def run(self) -> Dict[str, Any]:
        return asyncio.run(self.run_async())
