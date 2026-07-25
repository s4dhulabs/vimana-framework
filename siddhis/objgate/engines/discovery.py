# -*- coding: utf-8 -*-
# REST object path discovery for objgate (HTTP BOLA targets).

import re
from typing import Dict, List, Set

from siddhis.objgate.utils import join_url, render_obj_path

OBJ_PATH_WORDLIST = (
    '/api/orders/{id}',
    '/api/secure/orders/{id}',
    '/api/users/{id}',
    '/api/accounts/{id}',
    '/api/invoices/{id}',
    '/api/v1/orders/{id}',
)

OBJ_HINT_RE = re.compile(
    r'order|invoice|account|user|customer|resource|object|record',
    re.I,
)


def _looks_like_obj_path(path: str, blob: str) -> bool:
    if '{id}' in path or '{pk}' in path or '{obj_id}' in path:
        return True
    if OBJ_HINT_RE.search(path) or OBJ_HINT_RE.search(blob):
        return True
    return False


def resolve_obj_pair(handler: dict) -> tuple:
    obj_a = handler.get('obj_id_a') or handler.get('obj_id') or '1'
    obj_b = handler.get('obj_id_b') or '2'
    if str(obj_a) == str(obj_b):
        obj_b = f'{obj_a}-alt'
    return str(obj_a), str(obj_b)


def resolve_templates(handler: dict, api_specs: dict) -> List[str]:
    explicit = handler.get('obj_path')
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
        if _looks_like_obj_path(path, ' '.join(hints)) and path not in seen:
            seen.add(path)
            templates.append(path)

    if not templates:
        templates = list(OBJ_PATH_WORDLIST)
    return templates


def build_targets(templates: List[str], base_url: str, obj_a: str, obj_b: str) -> List[Dict[str, str]]:
    targets = []
    for template in templates:
        targets.append({
            'template': template,
            'obj_a': obj_a,
            'obj_b': obj_b,
            'url_a': join_url(base_url, render_obj_path(template, obj_a)),
            'url_b': join_url(base_url, render_obj_path(template, obj_b)),
            'source': 'cli' if True else 'discovery',
        })
    return targets
