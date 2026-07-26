# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

from neotermcolor import colored
from core.spec_runtime import should_show_banner, get_hash, join_url  # noqa: F401


def bd_banner():
    """Multipart / UploadFile themed banner."""
    title = colored('BOUNDR', 39)
    subtitle = colored('Multipart & UploadFile Boundary Tester', 45)
    framework = colored('VimanaFramework v1.0', 8)
    print(
        f"""
    ╭────────────────────────────────────────╮
    │  ───{title}───  multipart/form-data  │
    │     UploadFile · boundary · MIME     │
    ╰────────────────────────────────────────╯
              {subtitle}
              {framework}
                    @s4dhulabs
        """
    )


def join_http_url(base_url: str, path: str) -> str:
    return join_url(base_url, path)
