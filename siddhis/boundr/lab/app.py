# -*- coding: utf-8 -*-
"""
FastAPI UploadFile lab for boundr testing.

Intentionally weak upload security: path traversal, MIME trust, no size limits.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Boundr Lab API",
    description="Vulnerable UploadFile endpoints for boundr audits",
    version="1.0.0",
)

UPLOAD_DIR = Path("/tmp/boundr_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _lab_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Ensure multipart content types are explicit for discovery
    for path in ("/upload", "/api/files"):
        if path in schema.get("paths", {}):
            continue
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _lab_openapi


@app.get("/health")
async def health():
    return {"status": "ok", "service": "boundr-lab"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Vulnerable upload: trusts client filename (path traversal),
    trusts Content-Type, no size limit, reflects saved path.
    """
    # Intentionally unsafe: join with client-controlled filename
    dest = UPLOAD_DIR / file.filename
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Allow escaping UPLOAD_DIR via ../ in filename
    try:
        with open(dest, "wb") as handle:
            shutil.copyfileobj(file.file, handle)
    except OSError as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

    return {
        "status": "ok",
        "filename": file.filename,
        "content_type": file.content_type,
        "saved_as": str(dest.resolve()),
        "size": dest.stat().st_size if dest.exists() else 0,
    }


@app.post("/api/files")
async def upload_document(
    document: UploadFile = File(...),
    note: Optional[str] = Form(None),
):
    """Alternate field name `document` — same weak storage policy."""
    dest = UPLOAD_DIR / "docs" / document.filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as handle:
        shutil.copyfileobj(document.file, handle)

    return {
        "status": "stored",
        "field": "document",
        "filename": document.filename,
        "content_type": document.content_type,
        "path": str(dest),
        "note": note,
    }


@app.get("/uploads/list")
async def list_uploads():
    files = []
    for root, _, names in os.walk(UPLOAD_DIR):
        for name in names:
            files.append(os.path.join(root, name))
    return {"files": files}
