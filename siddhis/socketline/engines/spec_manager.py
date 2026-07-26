# -*- coding: utf-8 -*-
# Shim: OpenAPI SpecManager — re-exported from core.spec_runtime.

from core.spec_runtime import SpecManager, SpecResolutionError  # noqa: F401


class SocketlineSpecManager(SpecManager):
    """socketline-facing wrapper around canonical Vimana OpenAPI management."""

    def __init__(self, handler: dict):
        super().__init__(handler, plugin='socketline')
