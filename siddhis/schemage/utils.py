# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

from neotermcolor import colored
from core.spec_runtime import should_show_banner, get_hash, join_url  # noqa: F401


def sg_banner():
    title = colored('SCHEMAGE', 39)
    subtitle = colored('GraphQL Security Auditor', 45)
    framework = colored('VimanaFramework v1.0', 8)
    print(
        f"""
    ╭────────────────────────────────────────╮
    │  ⌂  {title}  ⌂  /graphql              │
    │     introspect · depth · field IDOR  │
    ╰────────────────────────────────────────╯
              {subtitle}
              {framework}
                    @s4dhulabs
        """
    )


def parse_auth_header(raw) -> dict:
    if not raw:
        return {}
    raw = str(raw)
    if ':' in raw and not raw.lower().startswith('bearer '):
        key, value = raw.split(':', 1)
        return {key.strip(): value.strip()}
    return {'Authorization': raw}
