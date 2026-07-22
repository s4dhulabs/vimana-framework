# -*- coding: utf-8 -*-
"""
FastAPI WebSocket lab for framewire (post-handshake message fuzz).

Intentionally weak: echo accepts anything, rooms broadcast without isolation.
"""

from __future__ import annotations

import json
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Framewire Lab API",
    description="Vulnerable WebSocket message endpoints for framewire audits",
    version="1.0.0",
)

_WS_OPENAPI_PATHS = (
    "/ws/echo",
    "/ws/chat",
    "/ws/room/{room_id}",
)

_rooms: Dict[str, Set[WebSocket]] = {}


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
                "operationId": f"ws_{path.strip('/').replace('/', '_').replace('{', '').replace('}', '')}",
            }
        }
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _lab_openapi


@app.get("/health")
async def health():
    return {"status": "ok", "service": "framewire-lab"}


@app.websocket("/ws/echo")
async def ws_echo(websocket: WebSocket):
    """Blind echo — reflects any text/JSON without validation."""
    await websocket.accept()
    await websocket.send_json({"event": "connected", "channel": "echo"})
    try:
        while True:
            raw = await websocket.receive_text()
            # Reflect raw even if not valid JSON
            try:
                parsed = json.loads(raw)
                await websocket.send_json({"echo": parsed})
            except json.JSONDecodeError:
                await websocket.send_json({"echo": raw, "raw": True})
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """Chat echo — same weak validation as echo."""
    await websocket.accept()
    await websocket.send_json({"event": "connected", "channel": "chat"})
    try:
        while True:
            raw = await websocket.receive_text()
            await websocket.send_text(raw)
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/room/{room_id}")
async def ws_room(websocket: WebSocket, room_id: str):
    """Broadcast room — no auth, messages leak across sessions in same room."""
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
            await websocket.send_json({"ack": True, "room_id": room_id})
    except WebSocketDisconnect:
        peers.discard(websocket)
        if not peers:
            _rooms.pop(room_id, None)
