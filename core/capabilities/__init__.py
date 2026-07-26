# -*- coding: utf-8 -*-
# Plugin capability registry — specialty CLI flags + lab metadata from YAML.

from .loader import (
    clear_capability_cache,
    discover_capabilities,
    get_capability,
    get_lab_meta,
    register_specialty_args,
    specialty_tactical_keys,
)
from .schema import validate_composition_capabilities

__all__ = [
    'clear_capability_cache',
    'discover_capabilities',
    'get_capability',
    'get_lab_meta',
    'register_specialty_args',
    'specialty_tactical_keys',
    'validate_composition_capabilities',
]
