# -*- coding: utf-8 -*-
"""Build UI/API form schemas from plugin YAML capabilities + guide.naviargs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _dest_to_flag(dest: str) -> str:
    return '--' + dest.replace('_', '-')


def _field(
    *,
    dest: str,
    action: str = 'store',
    flags: Optional[List[str]] = None,
    default: Any = None,
    help_text: str = '',
    required: bool = False,
    input_type: str = 'text',
    source: str = 'specialty',
) -> Dict[str, Any]:
    flag_list = list(flags) if flags else [_dest_to_flag(dest)]
    # Heuristics for HTML input type
    if action == 'store_true':
        input_type = 'checkbox'
    elif dest in ('target_url', 'endpoint_url') or dest.endswith('_url'):
        input_type = 'url'
    return {
        'dest': dest,
        'flags': flag_list,
        'label': flag_list[0],
        'action': action,
        'type': input_type,
        'default': False if action == 'store_true' and default is None else default,
        'help': help_text or '',
        'required': required,
        'source': source,
    }


def build_plugin_form(
    *,
    plugin: str,
    specialty_args: Optional[Dict[str, Any]] = None,
    naviargs: Optional[Dict[str, Any]] = None,
    lab: Optional[Dict[str, Any]] = None,
    vfset: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Ordered form fields for Admin UI / Control API clients.

    Priority:
      1. composition.specialty_args.flags
      2. guide.naviargs keys not already covered
      3. target_url when lab.run_hint / naviargs / scope plugins imply it
    """
    specialty_args = specialty_args or {}
    naviargs = naviargs if isinstance(naviargs, dict) else {}
    lab = lab if isinstance(lab, dict) else {}
    vfset = vfset if isinstance(vfset, dict) else {}

    fields: List[Dict[str, Any]] = []
    seen = set()

    for block in specialty_args.get('flags') or []:
        flag = block if isinstance(block, dict) else {}
        dest = flag.get('dest')
        if not dest or dest in seen:
            continue
        action = flag.get('action', 'store')
        fields.append(
            _field(
                dest=dest,
                action=action,
                flags=list(flag.get('flags') or []) or None,
                default=flag.get('default', False if action == 'store_true' else None),
                help_text=str(flag.get('help') or ''),
                required=bool(flag.get('required')),
                source='specialty',
            )
        )
        seen.add(dest)

    for dest, _hint in naviargs.items():
        if not dest or dest in seen:
            continue
        # naviargs values are legacy bools (presence), not defaults
        fields.append(
            _field(
                dest=str(dest),
                action='store',
                default='',
                help_text=f'From guide.naviargs ({plugin})',
                required=True,
                source='naviargs',
            )
        )
        seen.add(str(dest))

    run_hint = str(lab.get('run_hint') or '')
    # Lab-oriented plugins need target_url even when naviargs omitted it
    needs_target = (
        '{url}' in run_hint
        or '--target-url' in run_hint
        or bool(lab.get('port'))
    )
    if needs_target and 'target_url' not in seen:
        fields.append(
            _field(
                dest='target_url',
                action='store',
                default='',
                help_text='Target base URL',
                required=True,
                source='shared',
            ),
        )
        seen.add('target_url')

    for f in fields:
        if f['dest'] == 'target_url':
            f['type'] = 'url'
            if not f.get('label') or f['label'] == 'target_url':
                f['label'] = '--target-url'

    # Prefer target_url at the top of the form when present
    fields.sort(key=lambda f: 0 if f.get('dest') == 'target_url' else 1)

    return fields
