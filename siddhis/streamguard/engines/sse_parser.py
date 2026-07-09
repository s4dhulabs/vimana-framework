# -*- coding: utf-8 -*-
# SSE frame parsing helpers.

from typing import Any, Dict, List


def parse_sse_events(raw: str) -> List[Dict[str, Any]]:
    """Parse Server-Sent Events text into structured event dicts."""
    events: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}

    for line in raw.splitlines():
        if not line.strip():
            if current:
                events.append(current)
                current = {}
            continue

        if line.startswith(':'):
            continue

        if ':' in line:
            field, value = line.split(':', 1)
            field = field.strip()
            value = value.lstrip()
        else:
            field, value = line.strip(), ''

        if field == 'event':
            current['event'] = value
        elif field == 'data':
            current['data'] = current.get('data', '') + value
        elif field == 'id':
            current['id'] = value
        elif field == 'retry':
            current['retry'] = value

    if current:
        events.append(current)

    return events


def count_ndjson_lines(raw: str) -> int:
    return sum(1 for line in raw.splitlines() if line.strip())


def looks_like_stream(content_type: str, body_preview: str) -> bool:
    ct = (content_type or '').lower()
    if 'text/event-stream' in ct:
        return True
    if 'ndjson' in ct or 'jsonlines' in ct:
        return True
    if body_preview.startswith('event:') or 'data:' in body_preview[:200]:
        return True
    if body_preview.count('\n') >= 2 and body_preview.strip().startswith('{'):
        return True
    return False
