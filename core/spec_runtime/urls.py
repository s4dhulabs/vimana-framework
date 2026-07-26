# -*- coding: utf-8 -*-
# URL helpers shared by specialty plugins.


def join_url(base_url: str, path: str) -> str:
    base = str(base_url or '').rstrip('/')
    path = str(path or '')
    if not path.startswith('/'):
        path = '/' + path
    return base + path
