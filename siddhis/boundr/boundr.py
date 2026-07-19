# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

import sys

from neotermcolor import colored
from core.vmnf_shared_args import VimanaSharedArgs
from core.vmnf_specs import list_specs

from siddhis.boundr.utils import should_show_banner, bd_banner
from siddhis.boundr.engines.spec_manager import SpecResolutionError
from siddhis.boundr.orchestrator import run_spec_scan, run_upload_audit


class siddhi:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler

    def _quiet(self) -> bool:
        return bool(
            self.vmnf_handler.get('ci_mode')
            or self.vmnf_handler.get('json_output')
        )

    def start(self):
        handler = self.vmnf_handler

        if handler.get('list_specs'):
            if self._quiet():
                from core.vmnf_specs import get_specs
                import json
                specs = get_specs()
                payload = [
                    {
                        'spec_id': s.spec_id,
                        'title': s.spec_title,
                        'host': s.spec_host,
                        'paths': s.spec_paths,
                        'methods': s.spec_methods,
                    }
                    for s in (specs or [])
                ]
                sys.stdout.write(json.dumps(payload, indent=2, default=str))
                sys.stdout.write('\n')
            else:
                list_specs()
            return True

        if should_show_banner(handler):
            bd_banner()

        scan_only = handler.get('api_scan_enabled') and not handler.get('upload_audit_enabled')

        if scan_only:
            try:
                run_spec_scan(handler)
                return True
            except SpecResolutionError as exc:
                self._fail(str(exc))

        if handler.get('upload_audit_enabled') or handler.get('target_url') or handler.get('upload_endpoint'):
            try:
                run_upload_audit(handler)
                return True
            except SpecResolutionError as exc:
                self._fail(str(exc))

        if not self._quiet():
            print(VimanaSharedArgs().shared_help.__doc__)
        sys.exit(1)

    def _fail(self, message: str) -> None:
        if self._quiet():
            import json
            sys.stdout.write(json.dumps({'error': message, 'passed': False}))
            sys.stdout.write('\n')
            sys.exit(2)
        print(colored(f'\n[!] {message}\n', 'red'))
        sys.exit(1)
