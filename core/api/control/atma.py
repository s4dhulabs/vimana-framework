# -*- coding: utf-8 -*-
"""
Atma — dogfood the Control API with Vimana's own FastAPI-oriented plugins.

Zero-config self-scan: target is this process (localhost Control API).
Safety: localhost-only, sequential runs, per-plugin timeout, no fuzz/WS engines.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from core.api.control.mcp_connect import ATMA_MCP_CHECKS, run_all_mcp_checks

# Whitelist only — never auto-discover all FastAPI plugins (avoids fff/jcolt-fuzz/WS).
# Each entry uses light audit / recon flags only.
ATMA_SUITE: List[Dict[str, Any]] = [
    {
        'name': 'framewalk',
        'label': 'Fingerprint',
        'blurb': 'Identify stack / surface of this Control API',
        'timeout_sec': 45,
        'args': {
            'json_output': True,
            'no_channels': True,
            'timeout': 5,
            'summary_only': False,
        },
    },
    {
        'name': 'boundr',
        'label': 'Upload surface',
        'blurb': 'Probe multipart / UploadFile candidates via OpenAPI + wordlist',
        'timeout_sec': 60,
        'args': {
            'upload_audit_enabled': True,
            'json_output': True,
            'no_channels': True,
        },
    },
    {
        'name': 'objgate',
        'label': 'Object / IDOR',
        'blurb': 'Probe REST object endpoints for BOLA/IDOR-style issues',
        'timeout_sec': 60,
        'args': {
            'obj_audit_enabled': True,
            'json_output': True,
            'no_channels': True,
        },
    },
    {
        'name': 'fetchbane',
        'label': 'SSRF fetch',
        'blurb': 'Probe URL-fetch / webhook-style endpoints for SSRF',
        'timeout_sec': 60,
        'args': {
            'ssrf_audit_enabled': True,
            'json_output': True,
            'no_channels': True,
        },
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_safe_atma_target(url: str) -> str:
    """Atma may only target the local Control API (dogfood, not remote pentest)."""
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    if host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError(
            f'atma refuses non-local target {url!r} — only 127.0.0.1/localhost'
        )
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f'atma requires http(s) target, got {parsed.scheme!r}')
    return url.rstrip('/')


@dataclass
class AtmaPluginState:
    name: str
    label: str
    blurb: str = ''
    status: str = 'queued'  # queued | running | succeeded | failed | skipped | timeout
    run_id: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'label': self.label,
            'blurb': self.blurb,
            'status': self.status,
            'run_id': self.run_id,
            'error': self.error,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'summary': self.summary,
        }


@dataclass
class AtmaMcpState:
    """Non-destructive MCP protocol / tool checks (stdio NDJSON)."""
    id: str
    label: str
    blurb: str = ''
    status: str = 'queued'
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'label': self.label,
            'blurb': self.blurb,
            'status': self.status,
            'error': self.error,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'summary': self.summary,
        }


@dataclass
class AtmaJob:
    job_id: str
    target_url: str
    status: str = 'queued'  # queued | running | completed | failed
    created_at: str = field(default_factory=_utc_now)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    plugins: List[AtmaPluginState] = field(default_factory=list)
    mcp_checks: List[AtmaMcpState] = field(default_factory=list)
    note: str = (
        'Atma runs a curated, non-fuzz suite against this Control API (localhost), '
        'plus non-destructive MCP stdio checks. '
        'Not a substitute for a full assessment — dogfood of Vimana engines.'
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'target_url': self.target_url,
            'status': self.status,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'note': self.note,
            'plugins': [p.to_dict() for p in self.plugins],
            'mcp_checks': [c.to_dict() for c in self.mcp_checks],
        }


class AtmaStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, AtmaJob] = {}
        self._active_job_id: Optional[str] = None

    def get(self, job_id: str) -> Optional[AtmaJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def active(self) -> Optional[AtmaJob]:
        with self._lock:
            if self._active_job_id:
                return self._jobs.get(self._active_job_id)
            return None

    def create(self, target_url: str) -> AtmaJob:
        with self._lock:
            if self._active_job_id:
                current = self._jobs.get(self._active_job_id)
                if current and current.status in ('queued', 'running'):
                    raise RuntimeError(
                        f'atma already running (job {self._active_job_id}) — wait for it to finish'
                    )
            job = AtmaJob(
                job_id=str(uuid4()),
                target_url=target_url,
                plugins=[
                    AtmaPluginState(
                        name=p['name'],
                        label=p['label'],
                        blurb=p.get('blurb') or '',
                    )
                    for p in ATMA_SUITE
                ],
                mcp_checks=[
                    AtmaMcpState(
                        id=c['id'],
                        label=c['label'],
                        blurb=c.get('blurb') or '',
                    )
                    for c in ATMA_MCP_CHECKS
                ],
            )
            self._jobs[job.job_id] = job
            self._active_job_id = job.job_id
            return job

    def update_plugin(self, job_id: str, name: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for plug in job.plugins:
                if plug.name == name:
                    for k, v in fields.items():
                        setattr(plug, k, v)
                    break

    def update_mcp(self, job_id: str, check_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for chk in job.mcp_checks:
                if chk.id == check_id:
                    for k, v in fields.items():
                        setattr(chk, k, v)
                    break

    def set_job(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for k, v in fields.items():
                setattr(job, k, v)
            if fields.get('status') in ('completed', 'failed'):
                if self._active_job_id == job_id:
                    self._active_job_id = None


ATMA_STORE = AtmaStore()


def suite_manifest() -> Dict[str, Any]:
    return {
        'name': 'atma',
        'description': (
            'Zero-config dogfood: safe FastAPI-oriented plugin suite against this '
            'Control API (localhost), plus non-destructive MCP stdio checks.'
        ),
        'plugins': [
            {
                'name': p['name'],
                'label': p['label'],
                'blurb': p.get('blurb'),
                'timeout_sec': p['timeout_sec'],
            }
            for p in ATMA_SUITE
        ],
        'mcp_checks': [
            {
                'id': c['id'],
                'label': c['label'],
                'blurb': c.get('blurb'),
                'timeout_sec': c.get('timeout_sec'),
            }
            for c in ATMA_MCP_CHECKS
        ],
        'safety': {
            'localhost_only': True,
            'sequential': True,
            'fuzz_excluded': True,
            'websocket_excluded': True,
            'one_job_at_a_time': True,
            'per_plugin_timeout': True,
            'mcp_non_destructive': True,
            'mcp_no_lab_mutate': True,
            'mcp_no_plugin_run': True,
        },
    }


def start_atma(target_url: str) -> AtmaJob:
    target = assert_safe_atma_target(target_url)
    job = ATMA_STORE.create(target)
    thread = threading.Thread(
        target=_run_atma_job,
        args=(job.job_id,),
        name=f'atma-{job.job_id[:8]}',
        daemon=True,
    )
    thread.start()
    return job


def _run_atma_job(job_id: str) -> None:
    from core.api.control.services import run_plugin

    job = ATMA_STORE.get(job_id)
    if not job:
        return

    ATMA_STORE.set_job(job_id, status='running', started_at=_utc_now())

    by_name = {p['name']: p for p in ATMA_SUITE}

    for state in list(job.plugins):
        spec = by_name.get(state.name)
        if not spec:
            ATMA_STORE.update_plugin(
                job_id, state.name, status='skipped', error='not in suite',
                finished_at=_utc_now(),
            )
            continue

        ATMA_STORE.update_plugin(
            job_id, state.name, status='running', started_at=_utc_now(), error=None,
        )

        args = dict(spec.get('args') or {})
        args['target_url'] = job.target_url
        args.setdefault('json_output', True)
        args.setdefault('no_channels', True)
        # OpenAPI discovery against this API when the plugin understands --scan-api
        if 'api_scan_enabled' not in args:
            args['api_scan_enabled'] = job.target_url
        timeout = int(spec.get('timeout_sec') or 60)

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(run_plugin, state.name, args)
                try:
                    record = fut.result(timeout=timeout)
                except FuturesTimeout:
                    ATMA_STORE.update_plugin(
                        job_id,
                        state.name,
                        status='timeout',
                        error=f'exceeded {timeout}s — aborted to protect Control API',
                        finished_at=_utc_now(),
                    )
                    continue

            if not record:
                ATMA_STORE.update_plugin(
                    job_id, state.name, status='failed', error='no run record',
                    finished_at=_utc_now(),
                )
                continue

            summary = None
            if record.report and isinstance(record.report, dict):
                summary = record.report.get('summary')
                if summary is None and record.report.get('frameworks') is not None:
                    summary = {
                        'frameworks': len(record.report.get('frameworks') or []),
                    }

            ATMA_STORE.update_plugin(
                job_id,
                state.name,
                status=record.status if record.status in ('succeeded', 'failed') else 'succeeded',
                run_id=record.run_id,
                error=record.error,
                summary=summary if isinstance(summary, dict) else None,
                finished_at=_utc_now(),
            )
        except Exception as exc:
            ATMA_STORE.update_plugin(
                job_id,
                state.name,
                status='failed',
                error=f'{type(exc).__name__}: {exc}',
                finished_at=_utc_now(),
            )

        # Brief pause between plugins — reduce self-load
        time.sleep(0.4)

    # MCP checks after plugins — one stdio session, read-oriented tools only
    def _mcp_progress(check_id: str, partial: Dict[str, Any]) -> None:
        st = partial.get('status')
        if st == 'running':
            ATMA_STORE.update_mcp(
                job_id, check_id, status='running', started_at=_utc_now(), error=None,
            )
            return
        ATMA_STORE.update_mcp(
            job_id,
            check_id,
            status=partial.get('status') or 'failed',
            error=partial.get('error'),
            summary=partial.get('summary') if isinstance(partial.get('summary'), dict) else None,
            finished_at=_utc_now(),
        )

    # Mark all queued before starting batch
    for state in list(job.mcp_checks):
        ATMA_STORE.update_mcp(job_id, state.id, status='queued', error=None)

    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(run_all_mcp_checks, _mcp_progress)
            try:
                fut.result(timeout=sum(int(c.get('timeout_sec') or 20) for c in ATMA_MCP_CHECKS) + 30)
            except FuturesTimeout:
                for state in list(job.mcp_checks):
                    if state.status in ('queued', 'running'):
                        ATMA_STORE.update_mcp(
                            job_id, state.id, status='timeout',
                            error='MCP suite exceeded overall timeout',
                            finished_at=_utc_now(),
                        )
    except Exception as exc:
        for state in list(job.mcp_checks):
            if state.status in ('queued', 'running'):
                ATMA_STORE.update_mcp(
                    job_id, state.id, status='failed',
                    error=f'{type(exc).__name__}: {exc}',
                    finished_at=_utc_now(),
                )

    ATMA_STORE.set_job(job_id, status='completed', finished_at=_utc_now())
