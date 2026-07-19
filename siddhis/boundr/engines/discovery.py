# -*- coding: utf-8 -*-
# Multipart / upload endpoint discovery for boundr.

import re
from typing import Dict, List, Optional, Set

from siddhis.boundr.utils import join_http_url

UPLOAD_PATH_WORDLIST = (
    '/upload',
    '/uploads',
    '/api/upload',
    '/api/uploads',
    '/api/files',
    '/files',
    '/file',
    '/v1/upload',
    '/v1/files',
    '/media/upload',
    '/documents',
    '/attachments',
)

MULTIPART_HINT_RE = re.compile(
    r'multipart|uploadfile|upload|form-data|filename|file\b',
    re.I,
)


def _extract_file_field(op: dict) -> Optional[str]:
    """Best-effort file field name from OpenAPI requestBody / parameters."""
    body = op.get('requestBody') or {}
    content = body.get('content') or {}
    multipart = content.get('multipart/form-data') or {}
    schema = multipart.get('schema') or {}
    props = schema.get('properties') or {}
    for name, prop in props.items():
        if not isinstance(prop, dict):
            continue
        fmt = prop.get('format', '')
        ptype = prop.get('type', '')
        if fmt == 'binary' or (ptype == 'string' and 'file' in name.lower()):
            return name
        if prop.get('contentMediaType') or 'file' in str(prop).lower():
            return name
    for name in props:
        if 'file' in name.lower() or 'upload' in name.lower() or 'document' in name.lower():
            return name
    return 'file' if props else None


def discover_from_openapi(api_specs: dict, base_url: str) -> List[Dict[str, str]]:
    """Extract multipart/upload endpoints from OpenAPI."""
    found: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for path, operations in api_specs.get('paths', {}).items():
        if not isinstance(operations, dict):
            continue

        for method, op in operations.items():
            if method.lower() not in ('post', 'put', 'patch'):
                continue
            if not isinstance(op, dict):
                continue

            hints = [path, method]
            for field in ('summary', 'description', 'operationId'):
                value = op.get(field)
                if value:
                    hints.append(str(value))

            body = op.get('requestBody') or {}
            content = body.get('content') or {}
            has_multipart = 'multipart/form-data' in content
            blob = ' '.join(hints)

            if has_multipart or MULTIPART_HINT_RE.search(blob):
                key = f'{method.upper()} {path}'
                if key in seen:
                    continue
                seen.add(key)
                field_name = _extract_file_field(op) or 'file'
                found.append({
                    'path': path,
                    'method': method.upper(),
                    'field': field_name,
                    'source': 'openapi',
                    'url': join_http_url(base_url, path),
                })

    return found


def discover_from_wordlist(base_url: str, extra_paths: List[str] = None) -> List[Dict[str, str]]:
    paths = list(UPLOAD_PATH_WORDLIST)
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
            'method': 'POST',
            'field': 'file',
            'source': 'wordlist',
            'url': join_http_url(base_url, path),
        })
    return found


def merge_candidates(*groups: List[Dict[str, str]]) -> List[Dict[str, str]]:
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            key = f"{item.get('method', 'POST')} {item['url']}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


def resolve_targets(handler: dict, api_specs: dict, base_url: str) -> List[Dict[str, str]]:
    explicit = handler.get('upload_endpoint')
    field = handler.get('upload_field') or 'file'

    if explicit:
        paths = explicit if isinstance(explicit, list) else [explicit]
        return [{
            'path': path if path.startswith('/') else f'/{path}',
            'method': 'POST',
            'field': field,
            'source': 'cli',
            'url': join_http_url(base_url, path),
        } for path in paths]

    openapi_hits = discover_from_openapi(api_specs, base_url) if api_specs else []
    wordlist_hits = discover_from_wordlist(base_url)
    return merge_candidates(openapi_hits, wordlist_hits)
