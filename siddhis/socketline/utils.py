# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

import hashlib
from neotermcolor import colored


def should_show_banner(handler: dict) -> bool:
    """Banner is opt-in only (--banner). Off by default for pipes/CI."""
    if handler.get('ci_mode') or handler.get('json_output') or handler.get('no_metadata'):
        return False
    return bool(handler.get('show_banner'))


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


def get_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def get_methods(api_specs: dict) -> str:
    methods = set()
    for path_item in api_specs.get('paths', {}).values():
        if not isinstance(path_item, dict):
            continue
        for method in path_item:
            if method.lower() in {
                'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace',
            }:
                methods.add(method.upper())
    return ','.join(sorted(methods)) or 'N/A'


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
