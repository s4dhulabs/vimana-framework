# -*- coding: utf-8 -*-
"""Framework shared resources — OpenAPI specs + channels for Control API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from core.api.control.services import with_flask_db
from core._dbops_.vmnf_dbops import VFDBOps
from core.vmnf_specs import get_specs, load_spec_from_db

# Plugins that resolve OpenAPI via SpecManager (--apispec) or jcolt legacy path.
SPEC_CONSUMERS = (
    'boundr',
    'objgate',
    'fetchbane',
    'framewire',
    'socketline',
    'streamguard',
    'schemage',
    'roomgate',
    'jcolt',
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _spec_meta(record: Any) -> Dict[str, Any]:
    # VFSpecs PK column is named "index" but the ORM attr is "id" — avoid to_dict().
    keys = (
        'spec_id', 'spec_title', 'fastapi_version', 'openapi_version',
        'spec_host', 'spec_paths', 'spec_methods', 'spec_file_path', 'spec_date',
    )
    return {k: _jsonable(getattr(record, k, None)) for k in keys}


def _channel_dict(record: Any) -> Dict[str, Any]:
    if hasattr(record, 'to_dict'):
        raw = record.to_dict()
    else:
        raw = {
            'channel_id': getattr(record, 'channel_id', None),
            'type': getattr(record, 'type', None),
            'plugin': getattr(record, 'plugin', None),
            'target_url': getattr(record, 'target_url', None),
            'endpoint': getattr(record, 'endpoint', None),
            'method': getattr(record, 'method', None),
            'payload_template': getattr(record, 'payload_template', None),
            'description': getattr(record, 'description', None),
            'created_at': getattr(record, 'created_at', None),
            'last_verified': getattr(record, 'last_verified', None),
            'status': getattr(record, 'status', None),
            'channel_metadata': getattr(record, 'channel_metadata', None),
        }
    return {k: _jsonable(v) for k, v in raw.items()}


@with_flask_db
def list_specs() -> List[Dict[str, Any]]:
    return [_spec_meta(r) for r in get_specs()]


@with_flask_db
def get_spec(spec_id: str, include_body: bool = True) -> Optional[Dict[str, Any]]:
    record = VFDBOps().get_by_id('_SPECS_', 'spec_id', spec_id)
    if not record:
        return None
    out = _spec_meta(record)
    if include_body:
        try:
            body, host, sid = load_spec_from_db(spec_id)
        except ValueError:
            return None
        out['body'] = body
        out['spec_host'] = host or out.get('spec_host')
        out['spec_id'] = sid
    return out


@with_flask_db
def list_channels(
    plugin: Optional[str] = None,
    channel_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows = VFDBOps().getall('_CHANNELS_') or []
    out: List[Dict[str, Any]] = []
    for ch in rows:
        if plugin and getattr(ch, 'plugin', None) != plugin:
            continue
        if channel_type and getattr(ch, 'type', None) != channel_type:
            continue
        if status and getattr(ch, 'status', None) != status:
            continue
        out.append(_channel_dict(ch))
    return out


@with_flask_db
def get_channel(channel_id: str) -> Optional[Dict[str, Any]]:
    ch = VFDBOps().get_by_id('_CHANNELS_', 'channel_id', channel_id)
    if not ch:
        return None
    return _channel_dict(ch)


def spec_consumers() -> Dict[str, Any]:
    return {
        'plugins': list(SPEC_CONSUMERS),
        'note': (
            'Plugins that load a shared OpenAPI spec via --apispec / SpecManager '
            '(plus jcolt legacy).'
        ),
    }


_CASE_META_KEYS = (
    'case_id', 'case_name', 'case_target', 'case_date',
    'case_plugin', 'case_plugin_info', 'case_plugin_type', 'case_plugin_astt',
)


def _case_meta(record: Any, *, include_ns: bool = False) -> Dict[str, Any]:
    out = {k: _jsonable(getattr(record, k, None)) for k in _CASE_META_KEYS}
    if include_ns:
        out['case_ns'] = getattr(record, 'case_ns', None)
    return out


@with_flask_db
def list_cases() -> List[Dict[str, Any]]:
    rows = VFDBOps().getall('_CASES_') or []
    return [_case_meta(r) for r in rows]


@with_flask_db
def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    record = VFDBOps().get_by_id('_CASES_', 'case_id', case_id)
    if not record:
        return None
    out = _case_meta(record)
    try:
        plugin, args = case_run_args(record)
        out['run_hint'] = {'plugin': plugin, 'args': args}
    except Exception as exc:
        out['run_hint'] = None
        out['run_hint_error'] = f'{type(exc).__name__}: {exc}'
    return out


def case_run_args(record: Any) -> tuple:
    """Extract (plugin, args_dict) from a saved case without subprocess."""
    import jsonpickle

    raw_ns = getattr(record, 'case_ns', None)
    if raw_ns is None:
        raise ValueError('case has no case_ns')
    decoded = jsonpickle.decode(raw_ns) if isinstance(raw_ns, str) else raw_ns
    if hasattr(decoded, '__dict__'):
        data = dict(vars(decoded))
    elif isinstance(decoded, dict):
        data = dict(decoded)
    else:
        raise ValueError('unsupported case_ns payload')

    plugin = (
        data.get('module_run')
        or data.get('plugin_name')
        or getattr(record, 'case_plugin', None)
    )
    if not plugin:
        raise ValueError('case has no plugin')

    skip = {
        'args', 'save_case', 'load_case', 'module_run', 'plugin_name', 'module',
        'navigation_mode', 'start_resource', 'start_cases', 'start_scans',
        'start_tools', 'start_plugins', 'start_sessions', 'start_collections',
        'run_lab', 'lab_operation', 'lab_stop', 'lab_test', 'cleanup_labs',
        'runner_mode', 'docker_scope',
    }
    args: Dict[str, Any] = {}
    for key, val in data.items():
        if key in skip or key.startswith('_'):
            continue
        if isinstance(val, (str, int, float, bool)) or val is None:
            args[key] = False if val is None else val
    args.setdefault('json_output', True)
    args.setdefault('no_channels', True)
    return str(plugin), args


@with_flask_db
def run_case(case_id: str, *, async_job: bool = True) -> Any:
    from core.api.control.services import run_plugin

    record = VFDBOps().get_by_id('_CASES_', 'case_id', case_id)
    if not record:
        raise LookupError(f'case not found: {case_id}')
    plugin, args = case_run_args(record)
    return run_plugin(plugin, args, async_job=async_job)
