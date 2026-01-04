

import asyncio
from res.regex.secrets import secrets as secrets_regex
from neotermcolor import colored as cl
from time import sleep
import os
import re


class tool:
    def __init__(self, handler:dict=False):
        self.vmnf_handler = handler
        self.verified = []

    def run(self, _exceptions_:list=False):

        if not _exceptions_:
            return False

        for exception in _exceptions_:
            xid = exception.exception_id
            exception = exception.exception_meta
            summary = exception['summary']
            exception_type = summary.get('Exception Type')
            app_response = exception['app_response']
            tracebacks = exception['traceback']

            view_trigger_hash = hash(str(exception['view_trigger']))
            
            if view_trigger_hash in self.verified:
                continue

            self.verified.append(view_trigger_hash)

            for trigger in tracebacks:    
                if not exception['view_trigger']['fullpath'] == trigger['MODULE_TRIGGERS']['Module']:
                    continue

                for k,v in trigger['MODULE_TRIGGERS'].items():
                    print(f"    + {cl(k, 'green')} : {v}")
                print()

                for line in (trigger['HL_CODE_SNIPPET']):
                    print(line)
                    #sleep(0.1)

                print('-'*100)

        input()


