# -*- coding: utf-8 -*-
"""Format informational tool payloads into readable agent final answers."""

from __future__ import annotations

from typing import Any, Dict, List


def format_about_answer(payload: Dict[str, Any]) -> str:
    name = payload.get('name') or 'Vimana'
    ver = payload.get('version') or ''
    lines: List[str] = [
        f"{name} {ver}".strip(),
        '',
        (payload.get('summary') or '').strip(),
        '',
        'Capabilities:',
    ]
    for cap in payload.get('capabilities') or []:
        lines.append(f'  - {cap}')
    cli = payload.get('cli') or {}
    if cli:
        lines.append('')
        lines.append('Useful CLI:')
        for k, v in cli.items():
            if v:
                lines.append(f'  - {k}: `{v}`')
    docs = payload.get('docs') or []
    if docs:
        lines.append('')
        lines.append('Docs: ' + ', '.join(docs))
    url = payload.get('url')
    if url:
        lines.append('')
        lines.append(str(url))
    return '\n'.join(lines).strip() + '\n'


def format_plugin_answer(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return str(payload)
    if payload.get('error'):
        return f"Error: {payload.get('error')}\n"

    name = payload.get('name') or '?'
    focus = payload.get('focus') or 'overview'
    lines: List[str] = [
        f"Plugin: {name}",
        f"Type: {payload.get('type') or '—'}  |  Category: {payload.get('category') or '—'}",
    ]
    if payload.get('framework'):
        lines.append(f"Framework: {payload.get('framework')}")
    lines.append(
        f"Lab: {'yes' if payload.get('has_lab') else 'no'}  |  "
        f"Orchestrator: {'yes' if payload.get('has_orchestrator') else 'no'}"
    )
    info = (payload.get('info') or '').strip()
    if info:
        lines.extend(['', info])
    desc = (payload.get('description') or '').strip()
    if desc and focus == 'overview' and desc != info:
        # keep overview readable
        preview = desc if len(desc) <= 900 else desc[:900] + '…'
        lines.extend(['', preview])

    guide = payload.get('guide') or {}
    if focus == 'overview':
        for key, label in (
            ('args_preview', 'Args (preview)'),
            ('examples_preview', 'Examples (preview)'),
            ('labs_preview', 'Lab setup (preview)'),
        ):
            block = (guide.get(key) or '').strip()
            if block:
                lines.extend(['', f'{label}:', block])
    else:
        for key, label in (
            ('args', 'Arguments'),
            ('examples', 'Examples'),
            ('labs', 'Lab setup'),
        ):
            block = (guide.get(key) or '').strip()
            if block:
                lines.extend(['', f'{label}:', block])
        form = guide.get('form') or []
        if form:
            lines.extend(['', 'Form fields:'])
            for field in form[:40]:
                if isinstance(field, dict):
                    lines.append(
                        f"  - {field.get('name') or field.get('dest')}: "
                        f"{field.get('help') or field.get('label') or ''}"
                    )

    cli = payload.get('cli') or {}
    if cli:
        lines.extend(['', 'CLI:'])
        for k, v in cli.items():
            if v:
                lines.append(f'  - {k}: `{v}`')

    return '\n'.join(lines).strip() + '\n'


def format_analyze_answer(payload: Dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        return str(payload)
    if payload.get('error') and not payload.get('frameworks'):
        return (
            f"Analyze failed at stage={payload.get('stage') or '?'}: "
            f"{payload.get('error')}\n"
        )

    lines: List[str] = [
        f"Target analysis: {payload.get('target_url') or '?'}",
        (
            f"ok={payload.get('ok')}  auto={payload.get('auto')}  "
            f"fingerprint={((payload.get('fingerprint') or {}).get('plugin'))}"
        ),
    ]
    playbook = payload.get('playbook') or []
    if playbook:
        lines.append('Playbook order: ' + ' → '.join(playbook))
    fp = payload.get('fingerprint') or {}
    if fp.get('run_id'):
        lines.append(f"fingerprint run_id={fp.get('run_id')} status={fp.get('status')}")
    if fp.get('error'):
        lines.append(f"fingerprint error: {fp.get('error')}")

    primary = payload.get('primary_framework')
    if primary:
        lines.extend([
            '',
            f"Primary framework: {primary.get('name')} "
            f"(confidence={primary.get('confidence')}, version={primary.get('version') or '?'})",
        ])
    else:
        lines.extend(['', 'Primary framework: (none detected)'])

    fws = payload.get('frameworks') or []
    if len(fws) > 1:
        lines.append('Other detections:')
        for fw in fws[1:6]:
            lines.append(
                f"  - {fw.get('name')} confidence={fw.get('confidence')} "
                f"version={fw.get('version') or '?'}"
            )

    cands = payload.get('candidates') or []
    lines.extend(['', f'Recommended plugins ({len(cands)}):'])
    if not cands:
        lines.append('  (none — try vimana_list_plugins / widen include_fuzzers)')
    for c in cands:
        lines.append(
            f"  - {c.get('name')} [{c.get('category')}/{c.get('framework')}] "
            f"— {c.get('reason')} (score={c.get('score')})"
        )
        info = (c.get('info') or '').strip()
        if info:
            lines.append(f"      {info[:160]}")

    follows = payload.get('follow_ups') or []
    if follows:
        lines.extend(['', 'Follow-up runs:'])
        for f in follows:
            lines.append(
                f"  - {f.get('name')}: status={f.get('status')} "
                f"run_id={f.get('run_id')} err={f.get('error')}"
            )

    nxt = payload.get('next_steps') or {}
    note = nxt.get('note')
    if note:
        lines.extend(['', note])
    examples = nxt.get('cli_examples') or []
    if examples:
        lines.extend(['', 'CLI next:'])
        for ex in examples[:5]:
            lines.append(f'  `{ex}`')

    return '\n'.join(lines).strip() + '\n'
