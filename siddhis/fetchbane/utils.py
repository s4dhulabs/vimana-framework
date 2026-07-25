# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

import hashlib
from neotermcolor import colored


def should_show_banner(handler: dict) -> bool:
    if handler.get('ci_mode') or handler.get('json_output') or handler.get('no_metadata'):
        return False
    return bool(handler.get('show_banner'))


def fb_banner():
    title = colored('FETCHBANE', 39)
    subtitle = colored('Server-Side Request Forgery Auditor', 45)
    framework = colored('VimanaFramework v1.0', 8)
    print(
        f"""
    ╭────────────────────────────────────────╮
    │  ⌂  {title}  ⌂  ?url= / webhook      │
    │     SSRF · loopback · metadata       │
    ╰────────────────────────────────────────╯
              {subtitle}
              {framework}
                    @s4dhulabs
        """
    )


def get_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def join_url(base_url: str, path: str) -> str:
    base = str(base_url).rstrip('/')
    if not path.startswith('/'):
        path = '/' + path
    return base + path


CANARY_MARKER = 'FETCHBANE_CANARY_SECRET'
