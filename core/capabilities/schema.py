# -*- coding: utf-8 -*-
# Lightweight validation for composition.lab / composition.specialty_args.

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def validate_composition_capabilities(
    composition: Any,
    *,
    plugin: str = '',
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate optional capability blocks under composition.

    Returns (normalized_composition, warnings). Raises ValueError on hard errors.
    """
    warnings: List[str] = []
    if composition is None:
        return {}, warnings
    if not isinstance(composition, dict):
        raise ValueError(f'{plugin}: composition must be a mapping')

    comp = dict(composition)

    lab = comp.get('lab')
    if lab is not None:
        if not isinstance(lab, dict):
            raise ValueError(f'{plugin}: composition.lab must be a mapping')
        if 'port' in lab and lab['port'] is not False:
            try:
                lab['port'] = int(lab['port'])
            except (TypeError, ValueError) as exc:
                raise ValueError(f'{plugin}: composition.lab.port must be an int') from exc
        if 'run_hint' in lab and lab['run_hint'] is not None and not isinstance(lab['run_hint'], str):
            raise ValueError(f'{plugin}: composition.lab.run_hint must be a string')
        comp['lab'] = lab

    specialty = comp.get('specialty_args')
    if specialty is not None:
        if not isinstance(specialty, dict):
            raise ValueError(f'{plugin}: composition.specialty_args must be a mapping')
        flags = specialty.get('flags') or []
        if not isinstance(flags, list):
            raise ValueError(f'{plugin}: composition.specialty_args.flags must be a list')
        for idx, flag in enumerate(flags):
            if not isinstance(flag, dict):
                raise ValueError(f'{plugin}: specialty_args.flags[{idx}] must be a mapping')
            if not flag.get('flags') or not isinstance(flag['flags'], list):
                raise ValueError(f'{plugin}: specialty_args.flags[{idx}].flags must be a non-empty list')
            if not flag.get('dest'):
                raise ValueError(f'{plugin}: specialty_args.flags[{idx}].dest is required')
            action = flag.get('action', 'store')
            if action not in ('store', 'store_true', 'store_false', 'append'):
                raise ValueError(f'{plugin}: unsupported action {action!r} in specialty_args.flags[{idx}]')
        tactical = specialty.get('tactical_keys') or []
        if tactical and not isinstance(tactical, list):
            raise ValueError(f'{plugin}: specialty_args.tactical_keys must be a list')
        comp['specialty_args'] = specialty

    return comp, warnings
