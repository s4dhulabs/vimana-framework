# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

from neotermcolor import colored
from core.spec_runtime import should_show_banner, get_hash, join_url  # noqa: F401
from core.vmnf_specs import get_methods  # noqa: F401


def sl_banner():
    """WebSocket / network themed banner (not jcolt saxophone)."""
    title = colored('SOCKETLINE', 39)
    subtitle = colored('WebSocket Security Auditor', 45)
    framework = colored('VimanaFramework v1.0', 8)
    print(
        f"""
    ◉───────────╮         ╭───────────◉
     \\   ws://  \\───────/  wss://   /
      \\         \\  {title}  /         /
       ◉─────────◉─────────◉─────────◉
              {subtitle}
              {framework}
                    @s4dhulabs
        """
    )


def http_to_ws_url(url: str) -> str:
    url = url.rstrip('/')
    if url.startswith('https://'):
        return 'wss://' + url[len('https://'):]
    if url.startswith('http://'):
        return 'ws://' + url[len('http://'):]
    if url.startswith('ws://') or url.startswith('wss://'):
        return url
    return 'ws://' + url


def join_ws_url(base_url: str, path: str) -> str:
    base = http_to_ws_url(base_url.rstrip('/'))
    if not path.startswith('/'):
        path = '/' + path
    return base + path
