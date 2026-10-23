# -*- coding: utf-8 -*-
"""Pydantic request/response models for Control API v1."""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
    _V2 = True
except ImportError:
    ConfigDict = None  # type: ignore
    _V2 = False


class RunRequest(BaseModel):
    """Body for POST /v1/plugins/{name}/run — arbitrary specialty + shared flags."""

    args: Dict[str, Any] = Field(default_factory=dict)
    async_mode: bool = Field(
        False,
        alias='async',
        description='If true, enqueue background run and return 202 immediately',
    )

    if _V2:
        model_config = ConfigDict(extra='allow', populate_by_name=True)
    else:
        class Config:
            extra = 'allow'
            allow_population_by_field_name = True


class LabActionResponse(BaseModel):
    plugin: str
    ok: Optional[bool] = None
    running: bool = False
    valid: bool = False
    url: Optional[str] = None
    ports: list = Field(default_factory=list)
    missing_files: list = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    lab_path: Optional[str] = None
