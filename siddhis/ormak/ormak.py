# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

import json
import sys

from core.vmnf_shared_args import VimanaSharedArgs
from siddhis.ormak.engines.auditor import run_audit


class siddhi:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler

    def _quiet(self) -> bool:
        handler = self.vmnf_handler
        return bool(handler.get('ci_mode') or handler.get('json_output'))

    def start(self):
        handler = self.vmnf_handler
        if not handler.get('orm_audit_enabled') and not handler.get('target_url'):
            if not self._quiet():
                print(VimanaSharedArgs().shared_help.__doc__)
            return False

        result = run_audit(handler)
        if self._quiet():
            sys.stdout.write(json.dumps(result, indent=2))
            sys.stdout.write('\n')
        else:
            self._print(result)
        return True

    def _print(self, result: dict) -> None:
        state = 'vulnerable' if result.get('vulnerable') else 'clean'
        print(f"[ormak] {state} {result.get('endpoint')}")
        print(
            f"  lookup={result.get('lookup')} "
            f"baseline={result.get('baseline_count')} "
            f"invalid={result.get('invalid_count')} "
            f"relational={result.get('relational_count')}"
        )
        safe = result.get('safe') or {}
        if safe:
            print(f"  safe={safe.get('endpoint')} rejects={safe.get('rejects')}")
        canary = result.get('canary') or {}
        if canary.get('recovered'):
            print(
                f"  canary field={canary.get('field')} "
                f"recovered={canary.get('recovered')} "
                f"exact={canary.get('exact')} "
                f"case_insensitive={canary.get('case_insensitive')}"
            )
