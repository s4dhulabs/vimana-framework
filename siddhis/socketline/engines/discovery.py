# -*- coding: utf-8 -*-
# WebSocket endpoint discovery for socketline.

import re
from typing import Dict, List, Set
from urllib.parse import urljoin

from siddhis.socketline.utils import join_ws_url

WS_PATH_WORDLIST = (
    '/ws',
    '/websocket',
    '/socket',
    '/live',
    '/chat',
    '/stream',
    '/stream/ws',
    '/api/ws',
    '/api/websocket',
    '/v1/ws',
    '/realtime',
    '/notifications',
    '/events/ws',
)

WS_HINT_RE = re.compile(r'websocket|ws://|wss://|socket\.io', re.I)


def discover_from_openapi(api_specs: dict, base_url: str) -> List[Dict[str, str]]:
    """Extract WebSocket hints from OpenAPI paths and descriptions."""
    found: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for path, operations in api_specs.get('paths', {}).items():
        if not isinstance(operations, dict):
            continue

        hints = [path]
        for op in operations.values():
            if not isinstance(op, dict):
                continue
            for field in ('summary', 'description', 'operationId'):
                value = op.get(field)
                if value:
                    hints.append(str(value))

        blob = ' '.join(hints).lower()
        if 'websocket' in blob or path.startswith('/ws'):
            if path not in seen:
                seen.add(path)
                found.append({
                    'path': path,
                    'source': 'openapi',
                    'url': join_ws_url(base_url, path),
                })

    return found


def discover_from_wordlist(base_url: str, extra_paths: List[str] = None) -> List[Dict[str, str]]:
    paths = list(WS_PATH_WORDLIST)
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
            'url': join_ws_url(base_url, path),
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


def resolve_targets(handler: dict, api_specs: dict, base_url: str) -> List[Dict[str, str]]:
    explicit = handler.get('ws_path')
    if explicit:
        paths = explicit if isinstance(explicit, list) else [explicit]
        return [{
            'path': path if path.startswith('/') else f'/{path}',
            'source': 'cli',
            'url': join_ws_url(base_url, path),
        } for path in paths]

    openapi_hits = discover_from_openapi(api_specs, base_url) if api_specs else []
    wordlist_hits = discover_from_wordlist(base_url)
    return merge_candidates(openapi_hits, wordlist_hits)
