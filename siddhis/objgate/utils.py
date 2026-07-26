# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

from neotermcolor import colored
from core.spec_runtime import should_show_banner, get_hash, join_url  # noqa: F401


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
