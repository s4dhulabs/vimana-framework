# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

from neotermcolor import colored
from core.spec_runtime import should_show_banner, get_hash, join_url  # noqa: F401


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


CANARY_MARKER = 'FETCHBANE_CANARY_SECRET'
