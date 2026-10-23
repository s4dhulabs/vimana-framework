# -*- coding: utf-8 -*-
"""CLI helpers for Exception Monitor (start / seed)."""

from __future__ import annotations

import json
import sys
from typing import Any, List, Optional


def run_monitor_cli(handler_ns: Any) -> None:
    """
    vimana monitor [--host] [--port]
    vimana monitor --seed-demo [--apps shop,blog]   # start + seed
    vimana monitor --seed [--url] [--apps ...]      # seed running server
    vimana monitor --reset [--url]
    """
    host = getattr(handler_ns, 'monitor_host', None) or '127.0.0.1'
    port = int(getattr(handler_ns, 'monitor_port', None) or 8000)
    url_raw = getattr(handler_ns, 'monitor_url', None)
    url = (
        str(url_raw).rstrip('/')
        if url_raw and url_raw is not False
        else f'http://{host}:{port}'
    )

    apps_raw = getattr(handler_ns, 'monitor_apps', None)
    apps: Optional[List[str]] = None
    if apps_raw and apps_raw is not False:
        apps = [a.strip() for a in str(apps_raw).split(',') if a.strip()]

    do_seed = bool(getattr(handler_ns, 'monitor_seed', False))
    seed_demo = bool(getattr(handler_ns, 'monitor_seed_demo', False))
    do_reset = bool(getattr(handler_ns, 'monitor_reset', False))

    if do_reset and not seed_demo:
        _reset_remote(url)
        if not do_seed:
            return

    if do_seed and not seed_demo:
        _seed_remote(url, reset=True, apps=apps)
        return

    from core.api.backend.vf_server import DashboardServer
    import core.api.backend.vf_server as vf

    server = DashboardServer()
    if seed_demo:
        from core.api.backend.mock_seed import seed_into_server
        result = seed_into_server(server, reset=True, apps=apps)
        print(json.dumps({'seeded_on_start': result}, indent=2, ensure_ascii=False))

    vf.server = server
    vf.app = server.app

    print(f'[vimana-monitor] http://{host}:{port}')
    print(f'[vimana-monitor] landing: http://{host}:{port}/')
    print(f'[vimana-monitor] demo seed: POST {url}/demo/seed')
    print(f'[vimana-monitor] real UI: cd core/api/frontend && npm run dev')
    print(f'[vimana-monitor]          → http://127.0.0.1:3000  (NEXT_PUBLIC_MONITOR_URL={url})')
    print(f'[vimana-monitor] Admin drawer: vimana api → /admin/ → Monitor')
    server.run(host=host, port=port)


def _seed_remote(url: str, *, reset: bool, apps: Optional[List[str]]) -> None:
    import httpx
    params = {'reset': 'true' if reset else 'false'}
    if apps:
        params['apps'] = ','.join(apps)
    endpoint = f'{url.rstrip("/")}/demo/seed'
    try:
        resp = httpx.post(endpoint, params=params, timeout=30.0)
        print(resp.text)
        if resp.status_code >= 400:
            sys.exit(1)
    except Exception as exc:
        print(f'[vimana-monitor] seed failed: {exc}', file=sys.stderr)
        print(f'[vimana-monitor] is the server running at {url}?', file=sys.stderr)
        sys.exit(1)


def _reset_remote(url: str) -> None:
    import httpx
    endpoint = f'{url.rstrip("/")}/demo/reset'
    try:
        resp = httpx.post(endpoint, timeout=15.0)
        print(resp.text)
        if resp.status_code >= 400:
            sys.exit(1)
    except Exception as exc:
        print(f'[vimana-monitor] reset failed: {exc}', file=sys.stderr)
        sys.exit(1)
