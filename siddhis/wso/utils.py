# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

from neotermcolor import colored
from core.spec_runtime import should_show_banner, get_hash  # noqa: F401


def wso_banner():
    title = colored('WSO', 39)
    subtitle = colored('WebSockets Orchestrator', 45)
    framework = colored('VimanaFramework v1.0', 8)
    print(
        f"""
    ╭────────────────────────────────────────╮
    │  ⟦  {title}  ⟧  socketline → framewire │
    │     handshake · frames · channels    │
    ╰────────────────────────────────────────╯
              {subtitle}
              {framework}
                    @s4dhulabs
        """
    )
