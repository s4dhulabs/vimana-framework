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


def og_banner():
    title = colored('OBJGATE', 39)
    subtitle = colored('HTTP REST Object Authz & BOLA Auditor', 45)
    framework = colored('VimanaFramework v1.0', 8)
    print(
        f"""
    ╭────────────────────────────────────────╮
    │  ⌂  {title}  ⌂  /api/resource/{{id}}   │
    │     BOLA · IDOR · BFLA (HTTP)        │
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


def render_obj_path(template: str, obj_id: str) -> str:
    """Replace {id}, {obj_id}, :id style placeholders."""
    path = template
    for token in ('{obj_id}', '{id}', ':obj_id', ':id'):
        if token in path:
            path = path.replace(token, str(obj_id))
    if path == template and not path.rstrip('/').endswith(str(obj_id)):
        path = path.rstrip('/') + '/' + str(obj_id)
    return path


def parse_auth_header(raw) -> dict:
    if not raw:
        return {}
    raw = str(raw)
    if ':' in raw and not raw.lower().startswith('bearer '):
        key, value = raw.split(':', 1)
        return {key.strip(): value.strip()}
    return {'Authorization': raw}
