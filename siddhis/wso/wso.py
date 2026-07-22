# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

import sys

from neotermcolor import colored
from core.vmnf_shared_args import VimanaSharedArgs

from siddhis.wso.utils import should_show_banner, wso_banner
from siddhis.wso.orchestrator import run_wso


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

        if should_show_banner(handler):
            wso_banner()

        has_target = bool(
            handler.get('api_scan_enabled')
            or handler.get('target_url')
            or handler.get('apispec_enabled')
            or handler.get('ws_path')
            or handler.get('frame_path')
        )

        if not has_target:
            if not self._quiet():
                print(VimanaSharedArgs().shared_help.__doc__)
            sys.exit(1)

        try:
            run_wso(handler)
            return True
        except ValueError as exc:
            self._fail(str(exc))
        except Exception as exc:
            self._fail(str(exc))

    def _fail(self, message: str) -> None:
        if self._quiet():
            import json
            sys.stdout.write(json.dumps({'error': message, 'passed': False}))
            sys.stdout.write('\n')
            sys.exit(2)
        print(colored(f'\n[!] {message}\n', 'red'))
        sys.exit(1)
