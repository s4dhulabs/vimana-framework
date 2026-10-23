# -*- coding: utf-8 -*-
"""Control API service layer — wraps DB, orchestrators, labs without CLI banners/exits."""

from __future__ import annotations

import functools
import importlib
import inspect
import os
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from core._dbops_.database import app as flask_app
from core._dbops_.vmnf_dbops import VFDBOps
from core._version import __version__
from core.api.control.runs import RUN_STORE, RunRecord
from core.capabilities import get_capability, get_lab_meta
from core.labs.vmnf_labs import VimanaLabManager

F = TypeVar('F', bound=Callable[..., Any])


def with_flask_db(fn: F) -> F:
    """
    Flask-SQLAlchemy sessions are scoped to the current app context (thread-local).

    FastAPI runs sync route handlers in a threadpool, so the context pushed at
    `core._dbops_.database` import time on the main thread is invisible here.
    Push a fresh context on every DB-touching Control API call.
    """
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        with flask_app.app_context():
            return fn(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


# Preferred orchestrator entrypoints per plugin (when multiple run_* exist)
_AUDIT_ENTRYPOINTS = {
    'boundr': 'run_upload_audit',
    'socketline': 'run_ws_audit',
    'streamguard': 'run_stream_audit',
    'schemage': 'run_gql_audit',
    'roomgate': 'run_room_audit',
    'objgate': 'run_obj_audit',
    'framewire': 'run_frame_audit',
    'fetchbane': 'run_ssrf_audit',
    'wso': 'run_wso',
}


def base_handler(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Minimal handler dict suitable for leaf orchestrators (API / quiet)."""
    handler: Dict[str, Any] = {
        'json_output': True,
        'ci_mode': False,  # avoid sys.exit from auditors
        'debug': False,
        'verbose': False,
        'sample': False,
        'auto': False,
        'runner_mode': False,
        'docker_scope': False,
        'save_case': False,
        'load_case': False,
        'list_specs': False,
        'request_data_set': False,
        'no_channels': True,
        'external_disabled': False,
        'xray_enabled': False,
        'proxy': False,
        'proxy_type': False,
        'framework': False,
        'project_dir': False,
        'endpoint_url': False,
        'target_url': False,
        'target': False,
        'scope': False,
        'file_scope': False,
        'ignore_state': False,
        'vf_debugger': False,
        'exit_on_trigger': False,
        'workflow': False,
        # Specialty flags often accessed with [] by older siddhis (e.g. jcolt)
        'export_body': False,
        'fuzzerspec_enabled': False,
        'api_scan_enabled': False,
        'apispec_enabled': False,
        'fingerprint': False,
        'colors_disabled': False,
        'list_pydantic_models': False,
        'list_field_constraints': False,
        'list_endpoint_models': False,
        'list_security_fields': False,
        'list_enums': False,
        'list_model_relationships': False,
        'list_validation_coverage': False,
        'list_op_ids': False,
        'list_parameters': False,
        'list_schemas': False,
        'list_response_codes': False,
        'list_examples': False,
        'list_tags': False,
        'list_paths': False,
        'schema_validate': False,
        'list_descriptions': False,
        'flush_spec': False,
        'flush_specs': False,
        'list_response_headers': False,
        'load_from_env': False,
        'describe_mode_enabled': False,
        'inspect': False,
        'navigation_mode': False,
        'output_table': False,
    }
    if extra:
        handler.update(extra)
    return handler


# Siddhis.id maps to SQL column "index" — do not use Model.to_dict() here.
_SIDDHI_FIELDS = (
    'name', 'author', 'brief', 'category', 'framework', 'info', 'module',
    'package', 'type', 'astt', 'tags', 'composition', 'description',
    'references', 'vfset', 'guide',
)


def _siddhi_row(row: Any) -> Dict[str, Any]:
    return {k: getattr(row, k, None) for k in _SIDDHI_FIELDS}


@with_flask_db
def health() -> Dict[str, Any]:
    plugins = VFDBOps().getall('_SIDDHIS_') or []
    return {
        'status': 'ok',
        'service': 'vimana-control-api',
        'version': __version__,
        'plugins_loaded': len(plugins),
    }


@with_flask_db
def about() -> Dict[str, Any]:
    """
    Framework overview for agents / Control (same spirit as `vimana about`).
    Structured JSON — not the ASCII banner.
    """
    from core._version import (
        FRAMEWORK_AUTHOR,
        FRAMEWORK_EMAIL,
        FRAMEWORK_NAME,
        FRAMEWORK_URL,
        get_version_info,
    )
    try:
        from res.vmnf_banners import about_text
        summary = about_text().strip()
    except Exception:
        summary = (
            'Vimana is a modular security framework for auditing Python APIs '
            'and web applications via plugins (siddhis).'
        )
    version_info = get_version_info()
    plugins_n = len(VFDBOps().getall('_SIDDHIS_') or [])
    return {
        'name': FRAMEWORK_NAME,
        'version': version_info.get('version') or __version__,
        'author': FRAMEWORK_AUTHOR,
        'email': FRAMEWORK_EMAIL,
        'url': FRAMEWORK_URL,
        'summary': summary,
        'capabilities': [
            'Vulnerability detection and exploitation',
            'Static and dynamic analysis',
            'Application crawling and discovery',
            'Persistence and post-exploitation analysis',
            'CI/CD security integration',
            'Plugin-based architecture (siddhis)',
            'Control API / Admin / MCP / native agent',
            'Docker labs per plugin (--lab / --test)',
        ],
        'plugins_loaded': plugins_n,
        'cli': {
            'about': 'vimana about',
            'list_plugins': 'vimana load --plugins',
            'guide': 'vimana guide -m <plugin>',
            'guide_args': 'vimana guide -m <plugin> -a',
            'guide_examples': 'vimana guide -m <plugin> -e',
            'run_lab_test': 'vimana run --lab <plugin> --test',
            'agent': 'vimana agent --policy safe "o que é a vimana?"',
        },
        'docs': [
            'docs/USER_GUIDE.md',
            'docs/CONTROL_API.md',
            'docs/MCP.md',
            'docs/LABS.md',
            'docs/AGENT.md',
        ],
    }


@with_flask_db
def explain_plugin(name: str, *, focus: str = 'overview') -> Dict[str, Any]:
    """
    Curated plugin card from YAML/DB guide (info, args, examples, labs).
    focus: overview | usage | args
    """
    detail = get_plugin(name)
    if not detail:
        raise LookupError(f'plugin not found: {name}')

    focus_l = (focus or 'overview').strip().lower()
    if focus_l in ('usage', 'how', 'howto', 'use', 'usar', 'guide', 'examples'):
        focus_l = 'usage'
    elif focus_l in ('args', 'arg', 'argument', 'arguments', 'flags', 'opts'):
        focus_l = 'args'
    else:
        focus_l = 'overview'

    guide = detail.get('guide') or {}
    has_lab = bool(detail.get('has_lab')) or _plugin_has_runnable_lab(name, detail)
    out: Dict[str, Any] = {
        'name': detail.get('name'),
        'focus': focus_l,
        'type': detail.get('type'),
        'category': detail.get('category'),
        'info': detail.get('info') or detail.get('brief'),
        'description': detail.get('description'),
        'framework': detail.get('framework'),
        'has_lab': has_lab,
        'has_orchestrator': detail.get('has_orchestrator'),
        'cli': {
            'info': f"vimana info --plugin {name}",
            'guide': f"vimana guide -m {name}",
            'guide_args': f"vimana guide -m {name} -a",
            'guide_examples': f"vimana guide -m {name} -e",
            'run_lab_test': (
                f"vimana run --lab {name} --test" if has_lab else None
            ),
            'agent_run': f'vimana agent --policy run "rode o {name}"',
        },
    }
    if focus_l == 'overview':
        out['guide'] = {
            'args_preview': (guide.get('args') or '')[:1200],
            'examples_preview': (guide.get('examples') or '')[:1200],
            'labs_preview': (guide.get('labs') or '')[:800],
        }
    elif focus_l == 'args':
        out['guide'] = {
            'args': guide.get('args') or '',
            'form': detail.get('form') or [],
            'specialty_args': (detail.get('capabilities') or {}).get('specialty_args') or {},
        }
    else:  # usage
        out['guide'] = {
            'args': guide.get('args') or '',
            'examples': guide.get('examples') or '',
            'labs': guide.get('labs') or '',
            'form': detail.get('form') or [],
        }
        lab_cap = (detail.get('capabilities') or {}).get('lab') or {}
        if lab_cap:
            out['lab'] = lab_cap
    return out


@with_flask_db
def list_plugins() -> List[Dict[str, Any]]:
    rows = VFDBOps().getall('_SIDDHIS_') or []
    out: List[Dict[str, Any]] = []
    for row in rows:
        data = _siddhi_row(row)
        name = data.get('name')
        cap = get_capability(name) if name else None
        out.append({
            'name': name,
            'type': data.get('type'),
            'category': data.get('category'),
            'astt': data.get('astt'),
            'info': data.get('info'),
            'has_lab': bool((cap or {}).get('lab')),
            'has_orchestrator': _has_orchestrator(name) if name else False,
        })
    return sorted(out, key=lambda p: (p.get('name') or ''))


@with_flask_db
def get_plugin(name: str) -> Optional[Dict[str, Any]]:
    from core.api.control.form_schema import build_plugin_form
    from core.vmnf_siddhi_schema import guide_section

    rows = VFDBOps().getall('_SIDDHIS_') or []
    row = next((r for r in rows if getattr(r, 'name', None) == name), None)
    if not row:
        return None
    data = _siddhi_row(row)
    cap = get_capability(name) or {}
    lab = get_lab_meta(name) or {}
    guide = data.get('guide') if isinstance(data.get('guide'), dict) else {}
    refs = data.get('references') if isinstance(data.get('references'), dict) else {}
    composition = data.get('composition') if isinstance(data.get('composition'), dict) else {}
    specialty = cap.get('specialty_args') or {}
    naviargs = guide.get('naviargs') if isinstance(guide.get('naviargs'), dict) else {}
    vfset = data.get('vfset') if isinstance(data.get('vfset'), dict) else {}

    form = build_plugin_form(
        plugin=name,
        specialty_args=specialty,
        naviargs=naviargs,
        lab=lab or cap.get('lab') or {},
        vfset=vfset,
    )

    return {
        'name': data.get('name'),
        'brief': data.get('brief'),
        'author': data.get('author'),
        'type': data.get('type'),
        'category': data.get('category'),
        'astt': data.get('astt'),
        'info': data.get('info'),
        'description': data.get('description'),
        'framework': data.get('framework'),
        'module': data.get('module'),
        'package': data.get('package'),
        'tags': data.get('tags') or [],
        'references': {
            'links': refs.get('links') or [],
            'cwe': refs.get('cwe') or [],
        },
        'composition': composition,
        'vfset': vfset,
        'guide': {
            'args': guide_section(guide, 'args'),
            'examples': guide_section(guide, 'examples'),
            'labs': guide_section(guide, 'lab_setup', 'labs'),
            'naviargs': naviargs,
        },
        'capabilities': {
            'lab': lab or cap.get('lab') or {},
            'specialty_args': specialty,
        },
        'form': form,
        'has_orchestrator': _has_orchestrator(name),
        'has_lab': bool(lab or (cap.get('lab') or {})),
    }


def _has_orchestrator(plugin: str) -> bool:
    try:
        importlib.import_module(f'siddhis.{plugin}.orchestrator')
        return True
    except Exception:
        return False


def resolve_run_callable(plugin: str) -> Tuple[Optional[Callable], Optional[str]]:
    """
    Resolve leaf orchestrator entrypoint.
    Preference: known audit map → run_{plugin} → first run_*_audit → any run_* except run_spec_scan.
    """
    try:
        mod = importlib.import_module(f'siddhis.{plugin}.orchestrator')
    except Exception as exc:
        return None, f'no orchestrator for {plugin}: {exc}'

    preferred = _AUDIT_ENTRYPOINTS.get(plugin)
    if preferred and hasattr(mod, preferred):
        return getattr(mod, preferred), preferred

    named = f'run_{plugin}'
    if hasattr(mod, named):
        return getattr(mod, named), named

    candidates = [
        name for name, obj in inspect.getmembers(mod, inspect.isfunction)
        if name.startswith('run_') and name != 'run_spec_scan'
        and obj.__module__ == mod.__name__
    ]
    audits = [c for c in candidates if c.endswith('_audit')]
    pick = (audits or candidates)
    if not pick:
        if hasattr(mod, 'run_spec_scan'):
            return getattr(mod, 'run_spec_scan'), 'run_spec_scan'
        return None, f'no run_* entrypoint in siddhis.{plugin}.orchestrator'

    pick.sort()
    return getattr(mod, pick[0]), pick[0]


def pad_handler_from_form(plugin: str, handler: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure specialty/form store_true dests exist (False) so older siddhis
    using handler['flag'] do not KeyError under Control API.
    """
    detail = get_plugin(plugin) or {}
    for field in detail.get('form') or []:
        dest = field.get('dest')
        if not dest or dest in handler:
            continue
        if field.get('action') == 'store_true' or field.get('type') == 'checkbox':
            handler[dest] = False
        else:
            default = field.get('default')
            handler[dest] = False if default in (None, False) else default
    return handler


@with_flask_db
def run_plugin(
    plugin: str,
    args: Optional[Dict[str, Any]] = None,
    *,
    async_job: bool = False,
    run_id: Optional[str] = None,
) -> RunRecord:
    """
    Execute plugin; store result in RUN_STORE.
    When async_job=True and run_id is None, enqueue background execution and return queued record.
    When run_id is set, execute that existing queued run (worker path).
    """
    import contextlib
    import io
    import threading

    from core.api.control.artifacts import collect_artifacts

    detail = get_plugin(plugin)
    if not detail:
        raise LookupError(f'plugin not found: {plugin}')

    if async_job and run_id is None:
        run = RUN_STORE.create(plugin, args, async_job=True)
        thread = threading.Thread(
            target=_run_plugin_worker,
            args=(plugin, dict(args or {}), run.run_id),
            name=f'run-{run.run_id[:8]}',
            daemon=True,
        )
        thread.start()
        return run

    if run_id:
        run = RUN_STORE.get(run_id)
        if not run:
            raise LookupError(f'run not found: {run_id}')
    else:
        run = RUN_STORE.create(plugin, args, async_job=False)

    RUN_STORE.mark_running(run.run_id)

    handler = base_handler(args)
    handler = pad_handler_from_form(plugin, handler)
    handler['module_run'] = plugin
    handler['module'] = plugin
    handler['plugin_name'] = plugin

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    report: Dict[str, Any] = {}
    error: Optional[str] = None

    fn, entry = resolve_run_callable(plugin)

    try:
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            if not fn:
                report = _run_via_siddhi_start(plugin, handler)
                report.setdefault('plugin', plugin)
                report.setdefault('_entrypoint', entry or 'siddhi.start')
            else:
                sig = inspect.signature(fn)
                if 'handler' in sig.parameters:
                    raw = fn(handler)
                else:
                    raw = fn(**handler)
                if not isinstance(raw, dict):
                    report = {'result': raw, 'plugin': plugin, 'entrypoint': entry}
                else:
                    report = raw
                report.setdefault('plugin', plugin)
                report.setdefault('_entrypoint', entry)
    except SystemExit as sex:
        error = f'SystemExit({sex.code}) — use json_output path without ci_mode'
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=8)}'

    stdout = stdout_buf.getvalue()
    stderr = stderr_buf.getvalue()
    # Soft failures: plugin printed an error / returned report.error without raising
    if not error and isinstance(report, dict) and report.get('error'):
        error = str(report.get('error'))
    if not error and stderr:
        for line in stderr.splitlines():
            low = line.strip().lower()
            if low.startswith('error:') or 'no target specified' in low:
                error = line.strip()
                break

    # Mirror captured console to server log — skip when MCP owns stdout
    quiet = os.getenv('VIMANA_MCP') or os.getenv('VIMANA_QUIET_CONSOLE')
    if not quiet:
        if stdout:
            sys.stdout.write(stdout)
            if not stdout.endswith('\n'):
                sys.stdout.write('\n')
        if stderr:
            sys.stderr.write(stderr)
            if not stderr.endswith('\n'):
                sys.stderr.write('\n')

    arts = collect_artifacts(
        plugin=plugin,
        report=report if not error else report or None,
        args=args,
        stdout=stdout,
        stderr=stderr,
    )

    if error:
        RUN_STORE.mark_failed(
            run.run_id, error, stdout=stdout, stderr=stderr, artifacts=arts,
        )
    else:
        RUN_STORE.mark_succeeded(
            run.run_id, report, stdout=stdout, stderr=stderr, artifacts=arts,
        )

    result = RUN_STORE.get(run.run_id)
    return result or run


