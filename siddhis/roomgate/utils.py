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


def rg_banner():
    title = colored('ROOMGATE', 39)
    subtitle = colored('WebSocket Room Authz & IDOR Auditor', 45)
    framework = colored('VimanaFramework v1.0', 8)
    print(
        f"""
    ╭────────────────────────────────────────╮
    │  ⌂  {title}  ⌂  /ws/room/{{id}}       │
    │     IDOR · tenancy · membership      │
    ╰────────────────────────────────────────╯
              {subtitle}
              {framework}
                    @s4dhulabs
        """
    )


def get_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


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


def render_room_path(template: str, room_id: str) -> str:
    """Replace {id}, {room_id}, :id style placeholders."""
    path = template
    for token in ('{room_id}', '{id}', ':room_id', ':id'):
        if token in path:
            path = path.replace(token, str(room_id))
    if path == template and not path.rstrip('/').endswith(str(room_id)):
        # bare prefix like /ws/room → /ws/room/<id>
        path = path.rstrip('/') + '/' + str(room_id)
    return path
