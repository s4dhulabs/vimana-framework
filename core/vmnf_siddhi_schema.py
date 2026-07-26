# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# This file is part of Vimana Framework Project.
#
# Lightweight siddhi YAML schema validation (no external deps).

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


REQUIRED_TOP_LEVEL = (
    'name',
    'author',
    'brief',
    'category',
    'framework',
    'info',
    'module',
    'type',
    'astt',
    'tags',
    'composition',
    'description',
    'references',
    'vfset',
    'guide',
)

REQUIRED_GUIDE_KEYS = ('args', 'examples', 'lab_setup')
STRING_FIELDS = (
    'name',
    'author',
    'brief',
    'category',
    'framework',
    'info',
    'module',
    'type',
    'astt',
    'description',
)


class SiddhiSchemaError(ValueError):
    """Raised when a plugin YAML fails schema validation."""

    def __init__(self, plugin: str, errors: List[str], yaml_file: Optional[str] = None):
        self.plugin = plugin
        self.errors = errors
        self.yaml_file = yaml_file
        loc = f' ({yaml_file})' if yaml_file else ''
        detail = '; '.join(errors)
        super().__init__(f'{plugin}{loc}: {detail}')


def normalize_guide(guide: Any) -> Dict[str, Any]:
    """Normalize guide dict: accept labs as alias for lab_setup."""
    if not isinstance(guide, dict):
        return {}
    normalized = dict(guide)
    if 'lab_setup' not in normalized and 'labs' in normalized:
        normalized['lab_setup'] = normalized.pop('labs')
    elif 'labs' in normalized and 'lab_setup' in normalized:
        # Prefer lab_setup; drop redundant labs key
        normalized.pop('labs', None)
    return normalized


def guide_section(guide: Any, *keys: str, default: str = '') -> str:
    """Safe guide section lookup with alias support."""
    if not isinstance(guide, dict):
        return default
    for key in keys:
        value = guide.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return default


def validate_siddhi_schema(
    data: Any,
    *,
    plugin_name: str,
    yaml_file: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and lightly normalize a plugin YAML dict.

    Returns (normalized_data, warnings). Raises SiddhiSchemaError on hard failures.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(data, dict):
        raise SiddhiSchemaError(
            plugin_name,
            ['root must be a mapping/dict'],
            yaml_file=yaml_file,
        )

    normalized = dict(data)

    for key in REQUIRED_TOP_LEVEL:
        if key not in normalized or normalized[key] in (None, ''):
            # package is optional in the model; already not in REQUIRED
            errors.append(f'missing required key: {key}')

    for key in STRING_FIELDS:
        if key in normalized and normalized[key] is not None and not isinstance(normalized[key], str):
            errors.append(f'{key} must be a string')

    if 'tags' in normalized and not isinstance(normalized.get('tags'), list):
        errors.append('tags must be a list')

    if 'composition' in normalized and not isinstance(normalized.get('composition'), dict):
        errors.append('composition must be a mapping')
    elif isinstance(normalized.get('composition'), dict):
        try:
            from core.capabilities.schema import validate_composition_capabilities
            composition, cap_warnings = validate_composition_capabilities(
                normalized['composition'],
                plugin=plugin_name,
            )
            normalized['composition'] = composition
            warnings.extend(cap_warnings)
        except ValueError as exc:
            errors.append(str(exc))
        except Exception as exc:
            warnings.append(f'composition capability validation skipped: {exc}')

    if 'references' in normalized and not isinstance(normalized.get('references'), (dict, bool)):
        errors.append('references must be a mapping (or bool for legacy plugins)')

    if 'vfset' in normalized and not isinstance(normalized.get('vfset'), dict):
        errors.append('vfset must be a mapping')

    guide = normalized.get('guide')
    if guide is None:
        errors.append('missing required key: guide')
    elif not isinstance(guide, dict):
        errors.append('guide must be a mapping')
    else:
        guide = normalize_guide(guide)
        normalized['guide'] = guide
        for gkey in REQUIRED_GUIDE_KEYS:
            if gkey not in guide:
                errors.append(f'guide missing required key: {gkey}')
            elif not isinstance(guide.get(gkey), str):
                errors.append(f'guide.{gkey} must be a string')
        if 'naviargs' in guide and not isinstance(guide['naviargs'], (dict, str)):
            warnings.append('guide.naviargs has unexpected type (expected mapping or string)')

    # Trim string fields that are lowercased later
    for key in ('name', 'category', 'framework', 'package', 'type'):
        if key in normalized and isinstance(normalized[key], str):
            normalized[key] = normalized[key].strip()

    if errors:
        raise SiddhiSchemaError(plugin_name, errors, yaml_file=yaml_file)

    return normalized, warnings
