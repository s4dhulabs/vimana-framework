# -*- coding: utf-8 -*-
"""
Exception Monitor client (Fase 3).

Thin, fail-soft bridge from plugins (djunch / d4m8) to the legacy
Exception Monitor HTTP API (`core/api/backend/vf_server.py`).

Safety rules:
  - OFF by default (no behavior change for fuzz engines)
  - Opt-in via handler ``monitor_enabled=True`` or env ``VIMANA_MONITOR_ENABLED=1``
  - Never raises into the caller (network / prepare errors are swallowed)
  - Does not start the monitor server; caller must have it running
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping, Optional

DEFAULT_MONITOR_URL = 'http://127.0.0.1:8000'


def _truthy(value: Any) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def is_monitor_enabled(handler: Optional[Mapping[str, Any]] = None) -> bool:
    """Return True only when explicitly opted in."""
    env = os.getenv('VIMANA_MONITOR_ENABLED', '')
    if _truthy(env):
        return True
    if handler:
        for key in ('monitor_enabled', 'exception_monitor', 'dashboard_enabled'):
            if _truthy(handler.get(key)):
                return True
    return False


def monitor_base_url(handler: Optional[Mapping[str, Any]] = None) -> str:
    if handler:
        for key in ('monitor_url', 'dashboard_url', 'exception_monitor_url'):
            raw = handler.get(key)
            if raw and raw is not False:
                return str(raw).rstrip('/')
    return (os.getenv('VIMANA_MONITOR_URL') or DEFAULT_MONITOR_URL).rstrip('/')


def publish_environment(
    app_env: Dict[str, Any],
    *,
    handler: Optional[Mapping[str, Any]] = None,
    base_url: Optional[str] = None,
) -> bool:
    """POST environment map to the monitor. Returns True on HTTP success."""
    if not is_monitor_enabled(handler):
        return False
    if not app_env:
        return False
    url = f'{(base_url or monitor_base_url(handler))}/environment'
    try:
        import httpx
        resp = httpx.post(url, json=app_env, timeout=3.0)
        return 200 <= resp.status_code < 300
    except Exception:
        return False


def publish_exception(
    data: Dict[str, Any],
    *,
    handler: Optional[Mapping[str, Any]] = None,
    base_url: Optional[str] = None,
) -> bool:
    """POST exception payload to the monitor. Returns True on HTTP success."""
    if not is_monitor_enabled(handler):
        return False
    if not data:
        return False
    url = f'{(base_url or monitor_base_url(handler))}/exception'
    try:
        import httpx
        resp = httpx.post(url, json=data, timeout=5.0)
        return 200 <= resp.status_code < 300
    except Exception:
        return False


def publish_from_response(
    response: Any,
    exception_info: Dict[str, Any],
    *,
    handler: Optional[Mapping[str, Any]] = None,
    scan_id: Optional[str] = None,
    plugin: Optional[str] = None,
    app_name: Optional[str] = None,
    extracted_vars: Any = False,
    send_env_once: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    High-level helper: prepare + optional env + publish.
    Safe no-op when monitor is disabled.
    """
    if not is_monitor_enabled(handler):
        return False
    try:
        from core.api.dashboard_utils import prepare_dashboard_data

        payload = prepare_dashboard_data(
            response=response,
            exception_info=exception_info,
            extracted_vars=extracted_vars,
            scan_id=scan_id,
        )
        meta = payload.setdefault('exception_meta', {})
        if plugin:
            meta['plugin'] = plugin
        if app_name:
            vt = meta.setdefault('view_trigger', {})
            if isinstance(vt, dict):
                vt['app_name'] = app_name
        if send_env_once:
            publish_environment(send_env_once, handler=handler)
        return publish_exception(payload, handler=handler)
    except Exception:
        return False
