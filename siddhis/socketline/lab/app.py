# -*- coding: utf-8 -*-
"""
FastAPI WebSocket lab for socketline testing.

Intentionally weak WS security: open handshake, no auth, permissive origin.
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Socketline Lab API",
    description="Vulnerable WebSocket endpoints for socketline audits",
    version="1.0.0",
)

_WS_OPENAPI_PATHS = (
    "/ws/chat",
    "/ws/room/{room_id}",
    "/ws/admin",
    "/ws/events",
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
    for path in _WS_OPENAPI_PATHS:
        schema.setdefault("paths", {})[path] = {
            "get": {
                "summary": f"WebSocket endpoint {path}",
                "description": "HTTP GET upgrades to WebSocket connection",
                "operationId": f"ws_{path.strip('/').replace('/', '_')}",
            }
        }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _lab_openapi

# In-memory rooms — cross-session leakage if clients join same room without auth
_rooms: Dict[str, Set[WebSocket]] = {}
_messages: list[str] = []


@app.get("/health")
async def health():
    return {"status": "ok", "service": "socketline-lab"}


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """Open chat — accepts any origin, no auth token."""
    await websocket.accept()
    await websocket.send_json({"event": "connected", "channel": "chat"})
    try:
        while True:
            raw = await websocket.receive_text()
            _messages.append(raw)
            await websocket.send_json({"echo": raw, "room": "chat"})
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/room/{room_id}")
async def ws_room(websocket: WebSocket, room_id: str):
    """Multi-client room — no membership checks."""
    await websocket.accept()
    peers = _rooms.setdefault(room_id, set())
    peers.add(websocket)
    await websocket.send_json({"event": "joined", "room_id": room_id})
    try:
        while True:
            raw = await websocket.receive_text()
            for peer in list(peers):
                if peer is not websocket:
                    try:
                        await peer.send_text(raw)
                    except Exception:
                        peers.discard(peer)
            await websocket.send_json({"broadcast": raw, "room_id": room_id})
    except WebSocketDisconnect:
        peers.discard(websocket)
        if not peers:
            _rooms.pop(room_id, None)


@app.websocket("/ws/admin")
async def ws_admin(websocket: WebSocket):
    """Admin channel — should require auth but does not."""
    await websocket.accept()
    await websocket.send_json({
        "event": "admin",
        "secret": "lab-only-not-for-production",
        "users": ["admin", "guest"],
    })
    try:
        while True:
            cmd = await websocket.receive_text()
            if cmd.strip().lower() == "dump":
                await websocket.send_json({"messages": _messages[-50:]})
            else:
                await websocket.send_json({"ack": cmd})
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    """SSE-like push over WS — no subprotocol negotiation."""
    await websocket.accept()
    for i in range(5):
        await websocket.send_json({"seq": i, "type": "tick"})
        await asyncio.sleep(0.5)
    await websocket.close()
