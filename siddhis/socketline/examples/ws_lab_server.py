#!/usr/bin/env python3
"""Lightweight aiohttp WS stub (port 18099). Prefer `vimana run --lab socketline` (port 18100)."""
import asyncio
from aiohttp import web


async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            await ws.send_str(msg.data)
    return ws


async def openapi(_):
    return web.json_response({
        'openapi': '3.1.0',
        'info': {'title': 'Socketline Lab', 'version': '1.0.0'},
        'paths': {
            '/ws/chat': {
                'get': {'summary': 'websocket upgrade', 'description': 'WebSocket chat'},
            },
        },
    })


app = web.Application()
app.router.add_get('/ws/chat', ws_handler)
app.router.add_get('/openapi.json', openapi)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=18099, print=lambda *a, **k: None)
