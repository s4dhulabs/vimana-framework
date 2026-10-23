# -*- coding: utf-8 -*-
"""Uvicorn entry for Control API."""

from __future__ import annotations

import os


def serve_control_api(host: str = '127.0.0.1', port: int = 8090, reload: bool = False) -> None:
    """
    Start Framework Control API (local-first).

    Admin UI: http://{host}:{port}/admin/
    OpenAPI:  http://{host}:{port}/docs
    """
    import uvicorn

    # Ensure VIMANA_PATH points at repo root when launched via CLI
    if not os.getenv('VIMANA_PATH'):
        here = os.path.abspath(__file__)
        repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))
        if os.path.isdir(os.path.join(repo, 'siddhis')):
            os.environ['VIMANA_PATH'] = repo

    print(f'[vimana-control] http://{host}:{port}/admin/  (API docs: /docs)')
    uvicorn.run(
        'core.api.control.app:app',
        host=host,
        port=int(port),
        reload=reload,
        log_level='info',
    )
