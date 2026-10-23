# -*- coding: utf-8 -*-
"""Collect run artifacts (console, structured report, exported files) for Control API / Admin UI."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4


_MAX_FILE_BYTES = 512_000  # ~512KB inline cap for UI inspection


def _guess_kind(path: str) -> str:
    lower = path.lower()
    if lower.endswith(('.json', '.jsonl')):
        return 'json'
    if lower.endswith(('.yaml', '.yml')):
        return 'yaml'
    if lower.endswith(('.html', '.htm')):
        return 'html'
    if lower.endswith(('.sarif',)):
        return 'json'
    return 'text'


def _read_file_artifact(path: str, label: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not path or not os.path.isfile(path):
        return None
    try:
        size = os.path.getsize(path)
        kind = _guess_kind(path)
        with open(path, 'r', encoding='utf-8', errors='replace') as handle:
            if size > _MAX_FILE_BYTES:
                content = handle.read(_MAX_FILE_BYTES)
                truncated = True
            else:
                content = handle.read()
                truncated = False
        # Pretty-print JSON when possible
        parsed = None
        if kind == 'json':
            try:
                parsed = json.loads(content)
                content = json.dumps(parsed, indent=2, default=str)
            except Exception:
                parsed = None
        return {
            'id': f'file-{uuid4().hex[:8]}',
            'kind': kind,
            'label': label or os.path.basename(path),
            'path': path,
            'content': content,
            'truncated': truncated,
            'size': size,
            'data': parsed,
        }
    except Exception:
        return None


def collect_artifacts(
    *,
    plugin: str,
    report: Optional[Dict[str, Any]],
    args: Optional[Dict[str, Any]],
    stdout: str = '',
    stderr: str = '',
) -> List[Dict[str, Any]]:
    """
    Build inspectable artifacts for a completed run.

    Always includes console output when present; includes structured report JSON
    when the report has meaningful keys; includes on-disk exports referenced by
    handler args / report fields.
    """
    artifacts: List[Dict[str, Any]] = []
    args = args or {}
    report = report if isinstance(report, dict) else {}

    if stdout and stdout.strip():
        artifacts.append({
            'id': 'console',
            'kind': 'console',
            'label': 'Console output',
            'content': stdout,
            'truncated': False,
        })
    if stderr and stderr.strip():
        artifacts.append({
            'id': 'stderr',
            'kind': 'console',
            'label': 'Stderr',
            'content': stderr,
            'truncated': False,
        })

    # Structured report worth inspecting (skip empty VFManager stubs)
    meaningful = any(
        report.get(k) not in (None, False, '', [], {})
        for k in (
            'findings', 'summary', 'frameworks', 'targets', 'candidates',
            'components', 'result', 'framework_counts',
        )
    )
    if meaningful:
        artifacts.append({
            'id': 'report',
            'kind': 'json',
            'label': f'{plugin} report',
            'content': json.dumps(report, indent=2, default=str),
            'data': report,
            'truncated': False,
        })

    # File paths from args / report
    path_candidates = []
    for key in (
        'output', 'output_file', 'scan_output_file', 'json_output_file',
        'report_file', 'sarif', 'sarif_file',
    ):
        val = args.get(key) or report.get(key)
        if isinstance(val, str) and val and not val.startswith('{'):
            path_candidates.append((val, key))
    # Nested common shapes
    for nested_key in ('artifacts', 'exports', 'files'):
        nested = report.get(nested_key)
        if isinstance(nested, list):
            for item in nested:
                if isinstance(item, str):
                    path_candidates.append((item, nested_key))
                elif isinstance(item, dict) and item.get('path'):
                    path_candidates.append((item['path'], item.get('label') or nested_key))

    seen_paths = set()
    for path, label in path_candidates:
        ap = os.path.abspath(path)
        if ap in seen_paths:
            continue
        seen_paths.add(ap)
        art = _read_file_artifact(path, label=f'Export · {label}')
        if art:
            artifacts.append(art)

    return artifacts
