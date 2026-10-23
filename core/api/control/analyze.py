# -*- coding: utf-8 -*-
"""
Target analysis playbook for Control / native agent.

Flow (remote URL — not lab):
  1. fingerprint via framewalk (+ optional sttinger later)
  2. extract detected frameworks from the report
  3. triage catalog plugins that match framework / category
  4. optional follow-up audits (off by default)

Uses vimana_run_plugin semantics (target_url), never vimana_run / lab --test.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

ProgressCb = Callable[[str, str, Dict[str, Any]], None]

_SKIP_CATEGORIES_DEFAULT = frozenset({'fuzzer'})

# Secondary framework detections below this are noise for triage.
_MIN_TRIAGE_CONFIDENCE = 50.0
# When primary is this strong, ignore unrelated secondary frameworks.
_PRIMARY_DOMINANT_CONFIDENCE = 70.0

# Closely related stacks (FastAPI sits on Starlette).
_RELATED_FRAMEWORKS = {
    'fastapi': frozenset({'starlette'}),
    'starlette': frozenset({'fastapi'}),
}

# Deterministic run order after fingerprint (auto / follow-up).
# Plugins not listed still append afterward (stable alpha), except skipped categories.
FRAMEWORK_RUN_ORDER: Dict[str, List[str]] = {
    'fastapi': [
        'jcolt',       # pydantic / serialization / fuzzspec suite
        'fff',
        'pyserial',    # only when OpenAPI context exists
        'boundr',
        'socketline',
        'streamguard',
        'framewire',
        'roomgate',
        'wso',
    ],
    'starlette': [
        'jcolt', 'fff', 'pyserial', 'boundr', 'socketline', 'streamguard',
        'framewire', 'roomgate', 'wso',
    ],
    'django': [
        'sttinger',    # django fingerprint / version
        'dmt',
        'd4m8',
        'jungle',
        'objgate',
        'viewscan',
        'tictrac',
        'djunch',
    ],
    'flask': [
        'fetchbane',
        'flame',
        'atlatl',
    ],
}

# Plugins that only join the queue when context is present.
_CONDITIONAL_PLUGINS: Dict[str, str] = {
    'pyserial': 'openapi',
}

# Specialty flags for auto / follow-up runs (api_scan_enabled True → target URL).
# jcolt: scan API then pydantic tests (start() continues when pydantic_test set).
# pyserial: prefers spec from ~/.jcolt_env after jcolt scan in the same --auto queue.
_FOLLOW_UP_ARGS: Dict[str, Dict[str, Any]] = {
    'jcolt': {
        'pydantic_test': True,
        'api_scan_enabled': True,
    },
    'fff': {'api_scan_enabled': True},
    'pyserial': {
        'serialization_test': True,
        # target_url alone is enough; ENV_FALLBACK_SPEC_ID from prior jcolt scan is preferred
    },
    'boundr': {'upload_audit_enabled': True, 'api_scan_enabled': True},
    'objgate': {'obj_audit_enabled': True, 'api_scan_enabled': True},
    'fetchbane': {'ssrf_audit_enabled': True, 'api_scan_enabled': True},
    'socketline': {'api_scan_enabled': True},
    'streamguard': {'api_scan_enabled': True},
    'sttinger': {},
    'dmt': {},
    'd4m8': {},
}


def _noop_progress(stage: str, detail: str, extra: Dict[str, Any]) -> None:
    return None


def normalize_target_url(url: str) -> str:
    raw = (url or '').strip()
    if not raw:
        raise ValueError('empty target URL')
    parsed = urlparse(raw)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValueError(f'need http(s) URL with host, got {url!r}')
    return raw.rstrip('/')


def _norm_fw(name: Any) -> str:
    return str(name or '').strip().lower().replace(' ', '')


def _confidence_num(value: Any) -> float:
    if value is None:
        return -1.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().rstrip('%')
    try:
        return float(text)
    except ValueError:
        return -1.0


def extract_frameworks(report: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize framewalk-style report.frameworks into triage rows."""
    if not isinstance(report, dict):
        return []
    rows = report.get('frameworks')
    if not isinstance(rows, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        name = item.get('name') or item.get('framework')
        if not name:
            continue
        out.append({
            'name': str(name),
            'normalized': _norm_fw(name),
            'confidence': item.get('confidence'),
            'score': item.get('score'),
            'version': item.get('version'),
            'components': item.get('components') or [],
        })
    out.sort(
        key=lambda r: (
            -_confidence_num(r.get('confidence')),
            -(float(r['score']) if r.get('score') is not None else -1.0),
        )
    )
    return out


def frameworks_for_triage(
    frameworks: List[Dict[str, Any]],
    *,
    min_confidence: float = _MIN_TRIAGE_CONFIDENCE,
    primary_dominant: float = _PRIMARY_DOMINANT_CONFIDENCE,
) -> List[str]:
    """
    Which framework names should drive plugin matching.

    High-confidence primary → primary (+ related stacks only).
    Otherwise keep secondaries at/above min_confidence.
    """
    if not frameworks:
        return ['python']
    primary = frameworks[0]
    primary_name = primary.get('normalized') or 'python'
    primary_conf = _confidence_num(primary.get('confidence'))
    related = set(_RELATED_FRAMEWORKS.get(primary_name, ()))

    if primary_conf >= primary_dominant:
        return [primary_name] + sorted(related)

    names: List[str] = []
    for fw in frameworks:
        n = fw.get('normalized')
        if not n:
            continue
        conf = _confidence_num(fw.get('confidence'))
        if n == primary_name or conf >= min_confidence or n in related:
            if n not in names:
                names.append(n)
    return names or [primary_name]


def has_openapi_context(
    report: Optional[Dict[str, Any]],
    frameworks: Optional[List[Dict[str, Any]]] = None,
) -> bool:
    """True when fingerprint evidence suggests OpenAPI / Swagger surface."""
    frameworks = frameworks or extract_frameworks(report)
    for fw in frameworks:
        if fw.get('normalized') == 'fastapi' and _confidence_num(fw.get('confidence')) >= 50:
            return True
        for comp in fw.get('components') or []:
            blob = str(comp).lower()
            if any(k in blob for k in ('openapi', 'swagger', 'redoc')):
                return True
    if not isinstance(report, dict):
        return False
    blob = str(report).lower()
    return any(
        k in blob
        for k in ('openapi.json', 'swagger', '/docs', 'redoc', 'openapi')
    )


def _plugin_run_args(plugin: str, target_url: str) -> Dict[str, Any]:
    args: Dict[str, Any] = {
        'target_url': target_url,
        'json_output': True,
        'no_channels': True,
        'summary_only': True,
    }
    for key, val in (_FOLLOW_UP_ARGS.get(plugin.lower()) or {}).items():
        if key == 'api_scan_enabled' and val is True:
            args[key] = target_url
        else:
            args[key] = val
    return args


def triage_candidates(
    frameworks: List[Dict[str, Any]],
    *,
    catalog: List[Dict[str, Any]],
    fingerprint_plugin: str = 'framewalk',
    include_fuzzers: bool = False,
    report: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Build an ordered candidate list for the detected stack.

    Order is deterministic via FRAMEWORK_RUN_ORDER (jcolt→fff→… for FastAPI;
    sttinger→dmt→d4m8→… for Django). Remaining matching plugins append after.
    """
    detected = frameworks_for_triage(frameworks)
    primary = detected[0]
    skip_cats = set() if include_fuzzers else set(_SKIP_CATEGORIES_DEFAULT)
    by_name = {
        str(p.get('name') or '').strip().lower(): p
        for p in catalog
        if p.get('name')
    }
    openapi = has_openapi_context(report, frameworks)
    playbook = list(FRAMEWORK_RUN_ORDER.get(primary) or [])

    playbook_l = [n.lower() for n in playbook]

    def _eligible(plug: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        name = str(plug.get('name') or '').strip()
        if not name or name.lower() == fingerprint_plugin.lower():
            return None
        lname = name.lower()
        in_playbook = lname in playbook_l
        cat = str(plug.get('category') or '').strip().lower()
        # Playbook entries win over fuzzer skip (django → d4m8).
        if cat in skip_cats and not in_playbook:
            return None
        fw = _norm_fw(plug.get('framework'))
        if not in_playbook:
            # Same / related stack only — no python-generic noise after a clear primary.
            if fw == primary or fw in detected:
                pass
            else:
                return None
        cond = _CONDITIONAL_PLUGINS.get(lname)
        if cond == 'openapi' and not openapi:
            return None
        if in_playbook:
            order_idx = playbook_l.index(lname)
            rank = order_idx
            reason = f'playbook#{order_idx + 1} ({primary})'
        else:
            rank = 1000
            reason = f'framework match ({fw or primary})'
        if cond == 'openapi':
            reason = f'{reason}; openapi context'
        return {
            'name': name,
            'framework': plug.get('framework'),
            'category': plug.get('category'),
            'type': plug.get('type'),
            'info': plug.get('info') or plug.get('brief') or '',
            'has_lab': bool(plug.get('has_lab')),
            'rank': rank,
            'score': max(0, 200 - rank),
            'reason': reason,
            'suggested_args': {
                'target_url': True,
                **dict(_FOLLOW_UP_ARGS.get(lname) or {}),
            },
        }

    ordered: List[Dict[str, Any]] = []
    seen: set = set()

    for pname in playbook:
        plug = by_name.get(pname.lower())
        if not plug:
            continue
        row = _eligible(plug)
        if not row:
            continue
        ordered.append(row)
        seen.add(row['name'].lower())

    extras: List[Dict[str, Any]] = []
    for plug in catalog:
        name = str(plug.get('name') or '').strip()
        if not name or name.lower() in seen:
            continue
        row = _eligible(plug)
        if not row:
            continue
        extras.append(row)
        seen.add(row['name'].lower())

    extras.sort(key=lambda r: (int(r['rank']), str(r['name'])))
    ordered.extend(extras)
    if limit is not None:
        return ordered[: max(0, int(limit))]
    return ordered


def _catalog_for_triage() -> List[Dict[str, Any]]:
    from core.api.control import services

    out: List[Dict[str, Any]] = []
    for row in services.list_plugins():
        name = row.get('name')
        if not name:
            continue
        detail = services.get_plugin(str(name)) or {}
        out.append({
            'name': name,
            'category': row.get('category') or detail.get('category'),
            'type': row.get('type') or detail.get('type'),
            'framework': detail.get('framework'),
            'info': row.get('info') or detail.get('info'),
            'brief': detail.get('brief'),
            'has_lab': row.get('has_lab'),
        })
    return out


def analyze_target(
    target_url: str,
    *,
    fingerprint_plugin: str = 'framewalk',
    follow_up: bool = False,
    follow_up_limit: int = 2,
    include_fuzzers: bool = False,
    auto: bool = False,
    on_progress: Optional[ProgressCb] = None,
    run_plugin_fn: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    """
    Fingerprint a live target and recommend (optionally run) matching plugins.

    auto=True → run the full deterministic triage queue (same as follow_up
    over all candidates). run_plugin_fn: injectable for tests.
    """
    progress = on_progress or _noop_progress
    from core.api.control import services

    runner = run_plugin_fn or services.run_plugin
    url = normalize_target_url(target_url)
    if auto:
        follow_up = True
        include_fuzzers = True
        follow_up_limit = 0  # 0 = all candidates
    progress('parse', f'target={url} auto={bool(auto)}', {'target_url': url, 'auto': auto})

    # summary_only + quiet env: avoid Rich banners flooding the agent TTY
    # (run_plugin still captures stdout; QUIET stops re-mirroring).
    fp_args = {
        'target_url': url,
        'json_output': True,
        'no_channels': True,
        'summary_only': True,
        'timeout': 8,
        'min_confidence': 0,  # keep full report; triage filters confidence
    }
    progress(
        'fingerprint',
        f'running {fingerprint_plugin} (DAST fingerprint)',
        {'plugin': fingerprint_plugin, 'args': {'target_url': url}},
    )

    try:
        record = runner(fingerprint_plugin, fp_args, async_job=False)
    except LookupError as exc:
        progress('fingerprint', f'fail: {exc}', {'error': str(exc)})
        return {
            'ok': False,
            'target_url': url,
            'error': str(exc),
            'stage': 'fingerprint',
        }
    except Exception as exc:
        progress('fingerprint', f'fail: {type(exc).__name__}: {exc}', {'error': str(exc)})
        return {
            'ok': False,
            'target_url': url,
            'error': f'{type(exc).__name__}: {exc}',
            'stage': 'fingerprint',
        }

    run_dict = record.to_dict(include_report=True) if record else {}
    report = (record.report if record else None) or {}
    frameworks = extract_frameworks(report if isinstance(report, dict) else {})
    top = frameworks[0] if frameworks else None

    if record and record.status == 'failed':
        progress(
            'fingerprint',
            f'failed run_id={getattr(record, "run_id", None)} err={record.error}',
            {'run_id': getattr(record, 'run_id', None), 'error': record.error},
        )
    else:
        progress(
            'fingerprint',
            f'ok run_id={getattr(record, "run_id", None)} frameworks={len(frameworks)}',
            {
                'run_id': getattr(record, 'run_id', None),
                'status': getattr(record, 'status', None),
            },
        )

    if top:
        conf = top.get('confidence')
        ver = top.get('version') or '?'
        progress(
            'framework',
            f"{top.get('name')} confidence={conf} version={ver}",
            {'framework': top},
        )
    else:
        progress(
            'framework',
            'no framework detected — using python-generic triage',
            {},
        )

    primary_fw = (top or {}).get('normalized') or frameworks_for_triage(frameworks)[0]
    progress(
        'triage',
        f'playbook order for {top.get("name") if top else primary_fw}',
        {'playbook': FRAMEWORK_RUN_ORDER.get(primary_fw) or []},
    )
    catalog = _catalog_for_triage()
    candidates = triage_candidates(
        frameworks,
        catalog=catalog,
        fingerprint_plugin=fingerprint_plugin,
        include_fuzzers=include_fuzzers or auto,
        report=report if isinstance(report, dict) else None,
    )
    names = ', '.join(c['name'] for c in candidates) or '(none)'
    progress(
        'triage',
        f'{len(candidates)} candidate(s) [{primary_fw}]: {names}',
        {'count': len(candidates), 'order': [c['name'] for c in candidates]},
    )

    follow_ups: List[Dict[str, Any]] = []
    if follow_up and candidates:
        queue = (
            candidates
            if not follow_up_limit or follow_up_limit <= 0
            else candidates[: int(follow_up_limit)]
        )
        mode = 'auto' if auto else 'follow-up'
        progress(mode, f'running {len(queue)} plugin(s) in playbook order', {})
        for idx, cand in enumerate(queue, 1):
            pname = cand['name']
            args = _plugin_run_args(pname, url)
            progress(mode, f'[{idx}/{len(queue)}] {pname}', {'plugin': pname, 'args': {
                k: args[k] for k in args if k not in ('json_output', 'no_channels', 'summary_only')
            }})
            try:
                fr = runner(pname, args, async_job=False)
                follow_ups.append({
                    'name': pname,
                    'ok': bool(fr and fr.status == 'succeeded'),
                    'run_id': getattr(fr, 'run_id', None),
                    'status': getattr(fr, 'status', None),
                    'error': getattr(fr, 'error', None),
                    'rank': cand.get('rank'),
                })
                st = 'ok' if fr and fr.status == 'succeeded' else 'fail'
                progress(
                    mode,
                    f"[{idx}/{len(queue)}] {pname} → {getattr(fr, 'status', '?')} "
                    f"run_id={getattr(fr, 'run_id', None)}",
                    {'plugin': pname, 'status': st},
                )
            except Exception as exc:
                follow_ups.append({
                    'name': pname,
                    'ok': False,
                    'error': f'{type(exc).__name__}: {exc}',
                    'rank': cand.get('rank'),
                })
                progress(mode, f'[{idx}/{len(queue)}] {pname} fail: {exc}', {'error': str(exc)})
    else:
        progress(
            'recommend',
            'auto/follow-up skipped — use --auto or "with follow-up"',
            {},
        )

    ok = bool(record and record.status == 'succeeded')
    host = urlparse(url).hostname
    return {
        'ok': ok,
        'auto': bool(auto),
        'target_url': url,
        'fingerprint': {
            'plugin': fingerprint_plugin,
            'run_id': getattr(record, 'run_id', None) if record else None,
            'status': getattr(record, 'status', None) if record else None,
            'error': getattr(record, 'error', None) if record else None,
        },
        'frameworks': frameworks,
        'primary_framework': top,
        'playbook': FRAMEWORK_RUN_ORDER.get(primary_fw) or [],
        'candidates': candidates,
        'follow_ups': follow_ups,
        'next_steps': {
            'cli_examples': [
                (
                    f'vimana agent --policy run --allow-target {host} '
                    f'"run {c["name"]} against {url}"'
                )
                for c in candidates[:5]
            ],
            'agent_auto': (
                f'vimana agent --policy run --auto --allow-target {host} '
                f'"Analyze this target {url}"'
            ),
            'note': (
                'Default: fingerprint + ordered recommendations. '
                '`--auto` runs the full playbook queue (FastAPI: jcolt→fff→pyserial→…; '
                'Django: sttinger→dmt→d4m8→…). '
                'Remote hosts need --allow-target <host>.'
            ),
        },
        'fingerprint_run': {
            'run_id': run_dict.get('run_id'),
            'status': run_dict.get('status'),
            'report_summary': {
                'frameworks': len(frameworks),
                'target': (report or {}).get('target') or (report or {}).get('target_url'),
            } if isinstance(report, dict) else {},
        },
    }
