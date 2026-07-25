# -*- coding: utf-8 -*-
# OpenAPI resolution for schemage (delegates to core.vmnf_specs).

import asyncio
import json
import os
from typing import Dict, Optional, Tuple

from core import vmnf_specs as specs_core


class SpecResolutionError(Exception):
    pass


class SchemageSpecManager:
    """Schemage-facing wrapper around canonical Vimana OpenAPI management."""

    ENV_PATH = os.path.expanduser('~/.schemage_env')
    PLUGIN = 'schemage'
    CACHE_SUBDIR = 'specs'

    def __init__(self, handler: dict):
        self.handler = handler
        self.quiet = bool(
            handler.get('ci_mode')
            or handler.get('json_output')
            or handler.get('no_metadata')
            or handler.get('quiet_output')
            or handler.get('_orchestrator')
        )
        self._env = self._load_env()

    def _load_env(self) -> Dict[str, str]:
        if not os.path.exists(self.ENV_PATH):
            return {}
        env = {}
        with open(self.ENV_PATH, 'r') as handle:
            for line in handle:
                line = line.strip()
                if not line or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                env[key.strip()] = value.strip()
        return env

    def _save_env(self, spec_id: str, spec_info: dict) -> None:
        env_map = {
            'SCHEMAGE_SPEC_ID': spec_id,
            'SCHEMAGE_TARGET': spec_info['spec_host'],
            'SCHEMAGE_API_TITLE': spec_info['spec_title'],
            'SCHEMAGE_OPENAPI_VERSION': str(spec_info['openapi_version']),
            'SCHEMAGE_LAST_SCAN': spec_info['spec_date'].strftime('%Y-%m-%d %H:%M:%S'),
            'SCHEMAGE_SPEC_FILE': spec_info['spec_file_path'],
        }
        os.makedirs(os.path.dirname(self.ENV_PATH) or '.', exist_ok=True)
        with open(self.ENV_PATH, 'w') as handle:
            for key, value in env_map.items():
                handle.write(f'{key}={value}\n')

    def _register(self, api_specs: dict, base_url: str) -> Tuple[str, dict]:
        spec_id, api_specs, spec_info = specs_core.register_openapi_spec(
            api_specs,
            base_url,
            plugin=self.PLUGIN,
            cache_subdir=self.CACHE_SUBDIR,
            quiet=self.quiet,
            upsert=True,
        )
        self._save_env(spec_id, spec_info)
        return spec_id, api_specs

    def load_from_db(self, spec_id: str) -> Tuple[dict, str, str]:
        try:
            return specs_core.load_spec_from_db(spec_id)
        except ValueError as exc:
            raise SpecResolutionError(str(exc)) from exc

    def load_from_file(self, path: str) -> dict:
        if not os.path.exists(path):
            raise SpecResolutionError(f'Spec file not found: {path}')
        with open(path, 'r') as handle:
            try:
                return specs_core.validate_openapi(json.load(handle))
            except ValueError as exc:
                raise SpecResolutionError(str(exc)) from exc

    def _resolve_spec_id(self) -> Optional[str]:
        for key in ('apispec_enabled', 'fuzzerspec_enabled', 'inspect'):
            value = self.handler.get(key)
            if value and value not in (False, 'ENV_FALLBACK'):
                return value

        if self.handler.get('load_from_env') or any(
            self.handler.get(key) == 'ENV_FALLBACK'
            for key in ('apispec_enabled', 'fuzzerspec_enabled', 'inspect')
        ):
            return self._env.get('SCHEMAGE_SPEC_ID')

        return None

    def _resolve_target_url(self) -> Optional[str]:
        scan = self.handler.get('api_scan_enabled')
        if scan and scan not in (False, 'ENV_FALLBACK'):
            return scan
        if scan == 'ENV_FALLBACK':
            return self._env.get('SCHEMAGE_TARGET')
        target = self.handler.get('target_url')
        if target:
            return target
        return self._env.get('SCHEMAGE_TARGET')

    async def fetch_openapi(self, base_url: str, custom_url: Optional[str] = None) -> dict:
        try:
            return await specs_core.fetch_openapi(base_url, custom_url=custom_url)
        except ValueError as exc:
            raise SpecResolutionError(str(exc)) from exc

    async def resolve(self) -> Tuple[dict, str, Optional[str]]:
        spec_file = self.handler.get('openapi_spec_file')
        spec_url = self.handler.get('openapi_spec_url')
        scan = self.handler.get('api_scan_enabled')
        target_url = self._resolve_target_url()

        if scan and scan not in (False, 'ENV_FALLBACK'):
            api_specs = await self.fetch_openapi(scan, custom_url=spec_url)
            spec_id, api_specs = self._register(api_specs, scan)
            return api_specs, scan.rstrip('/'), spec_id

        if scan == 'ENV_FALLBACK':
            if not target_url:
                raise SpecResolutionError('No target in ~/.schemage_env. Run --scan-api first.')
            api_specs = await self.fetch_openapi(target_url, custom_url=spec_url)
            spec_id, api_specs = self._register(api_specs, target_url)
            return api_specs, target_url.rstrip('/'), spec_id

        if spec_file:
            api_specs = self.load_from_file(spec_file)
            if target_url:
                spec_id, api_specs = self._register(api_specs, target_url)
                return api_specs, target_url.rstrip('/'), spec_id
            return api_specs, '', None

        if spec_url and target_url:
            api_specs = await self.fetch_openapi(target_url, custom_url=spec_url)
            spec_id, api_specs = self._register(api_specs, target_url)
            return api_specs, target_url.rstrip('/'), spec_id

        spec_id = self._resolve_spec_id()
        if spec_id:
            return self.load_from_db(spec_id)

        if target_url:
            api_specs = await self.fetch_openapi(target_url, custom_url=spec_url)
            spec_id, api_specs = self._register(api_specs, target_url)
            return api_specs, target_url.rstrip('/'), spec_id

        raise SpecResolutionError(
            'No API context provided. Use --scan-api, --target-url, --apispec, '
            '--spec-file, or --frame-path with --target-url.'
        )

    def run_scan_sync(self, base_url: Optional[str] = None) -> Tuple[str, dict]:
        url = base_url or self._resolve_target_url()
        if not url:
            raise SpecResolutionError('--scan-api or --target-url is required for API scan')

        async def _scan():
            custom = self.handler.get('openapi_spec_url')
            specs = await self.fetch_openapi(url, custom_url=custom)
            return self._register(specs, url)

        return asyncio.run(_scan())
