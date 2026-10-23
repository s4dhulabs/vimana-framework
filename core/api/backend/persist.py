# -*- coding: utf-8 -*-
"""Disk persistence for Exception Monitor (Fase 3.1).

Stores exceptions / environments under ~/.vimana/monitor/ so restarts
do not wipe the in-memory dashboard state.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_MAX_EXCEPTIONS = 2000


def monitor_dir() -> Path:
    root = Path(os.path.expanduser(os.getenv('VIMANA_HOME') or '~/.vimana'))
    path = root / 'monitor'
    path.mkdir(parents=True, exist_ok=True)
    return path


def exceptions_path() -> Path:
    return monitor_dir() / 'exceptions.jsonl'


def environments_path() -> Path:
    return monitor_dir() / 'environments.json'


def append_exception(record: Dict[str, Any]) -> None:
    path = exceptions_path()
    with path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(record, default=str, ensure_ascii=False) + '\n')


def load_exceptions(limit: int = DEFAULT_MAX_EXCEPTIONS) -> List[Dict[str, Any]]:
    path = exceptions_path()
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open('r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    if limit and len(rows) > limit:
        rows = rows[-limit:]
    return rows


def save_environments(store: Dict[str, Any]) -> None:
    path = environments_path()
    tmp = path.with_suffix('.tmp')
    try:
        tmp.write_text(
            json.dumps(store, default=str, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        tmp.replace(path)
    except OSError:
        pass


def load_environments() -> Dict[str, Any]:
    path = environments_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}
