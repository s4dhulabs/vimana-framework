# -*- coding: utf-8 -*-
# WebSocket room/channel path discovery for roomgate (IDOR targets).

import re
from typing import Dict, List, Set

from siddhis.roomgate.utils import join_ws_url, render_room_path

ROOM_PATH_WORDLIST = (
    '/ws/room/{id}',
    '/ws/secure/{id}',
    '/ws/channel/{id}',
    '/ws/rooms/{id}',
    '/api/ws/room/{id}',
)

ROOM_HINT_RE = re.compile(r'room|channel|tenant|workspace|conversation', re.I)


def _looks_like_room_path(path: str, blob: str) -> bool:
    if '{room_id}' in path or '{id}' in path or ':room_id' in path:
        return True
    if ROOM_HINT_RE.search(path) or ROOM_HINT_RE.search(blob):
        return True
    return False


def discover_from_openapi(api_specs: dict, base_url: str, room_id: str) -> List[Dict[str, str]]:
    found: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for path, operations in (api_specs or {}).get('paths', {}).items():
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

        blob = ' '.join(hints)
        if not _looks_like_room_path(path, blob):
            continue

        concrete = render_room_path(path, room_id)
        if concrete in seen:
            continue
        seen.add(concrete)
        found.append({
            'path': concrete,
            'template': path,
            'source': 'openapi',
            'url': join_ws_url(base_url, concrete),
            'room_id': str(room_id),
        })

    return found


def discover_from_wordlist(base_url: str, room_id: str, extra: List[str] = None) -> List[Dict[str, str]]:
    templates = list(ROOM_PATH_WORDLIST)
    if extra:
        templates.extend(extra)

    found = []
    seen = set()
    for template in templates:
        concrete = render_room_path(template, room_id)
        if concrete in seen:
            continue
        seen.add(concrete)
        found.append({
            'path': concrete,
            'template': template,
            'source': 'wordlist',
            'url': join_ws_url(base_url, concrete),
            'room_id': str(room_id),
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


def resolve_room_pair(handler: dict) -> tuple:
    room_a = handler.get('room_id_a') or handler.get('room_id') or 'room-a'
    room_b = handler.get('room_id_b') or 'room-b'
    if room_a == room_b:
        room_b = f'{room_a}-alt'
    return str(room_a), str(room_b)


def resolve_templates(handler: dict, api_specs: dict, base_url: str) -> List[str]:
    """Return path templates (with placeholders) to audit."""
    explicit = handler.get('room_path') or handler.get('ws_path') or handler.get('frame_path')
    if explicit:
        paths = explicit if isinstance(explicit, list) else [explicit]
        return [p if p.startswith('/') else f'/{p}' for p in paths]

    templates: List[str] = []
    seen: Set[str] = set()
    for path, operations in (api_specs or {}).get('paths', {}).items():
        if not isinstance(operations, dict):
            continue
        hints = [path]
        for op in operations.values():
            if isinstance(op, dict):
                for field in ('summary', 'description', 'operationId'):
                    if op.get(field):
                        hints.append(str(op[field]))
        if _looks_like_room_path(path, ' '.join(hints)) and path not in seen:
            seen.add(path)
            templates.append(path)

    if not templates:
        templates = list(ROOM_PATH_WORDLIST)
    return templates