def _run_plugin_worker(plugin: str, args: Dict[str, Any], run_id: str) -> None:
    try:
        run_plugin(plugin, args, async_job=False, run_id=run_id)
    except Exception as exc:
        RUN_STORE.mark_failed(run_id, f'{type(exc).__name__}: {exc}')


def _run_via_siddhi_start(plugin: str, handler: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call leaf siddhi.start() directly so structured return values are preserved
    (VFManager.run_siddhi discards them).
    """
    h = dict(handler)
    h['module_run'] = plugin
    h['module'] = plugin
    h['runner_mode'] = True

    rows = VFDBOps().getall('_SIDDHIS_') or []
    row = next((r for r in rows if getattr(r, 'name', None) == plugin), None)
    if not row or not getattr(row, 'module', None):
        raise RuntimeError(f'plugin module path not found in DB: {plugin}')

    module_path = str(row.module).replace('/', '.').replace('\\', '.')
    if module_path.endswith('.py'):
        module_path = module_path[:-3]

    try:
        _siddhi_ = __import__(module_path, globals(), 'siddhi', 1).siddhi
    except Exception as exc:
        raise RuntimeError(f'import failed for {module_path}: {exc}') from exc

    try:
        result = _siddhi_(**h).start()
    except SystemExit as sex:
        # Many CLI siddhis call sys.exit(0) on success — treat as completed under Control.
        code = sex.code
        if code in (0, None):
            return {
                'plugin': plugin,
                'summary': {'passed': True, 'note': 'siddhi.start exited 0'},
                'exit_code': 0,
            }
        raise RuntimeError(f'siddhi.start SystemExit({code})') from sex

    if isinstance(result, dict):
        return result
    return {
        'plugin': plugin,
        'summary': {'passed': True, 'note': 'siddhi.start completed'},
        'result': result,
    }


@with_flask_db
def lab_status(plugin: str) -> Dict[str, Any]:
    mgr = VimanaLabManager()
    lab_path = mgr._get_plugin_lab_path(plugin)
    valid, missing = mgr._validate_lab_structure(plugin)
    meta = get_lab_meta(plugin) or {}

    # No lab dir / incomplete structure — skip compose/port probes (avoids noisy warnings)
    if not valid:
        return {
            'plugin': plugin,
            'lab_path': lab_path,
            'valid': False,
            'missing_files': missing,
            'running': False,
            'ports': [],
            'url': None,
            'meta': meta,
        }

    running = False
    try:
        running = bool(mgr._check_lab_health(plugin))
    except Exception:
        running = False
    ports = []
    url = None
    try:
        ports = mgr._get_lab_ports(plugin) or []
        port = mgr._get_lab_port(plugin)
        if port:
            url = f'http://localhost:{port}'
    except Exception:
        port = None

    return {
        'plugin': plugin,
        'lab_path': lab_path,
        'valid': valid,
        'missing_files': missing,
        'running': running,
        'ports': ports,
        'url': url,
        'meta': meta,
    }


@with_flask_db
def list_labs() -> List[Dict[str, Any]]:
    """Status snapshot for every plugin that has a lab/ directory."""
    import os

    mgr = VimanaLabManager()
    rows = VFDBOps().getall('_SIDDHIS_') or []
    out: List[Dict[str, Any]] = []
    for row in rows:
        name = getattr(row, 'name', None)
        if not name:
            continue
        lab_path = mgr._get_plugin_lab_path(name)
        if not os.path.isdir(lab_path):
            continue
        out.append(lab_status(name))
    out.sort(key=lambda x: (not x.get('running'), x.get('plugin') or ''))
    return out


@with_flask_db
def lab_cleanup() -> Dict[str, Any]:
    """Stop all running labs (mirrors CLI --cleanup-labs)."""
    mgr = VimanaLabManager()
    before = []
    try:
        before = list(mgr._discover_running_labs())
    except Exception:
        before = []
    tracked = list(getattr(mgr, 'active_labs', {}) or {})
    names = sorted(set(before) | set(tracked))
    mgr.cleanup_labs()
    after = []
    try:
        after = list(mgr._discover_running_labs())
    except Exception:
        after = []
    return {
        'ok': len(after) == 0,
        'stopped': names,
        'still_running': after,
    }


@with_flask_db
def lab_start(plugin: str) -> Dict[str, Any]:
    mgr = VimanaLabManager()
    ok = mgr.start_lab(plugin)
    status = lab_status(plugin)
    # Compose/health can lag a beat after start_lab's own wait — poll briefly
    # so Control / agent callers see running=true before the next tool.
    if ok and not status.get('running'):
        import time
        for _ in range(12):
            time.sleep(0.5)
            status = lab_status(plugin)
            if status.get('running'):
                break
    status['ok'] = bool(ok and status.get('running'))
    return status


@with_flask_db
def lab_stop(plugin: str) -> Dict[str, Any]:
    mgr = VimanaLabManager()
    ok = mgr.stop_lab(plugin)
    status = lab_status(plugin)
    status['ok'] = ok
    return status


@with_flask_db
def lab_test(plugin: str) -> Dict[str, Any]:
    """
    Start lab (if needed) and run the plugin via composition.lab.run_hint.
    Mirrors: vimana run --lab <plugin> --test
    """
    import os

    mgr = VimanaLabManager()
    # Surface port conflicts before compose (same check start_lab uses).
    try:
        ports = mgr._get_lab_ports(plugin)
        conflicts = mgr._port_conflicts(ports) if hasattr(mgr, '_port_conflicts') else []
    except Exception:
        conflicts = []
    started = mgr.start_lab(plugin)
    status = lab_status(plugin)
    if not status.get('running'):
        status['ok'] = False
        status['started'] = started
        if conflicts:
            status['error'] = (
                'lab failed to start: host port(s) already in use — '
                + '; '.join(h for _, h in conflicts)
            )
            status['port_conflicts'] = [
                {'port': p, 'hint': h} for p, h in conflicts
            ]
        else:
            status['error'] = 'lab is not running / failed to start'
        status['run'] = None
        return status

    url = status.get('url') or f"http://localhost:{status.get('ports', [None])[0]}"
    args = mgr.parse_run_hint_args(plugin, url)

    # Multi-service labs (e.g. framewalk): prefer targets.txt created by start_lab
    lab_path = mgr._get_plugin_lab_path(plugin)
    targets_file = os.path.join(lab_path, 'targets.txt') if lab_path else ''
    if (
        plugin in getattr(mgr, 'multi_service_labs', {})
        and targets_file
        and os.path.isfile(targets_file)
    ):
        args = dict(args)
        args['file_scope'] = targets_file
        args.pop('target_url', None)
        args.setdefault('json_output', True)
        args.setdefault('no_channels', True)

    run = run_plugin(plugin, args)
    status['ok'] = _run_ok(run)
    status['started'] = started
    status['run'] = run.to_dict(include_report=True) if run else None
    status['hint'] = mgr._format_run_hint(plugin, url)
    if run and not status['ok']:
        status['error'] = (
            run.error
            or (isinstance(run.report, dict) and run.report.get('error'))
            or (run.stderr or '').strip().splitlines()[-1:][0] if run.stderr else None
        )
    return status


def _run_ok(run: Any) -> bool:
    if not run or getattr(run, 'status', None) != 'succeeded':
        return False
    if getattr(run, 'error', None):
        return False
    report = getattr(run, 'report', None) or {}
    if isinstance(report, dict) and report.get('error'):
        return False
    stderr = (getattr(run, 'stderr', None) or '').lower()
    if 'error: no target' in stderr or 'no target specified' in stderr:
        return False
    return True


def _plugin_has_runnable_lab(plugin: str, detail: Optional[Dict[str, Any]] = None) -> bool:
    """True when YAML/capabilities declare a lab OR a lab directory is valid."""
    if detail and detail.get('has_lab'):
        return True
    try:
        status = lab_status(plugin)
        return bool(status.get('valid'))
    except Exception:
        return False


@with_flask_db
def run_plugin_playbook(plugin: str, *, stop_lab_after: bool = True) -> Dict[str, Any]:
    """
    One-shot \"run this plugin\" path for agents / NL.

    - Plugin with a lab (metadata OR lab dir) → lab_test (--lab X --test)
    - Plugin without a lab → sync run_plugin with empty specialty args
    - stop_lab_after (default True): stop lab after a lab-backed run so
      casual agentic use does not accumulate Docker labs
    """
    detail = get_plugin(plugin)
    if not detail:
        return {
            'ok': False,
            'plugin': plugin,
            'mode': None,
            'error': f'plugin not found: {plugin}',
            'run': None,
        }

    if _plugin_has_runnable_lab(plugin, detail):
        result = lab_test(plugin)
        result['plugin'] = plugin
        result['mode'] = 'lab_test'
        result['has_lab'] = True
        result['lab_stopped'] = False
        # Only stop when the lab actually came up (or leftovers exist).
        # Avoid advertising lab_stopped=True after a failed start.
        if stop_lab_after and (result.get('running') or result.get('started')):
            stopped = lab_stop(plugin)
            result['lab_stopped'] = True
            result['lab_stop'] = stopped
            result['running'] = bool(stopped.get('running'))
        elif stop_lab_after:
            # Best-effort cleanup of partial compose state (Created containers).
            try:
                lab_stop(plugin)
            except Exception:
                pass
            result['lab_stopped'] = False
        return result

    run = run_plugin(plugin, {}, async_job=False)
    return {
        'ok': _run_ok(run),
        'plugin': plugin,
        'mode': 'direct',
        'has_lab': False,
        'run': run.to_dict(include_report=True) if run else None,
        'error': (
            (run.error if run else None)
            or (isinstance(run.report, dict) and run.report.get('error') if run else None)
            or ((run.stderr or '').strip() if run and run.stderr else None)
        ),
        'lab_stopped': False,
    }
