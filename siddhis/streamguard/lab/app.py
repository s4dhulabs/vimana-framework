# -*- coding: utf-8 -*-
"""
FastAPI SSE / NDJSON lab for streamguard testing.

Intentionally weak streaming security for audit demonstrations.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(
    title="Streamguard Lab API",
    description="Vulnerable SSE and NDJSON streams for streamguard audits",
    version="1.0.0",
)

_STREAM_OPENAPI_PATHS = (
    "/events",
    "/events/search",
    "/events/private",
    "/logs/stream",
)


def _lab_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    stream_hints = {
        "/events": "text/event-stream SSE notifications",
        "/events/search": "text/event-stream search with query reflection",
        "/events/private": "text/event-stream authenticated feed",
        "/logs/stream": "application/x-ndjson log tail",
    }
    for path, hint in stream_hints.items():
        schema.setdefault("paths", {})[path] = {
            "get": {
                "summary": hint,
                "description": f"Streaming endpoint — {hint}",
                "operationId": f"stream_{path.strip('/').replace('/', '_')}",
                "responses": {
                    "200": {
                        "description": "Stream",
                        "content": {
                            "text/event-stream": {"schema": {"type": "string"}},
                        },
                    }
                },
            }
        }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _lab_openapi


@app.get("/health")
async def health():
    return {"status": "ok", "service": "streamguard-lab"}


async def _sse_ticks(user: str = "guest") -> AsyncIterator[str]:
    for i in range(8):
        payload = json.dumps({"user": user, "seq": i, "channel": "public"})
        yield f"event: tick\nid: {i}\ndata: {payload}\n\n"
        await asyncio.sleep(0.4)


@app.get("/events")
async def events(request: Request):
    """Open SSE — accepts any client; cursor tampering can leak other tenant data."""
    last_id = request.headers.get("last-event-id", "")

    if last_id in ("user-b-leak", "99999"):
        async def leak() -> AsyncIterator[str]:
            secret = json.dumps({
                "leak": True,
                "tenant": "user-b",
                "secret": "user-b private stream payload",
            })
            yield f"event: leak\nid: leaked\n data: {secret}\n\n"
        return StreamingResponse(
            leak(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no"},
        )

    return StreamingResponse(
        _sse_ticks(),
        media_type="text/event-stream",
    )


@app.get("/events/search")
async def events_search(q: str = ""):
    """Reflects query in SSE data — vulnerable to CRLF injection in q."""

    async def gen() -> AsyncIterator[str]:
        yield f"event: search\n data: search result for {q}\n\n"
        yield f"data: {json.dumps({'query': q})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/events/private")
async def events_private(request: Request):
    """Should require auth — used for auth drift comparison in lab docs."""
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return StreamingResponse(
        _sse_ticks(user="authenticated"),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/logs/stream")
async def logs_stream():
    """Open NDJSON log stream."""

    async def ndjson() -> AsyncIterator[str]:
        for i in range(6):
            line = json.dumps({"level": "info", "msg": f"log line {i}", "tenant": "shared"})
            yield line + "\n"
            await asyncio.sleep(0.35)

    return StreamingResponse(ndjson(), media_type="application/x-ndjson")
