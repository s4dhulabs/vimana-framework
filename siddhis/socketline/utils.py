# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

import hashlib
from neotermcolor import colored


def sl_banner():
    print(
        f"""
            _
         -='-ø'`
              \\ \\
               ø {colored('S0cketline', 39)}
              .ø |.---,
              :ø ||  |
               \\ ~   |
                '._.'
                {colored('VimanaFramework v1.0', 8)}
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
