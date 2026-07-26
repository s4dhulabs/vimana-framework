# -*- coding: utf-8 -*-
# Quiet / banner helpers shared by specialty plugins.


def is_quiet(handler: dict) -> bool:
    """True when plugins should suppress human console noise."""
    handler = handler or {}
    return bool(
        handler.get('ci_mode')
        or handler.get('json_output')
        or handler.get('no_metadata')
        or handler.get('quiet_output')
        or handler.get('_orchestrator')
    )


def should_show_banner(handler: dict) -> bool:
    """Banner only when explicitly requested and not in quiet/CI mode."""
    handler = handler or {}
    if is_quiet(handler):
        return False
    return bool(handler.get('show_banner'))
