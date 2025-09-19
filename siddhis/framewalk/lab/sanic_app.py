#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sanic import Sanic
from sanic.response import html, json

app = Sanic("sanic_test_app")

@app.route("/")
async def index(request):
    return html("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sanic Test App</title>
    </head>
    <body>
        <h1>Hello from Sanic!</h1>
        <p>This is a minimal Sanic application for testing Framewalk.</p>
        <ul>
            <li><a href="/api/status">API Status</a></li>
            <li><a href="/about">About</a></li>
        </ul>
    </body>
    </html>
    """)

@app.route("/api/status")
async def api_status(request):
    return json({
        "status": "running",
        "framework": "sanic",
        "version": "21.12.0"
    })

@app.route("/about")
async def about(request):
    return html("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>About - Sanic</title>
    </head>
    <body>
        <h1>About Sanic</h1>
        <p>Sanic Framework Detection Test</p>
        <p>Sanic is a Python 3.7+ web server and web framework that's written to go fast.</p>
    </body>
    </html>
    """)

@app.route("/error")
async def trigger_error(request):
    # This will trigger a 404 error for testing
    raise Exception("Test error for framework detection")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True) 