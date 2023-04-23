# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import requests
from packaging.version import Version


def get_release(search_version):
    import requests
    from packaging.version import Version

    django_version = Version(search_version)  # replace with the desired version
    pypi_url = f"https://pypi.org/pypi/Django/json"
    release_info = False

    response = requests.get(pypi_url)
    if response.status_code == 200:
        data = response.json()
        releases = data["releases"]
        release_info = releases[str(django_version)][0]

        for release in releases:
            if Version(release) == django_version:
                break

    return release_info


