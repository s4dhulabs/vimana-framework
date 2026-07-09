# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from neotermcolor import colored
from prettytable import PrettyTable

from core._dbops_.vmnf_dbops import VFDBOps

logger = logging.getLogger('vmnf_specs')

DEFAULT_OPENAPI_PATHS = (
    '/openapi.json',
    '/docs/openapi.json',
    '/api/openapi.json',
    '/api/v1/openapi.json',
    '/swagger/v1/swagger.json',
    '/redoc/openapi.json',
)

SPEC_ID_PREFIX = 'aS'
SPEC_ID_LENGTH = 4


def get_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def get_methods(api_specs: dict) -> str:
    methods = set()
    for path_item in api_specs.get('paths', {}).values():
        if not isinstance(path_item, dict):
            continue
        for method in path_item:
            if method.lower() in {
                'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace',
            }:
                methods.add(method.upper())
    return ','.join(sorted(methods)) or 'N/A'


def content_fingerprint(api_specs: dict) -> str:
    return get_hash(json.dumps(api_specs, sort_keys=True))


def generate_spec_id(api_specs: dict) -> str:
    """
    Canonical Vimana spec ID: aS + 4 hex chars (same format as jcolt).
    """
    salted = content_fingerprint(api_specs) + str(int(datetime.now().timestamp()))
    return f'{SPEC_ID_PREFIX}{get_hash(salted)[:SPEC_ID_LENGTH]}'


def get_specs():
    result = VFDBOps().list_resource('_SPECS_', [])
    return result if isinstance(result, list) else []


def find_spec_by_host_and_fingerprint(base_url: str, fingerprint: str) -> Optional[Any]:
    normalized_host = base_url.rstrip('/')
    for record in get_specs():
        if record.spec_host.rstrip('/') != normalized_host:
            continue
        spec_path = record.spec_file_path
        if not spec_path or not os.path.exists(spec_path):
            continue
        try:
            with open(spec_path, 'r') as handle:
                existing = json.load(handle)
            if content_fingerprint(existing) == fingerprint:
                return record
        except (json.JSONDecodeError, OSError):
            continue
    return None


def validate_openapi(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise ValueError('OpenAPI payload is not a JSON object')
    if 'paths' not in payload or not isinstance(payload['paths'], dict):
        raise ValueError('OpenAPI document missing a valid paths object')
    return payload


async def fetch_openapi(
    base_url: str,
    custom_url: Optional[str] = None,
    timeout: float = 30.0,
) -> dict:
    base_url = base_url.rstrip('/')
    candidates = []
    if custom_url:
        candidates.append(custom_url)
    candidates.extend(urljoin(base_url + '/', path.lstrip('/')) for path in DEFAULT_OPENAPI_PATHS)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
        for url in candidates:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
                return validate_openapi(response.json())
            except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
                logger.debug('OpenAPI fetch failed for %s: %s', url, exc)
                continue

    raise ValueError(
        f'No OpenAPI specification found for {base_url}. '
        f'Tried: {", ".join(candidates[:5])}...'
    )


def register_openapi_spec(
    api_specs: dict,
    base_url: str,
    *,
    plugin: str = 'vimana',
    cache_subdir: str = 'openapi',
    env_path: Optional[str] = None,
    env_mapping: Optional[Dict[str, str]] = None,
    quiet: bool = False,
    upsert: bool = True,
) -> Tuple[str, dict, dict]:
    """
    Register OpenAPI spec in _SPECS_, cache on disk, optionally write plugin env file.

    Returns (spec_id, api_specs, spec_info dict).
    """
    api_specs = validate_openapi(api_specs)
    base_url = base_url.rstrip('/')
    fingerprint = content_fingerprint(api_specs)

    spec_id = None
    existing = None
    if upsert:
        existing = find_spec_by_host_and_fingerprint(base_url, fingerprint)
        if existing:
            spec_id = existing.spec_id

    if not spec_id:
        spec_id = generate_spec_id(api_specs)

    cache_dir = os.path.expanduser(f'~/.vimana/cache/{plugin}/{cache_subdir}')
    os.makedirs(cache_dir, exist_ok=True)
    spec_path = os.path.join(cache_dir, f'{spec_id}.json')

    with open(spec_path, 'w') as handle:
        json.dump(api_specs, handle, indent=2)

    api_info = api_specs.get('info', {})
    spec_info = {
        'spec_id': spec_id,
        'spec_title': api_info.get('title', 'Unknown API'),
        'fastapi_version': api_info.get('version', '?'),
        'openapi_version': api_specs.get('openapi', api_specs.get('swagger', '?')),
        'spec_host': base_url,
        'spec_paths': len(api_specs.get('paths', {})),
        'spec_methods': get_methods(api_specs),
        'spec_file_path': spec_path,
        'spec_date': datetime.now(),
    }

    if not existing:
        VFDBOps(**spec_info).register('_SPECS_')

    if env_path and env_mapping:
        os.makedirs(os.path.dirname(env_path) or '.', exist_ok=True)
        with open(env_path, 'w') as handle:
            for key, value in env_mapping.items():
                handle.write(f'{key}={value}\n')

    if not quiet:
        print(colored('\n[+] OpenAPI specification registered', 'green'))
        print(f"    Spec ID : {colored(spec_id, 'cyan')}")
        print(f"    Title   : {spec_info['spec_title']}")
        print(f"    Host    : {spec_info['spec_host']}")
        print(f"    Paths   : {spec_info['spec_paths']}")
        print(f"    Methods : {spec_info['spec_methods']}")
        print(f"    Cache   : {spec_path}\n")

    return spec_id, api_specs, spec_info


def load_spec_from_db(spec_id: str) -> Tuple[dict, str, str]:
    record = VFDBOps().get_by_id('_SPECS_', 'spec_id', spec_id)
    if not record:
        raise ValueError(f'Spec {spec_id} not found in Vimana database')

    spec_path = record.spec_file_path
    if not spec_path or not os.path.exists(spec_path):
        raise ValueError(f'Spec file missing for {spec_id}: {spec_path}')

    with open(spec_path, 'r') as handle:
        api_specs = validate_openapi(json.load(handle))

    return api_specs, record.spec_host, spec_id


def list_specs(specs=None):
    if specs is None:
        specs = get_specs()

    if not specs:
        print(colored('No API specs found.', 'yellow'))
        print()
        return False

    output_table = PrettyTable()
    output_table.title = f"Vimana API Specs - {len(specs)} registered"
    output_table.field_names = [
        "Index", "ID", "Title", "FastAPI", "OpenAPI",
        "Host", "Paths", "Methods", "Date",
    ]
    output_table.align = 'l'

    for tbl_index, spec in enumerate(specs, 1):
        output_table.add_row([
            tbl_index,
            colored(spec.spec_id, 49),
            spec.spec_title[:20] if spec.spec_title else '',
            spec.fastapi_version,
            spec.openapi_version,
            spec.spec_host,
            spec.spec_paths,
            spec.spec_methods,
            spec.spec_date,
        ])

    print(output_table)
    print()
    return specs


class VFSpecsManager:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.model = '_SPECS_'

    def get_specs(self):
        result = VFDBOps().list_resource(self.model, [])
        return result if isinstance(result, list) else []

    def list_specs(self):
        return list_specs(self.get_specs())
