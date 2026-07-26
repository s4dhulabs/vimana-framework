# -*- coding: utf-8 -*-
# Discover plugin YAML capabilities and register specialty argparse flags.

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

import yaml

from core.capabilities.schema import validate_composition_capabilities


def _vimana_root() -> str:
    env = os.getenv('VIMANA_PATH')
    if env and os.path.exists(env):
        return env
    here = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(os.path.dirname(here)))


def _siddhis_path() -> str:
    return os.path.join(_vimana_root(), 'siddhis')


@lru_cache(maxsize=1)
def discover_capabilities() -> Dict[str, Dict[str, Any]]:
    """
    Load composition capabilities from siddhis/*/*.yaml.

    Returns {plugin_name: {lab: {...}, specialty_args: {...}, raw_composition: {...}}}.
    """
    registry: Dict[str, Dict[str, Any]] = {}
    root = _siddhis_path()
    if not os.path.isdir(root):
        return registry

    for entry in os.scandir(root):
        if not entry.is_dir() or entry.name.startswith('_'):
            continue
        yaml_path = os.path.join(entry.path, f'{entry.name}.yaml')
        if not os.path.exists(yaml_path):
            continue
        try:
            with open(yaml_path, 'r') as handle:
                data = yaml.load(handle, Loader=yaml.FullLoader) or {}
        except Exception:
            continue

        composition = data.get('composition') or {}
        try:
            composition, _warnings = validate_composition_capabilities(
                composition, plugin=entry.name
            )
        except ValueError:
            continue

        # composition.lab wins; vfset.lab is a legacy/fallback source
        vfset = data.get('vfset') if isinstance(data.get('vfset'), dict) else {}
        lab = composition.get('lab') or {}
        if not lab and isinstance(vfset.get('lab'), dict):
            lab = dict(vfset.get('lab') or {})

        registry[entry.name] = {
            'plugin': entry.name,
            'lab': lab,
            'specialty_args': composition.get('specialty_args') or {},
            'composition': composition,
            'yaml_file': yaml_path,
        }
    return registry


def get_capability(plugin: str) -> Optional[Dict[str, Any]]:
    return discover_capabilities().get(plugin)


def get_lab_meta(plugin: str) -> Dict[str, Any]:
    cap = get_capability(plugin) or {}
    return dict(cap.get('lab') or {})


def specialty_tactical_keys() -> List[str]:
    """Union of all specialty tactical_keys declared in plugin YAMLs."""
    keys: List[str] = []
    seen = set()
    for cap in discover_capabilities().values():
        specialty = cap.get('specialty_args') or {}
        for key in specialty.get('tactical_keys') or []:
            if key not in seen:
                seen.add(key)
                keys.append(str(key))
        # Fallback: every dest from flags is also tactical
        for flag in specialty.get('flags') or []:
            dest = flag.get('dest')
            if dest and dest not in seen:
                # Only auto-include audit/path style keys when tactical_keys omitted
                if specialty.get('tactical_keys'):
                    continue
                seen.add(dest)
                keys.append(str(dest))
    return keys


_TYPE_MAP = {
    'int': int,
    'float': float,
    'str': str,
}


def register_specialty_args(parser) -> int:
    """
    Register specialty flags from plugin YAML onto an argparse parser.

    Returns number of flags registered.
    """
    count = 0
    seen_dests = set()
    for cap in discover_capabilities().values():
        specialty = cap.get('specialty_args') or {}
        for flag in specialty.get('flags') or []:
            dest = flag.get('dest')
            if not dest or dest in seen_dests:
                continue
            seen_dests.add(dest)
            kwargs: Dict[str, Any] = {
                'dest': dest,
                'default': flag.get('default', False),
            }
            action = flag.get('action', 'store')
            kwargs['action'] = action
            if action == 'store' and 'type' in flag:
                type_name = flag['type']
                if isinstance(type_name, str) and type_name in _TYPE_MAP:
                    kwargs['type'] = _TYPE_MAP[type_name]
            if flag.get('help'):
                kwargs['help'] = flag['help']
            # nargs support
            if 'nargs' in flag:
                kwargs['nargs'] = flag['nargs']
            if 'const' in flag:
                kwargs['const'] = flag['const']

            flag_names = list(flag.get('flags') or [])
            parser.add_argument(*flag_names, **kwargs)
            count += 1
    return count


def clear_capability_cache() -> None:
    discover_capabilities.cache_clear()
