# -*- coding: utf-8 -*-
"""Run store for Control API — memory + light disk persistence."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _runs_dir() -> Path:
    root = Path(os.path.expanduser('~/.vimana/control/runs'))
    root.mkdir(parents=True, exist_ok=True)
    return root


@dataclass
class RunRecord:
    run_id: str
    plugin: str
    status: str  # queued | running | succeeded | failed
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    stdout: str = ''
    stderr: str = ''
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    async_job: bool = False

    def to_dict(self, include_report: bool = True) -> Dict[str, Any]:
        data = {
            'run_id': self.run_id,
            'plugin': self.plugin,
            'status': self.status,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'args': self.args,
            'error': self.error,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'async': self.async_job,
            'artifacts': [
                {
                    'id': a.get('id'),
                    'kind': a.get('kind'),
                    'label': a.get('label'),
                    'path': a.get('path'),
                    'truncated': a.get('truncated'),
                    'size': a.get('size'),
                }
                for a in (self.artifacts or [])
            ],
        }
        if include_report:
            data['report'] = self.report
            data['artifacts_detail'] = self.artifacts
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RunRecord':
        return cls(
            run_id=data['run_id'],
            plugin=data.get('plugin') or '',
            status=data.get('status') or 'queued',
            created_at=data.get('created_at') or _utc_now(),
            started_at=data.get('started_at'),
            finished_at=data.get('finished_at'),
            args=dict(data.get('args') or {}),
            report=data.get('report'),
            error=data.get('error'),
            stdout=data.get('stdout') or '',
            stderr=data.get('stderr') or '',
            artifacts=list(data.get('artifacts_detail') or data.get('artifacts') or []),
            async_job=bool(data.get('async')),
        )


class RunStore:
    def __init__(self, persist: bool = True) -> None:
        self._lock = Lock()
        self._runs: Dict[str, RunRecord] = {}
        self._persist = persist
        if persist:
            self._load_from_disk()

    def _path(self, run_id: str) -> Path:
        return _runs_dir() / f'{run_id}.json'

    def _persist_run(self, run: RunRecord) -> None:
        if not self._persist:
            return
        try:
            path = self._path(run.run_id)
            # Cap stdout/stderr on disk to keep files manageable
            payload = run.to_dict(include_report=True)
            for key in ('stdout', 'stderr'):
                text = payload.get(key) or ''
                if len(text) > 200_000:
                    payload[key] = text[:200_000] + '\n…[truncated]'
            path.write_text(json.dumps(payload, default=str), encoding='utf-8')
        except OSError:
            pass

    def _load_from_disk(self) -> None:
        try:
            for path in sorted(_runs_dir().glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    data = json.loads(path.read_text(encoding='utf-8'))
                    run = RunRecord.from_dict(data)
                    # Mark interrupted async jobs
                    if run.status in ('queued', 'running'):
                        run.status = 'failed'
                        run.error = (run.error or '') + (
                            '\n[interrupted: Control API restarted while job was active]'
                        )
                        run.finished_at = run.finished_at or _utc_now()
                    self._runs[run.run_id] = run
                except (OSError, json.JSONDecodeError, KeyError, TypeError):
                    continue
                if len(self._runs) >= 200:
                    break
        except OSError:
            pass

    def create(
        self,
        plugin: str,
        args: Optional[Dict[str, Any]] = None,
        *,
        async_job: bool = False,
    ) -> RunRecord:
        run = RunRecord(
            run_id=str(uuid4()),
            plugin=plugin,
            status='queued',
            created_at=_utc_now(),
            args=dict(args or {}),
            async_job=async_job,
        )
        with self._lock:
            self._runs[run.run_id] = run
            self._persist_run(run)
        return run

    def get(self, run_id: str) -> Optional[RunRecord]:
        with self._lock:
            run = self._runs.get(run_id)
            if run:
                return run
        # Disk fallback (another process / cold)
        if self._persist:
            path = self._path(run_id)
            if path.is_file():
                try:
                    run = RunRecord.from_dict(json.loads(path.read_text(encoding='utf-8')))
                    with self._lock:
                        self._runs[run.run_id] = run
                    return run
                except (OSError, json.JSONDecodeError, KeyError, TypeError):
                    return None
        return None

    def list(self, limit: int = 50) -> List[RunRecord]:
        with self._lock:
            runs = sorted(
                self._runs.values(),
                key=lambda r: r.created_at,
                reverse=True,
            )
            return runs[: max(1, min(limit, 200))]

    def mark_running(self, run_id: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            run.status = 'running'
            run.started_at = _utc_now()
            self._persist_run(run)

    def mark_succeeded(
        self,
        run_id: str,
        report: Dict[str, Any],
        *,
        stdout: str = '',
        stderr: str = '',
        artifacts: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            run.status = 'succeeded'
            run.finished_at = _utc_now()
            run.report = report
            run.stdout = stdout or ''
            run.stderr = stderr or ''
            run.artifacts = list(artifacts or [])
            self._persist_run(run)

    def mark_failed(
        self,
        run_id: str,
        error: str,
        *,
        stdout: str = '',
        stderr: str = '',
        artifacts: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            run.status = 'failed'
            run.finished_at = _utc_now()
            run.error = error
            run.stdout = stdout or ''
            run.stderr = stderr or ''
            run.artifacts = list(artifacts or [])
            self._persist_run(run)


# Process-wide store (single Control API process)
RUN_STORE = RunStore(persist=True)
