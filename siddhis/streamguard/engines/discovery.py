# -*- coding: utf-8 -*-
# Streaming endpoint discovery for streamguard.

import re
from typing import Dict, List, Set

from siddhis.streamguard.utils import join_http_url

STREAM_PATH_WORDLIST = (
    '/events',
    '/event',
    '/stream',
    '/sse',
    '/logs/stream',
    '/api/events',
    '/api/stream',
    '/v1/events',
    '/v1/stream',
    '/realtime/events',
    '/notifications/stream',
    '/live',
    '/feed',
    '/chat/stream',
)

STREAM_HINT_RE = re.compile(
    r'event-stream|text/event-stream|ndjson|x-ndjson|streaming|chunked|sse',
    re.I,
)

STREAM_CONTENT_TYPES = {
    'sse': {'text/event-stream'},
    'ndjson': {'application/x-ndjson', 'application/ndjson', 'application/jsonlines'},
    'chunked': set(),
    'auto': set(),
}


def _infer_stream_type(path: str, hints: str) -> str:
    blob = f'{path} {hints}'.lower()
    if 'ndjson' in blob or 'jsonlines' in blob or '/logs/' in path:
        return 'ndjson'
    if 'event-stream' in blob or 'sse' in blob or '/events' in path:
        return 'sse'
    return 'chunked'


def discover_from_openapi(api_specs: dict, base_url: str) -> List[Dict[str, str]]:
    """Extract streaming endpoint hints from OpenAPI paths and response types."""
    found: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for path, operations in api_specs.get('paths', {}).items():
        if not isinstance(operations, dict):
            continue

        hints = [path]
        response_types: Set[str] = set()

        for op in operations.values():
            if not isinstance(op, dict):
                continue
            for field in ('summary', 'description', 'operationId'):
                value = op.get(field)
                if value:
                    hints.append(str(value))

            for response in op.get('responses', {}).values():
                if not isinstance(response, dict):
                    continue
                content = response.get('content', {})
                if isinstance(content, dict):
                    response_types.update(content.keys())

        blob = ' '.join(hints + list(response_types))
        if STREAM_HINT_RE.search(blob) or any(
            ct in blob for ct in ('text/event-stream', 'application/x-ndjson')
        ):
            if path not in seen:
                seen.add(path)
                found.append({
                    'path': path,
                    'source': 'openapi',
                    'url': join_http_url(base_url, path),
                    'stream_type': _infer_stream_type(path, blob),
                })

    return found


def discover_from_wordlist(base_url: str, extra_paths: List[str] = None) -> List[Dict[str, str]]:
    paths = list(STREAM_PATH_WORDLIST)
    if extra_paths:
        paths.extend(extra_paths)

    found = []
    seen = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        found.append({
            'path': path,
            'source': 'wordlist',
            'url': join_http_url(base_url, path),
            'stream_type': _infer_stream_type(path, path),
        })
    return found


def merge_candidates(*groups: List[Dict[str, str]]) -> List[Dict[str, str]]:
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            key = item['url']
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def _matches_stream_type(candidate: Dict[str, str], stream_type: str) -> bool:
    if stream_type in (None, False, 'auto'):
        return True
    return candidate.get('stream_type') == stream_type


def resolve_targets(handler: dict, api_specs: dict, base_url: str) -> List[Dict[str, str]]:
    explicit = handler.get('stream_path')
    stream_type = handler.get('stream_type') or 'auto'

    if explicit:
        paths = explicit if isinstance(explicit, list) else [explicit]
        candidates = [{
            'path': path if path.startswith('/') else f'/{path}',
            'source': 'cli',
            'url': join_http_url(base_url, path),
            'stream_type': _infer_stream_type(path, path),
        } for path in paths]
        return [c for c in candidates if _matches_stream_type(c, stream_type)]

    openapi_hits = discover_from_openapi(api_specs, base_url) if api_specs else []
    wordlist_hits = discover_from_wordlist(base_url)
    merged = merge_candidates(openapi_hits, wordlist_hits)
    return [c for c in merged if _matches_stream_type(c, stream_type)]


def build_crlf_probe_url(base_url: str, path: str) -> str:
    """Build URL with CRLF injection probe in query string."""
    return join_http_url(base_url, path) + '?q=probe%0d%0aevent:%20injected%0d%0adata:%20streamguard'
