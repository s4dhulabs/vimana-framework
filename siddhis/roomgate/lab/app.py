# -*- coding: utf-8 -*-
"""
FastAPI WebSocket lab for roomgate (room authz / IDOR).

Intentionally weak:
  /ws/room/{id}   — no auth at all
  /ws/secure/{id} — requires Bearer token but does NOT enforce room membership
                    (user-a can join room-b → classic BOLA)
"""

from __future__ import annotations

from typing import Dict, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Roomgate Lab API",
    description="Vulnerable WebSocket room endpoints for roomgate IDOR audits",
    version="1.0.0",
)

# token -> set of rooms the identity *should* own (enforcement missing on /ws/secure)
_MEMBERSHIP: Dict[str, Set[str]] = {
    "user-a": {"room-a"},
    "user-b": {"room-b"},
    "guest": set(),
}

_WS_OPENAPI_PATHS = (
    "/ws/room/{room_id}",
    "/ws/secure/{room_id}",
)

_open_rooms: Dict[str, Set[WebSocket]] = {}
_secure_rooms: Dict[str, Set[WebSocket]] = {}


def _lab_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    for path in _WS_OPENAPI_PATHS:
        schema.setdefault("paths", {})[path] = {
            "get": {
                "summary": f"WebSocket room endpoint {path}",
                "description": "HTTP GET upgrades to WebSocket room connection",
                "operationId": (
                    f"ws_{path.strip('/').replace('/', '_').replace('{', '').replace('}', '')}"
                ),
            }
        }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _lab_openapi


def _token_from_headers(websocket: WebSocket) -> Optional[str]:
    auth = websocket.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    if auth:
        return auth.strip()
    return websocket.headers.get("x-user")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "roomgate-lab"}


@app.get("/rooms")
async def list_rooms():
    """Public room catalog (helps discovery demos)."""
    return {
        "rooms": [
            {"id": "room-a", "owner": "user-a"},
            {"id": "room-b", "owner": "user-b"},
            {"id": "admin", "owner": "ops"},
        ]
    }


@app.websocket("/ws/room/{room_id}")
async def ws_open_room(websocket: WebSocket, room_id: str):
    """Open room — no authentication required (CWE-306)."""
    await websocket.accept()
    peers = _open_rooms.setdefault(room_id, set())
    peers.add(websocket)
    await websocket.send_json({
        "event": "joined",
        "room_id": room_id,
        "auth": "none",
    })
    try:
        while True:
            raw = await websocket.receive_text()
            await websocket.send_json({"ack": True, "room_id": room_id, "echo": raw})
    except WebSocketDisconnect:
        peers.discard(websocket)
        if not peers:
            _open_rooms.pop(room_id, None)


@app.websocket("/ws/secure/{room_id}")
async def ws_secure_room(websocket: WebSocket, room_id: str):
    """
    'Secure' room — requires a Bearer token, but does NOT check membership.
    Documented intent: user-a → room-a only; user-b → room-b only.
    Actual behavior: any valid token joins any room_id (BOLA / CWE-639).
    """
    token = _token_from_headers(websocket)
    if not token or token not in _MEMBERSHIP:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # BUG: membership for room_id is never checked against _MEMBERSHIP[token]
    await websocket.accept()
    peers = _secure_rooms.setdefault(room_id, set())
    peers.add(websocket)
    await websocket.send_json({
        "event": "joined",
        "room_id": room_id,
        "user": token,
        "auth": "bearer",
        # leak: server knows allowed rooms but still let them in
        "allowed_rooms": sorted(_MEMBERSHIP.get(token, set())),
    })
    try:
        while True:
            raw = await websocket.receive_text()
            await websocket.send_json({
                "ack": True,
                "room_id": room_id,
                "user": token,
                "echo": raw,
            })
    except WebSocketDisconnect:
        peers.discard(websocket)
        if not peers:
            _secure_rooms.pop(room_id, None)
