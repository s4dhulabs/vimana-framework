# -*- coding: utf-8 -*-
"""
Flask SSRF lab for fetchbane.

- Local canary HTTP server on 127.0.0.1:9999/secret
- /preview?url=  — blind fetch, reflects body
- /webhook       — POST JSON {"url": ...}
- /fetch         — weak allowlist (*.example.com) with bypassable checks
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

CANARY_MARKER = 'FETCHBANE_CANARY_SECRET'
app = Flask(__name__)


class _CanaryHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split('?', 1)[0] in ('/secret', '/'):
            body = CANARY_MARKER.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def _start_canary():
    server = HTTPServer(('127.0.0.1', 9999), _CanaryHandler)
    server.serve_forever()


threading.Thread(target=_start_canary, daemon=True).start()


def _fetch(url: str, timeout: float = 5.0) -> dict:
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        return {
            'ok': True,
            'status': resp.status_code,
            'fetched': resp.text[:2000],
            'url': url,
        }
    except Exception as exc:
        return {'ok': False, 'error': str(exc), 'url': url}


@app.get('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'fetchbane-lab'})


@app.get('/openapi.json')
def openapi():
    return jsonify({
        'openapi': '3.0.3',
        'info': {
            'title': 'Fetchbane Lab API',
            'description': 'Vulnerable URL-fetch endpoints for SSRF audits',
            'version': '1.0.0',
        },
        'paths': {
            '/preview': {
                'get': {
                    'summary': 'Preview remote URL (SSRF)',
                    'operationId': 'preview_url',
                    'parameters': [{
                        'name': 'url',
                        'in': 'query',
                        'required': True,
                        'schema': {'type': 'string'},
                    }],
                },
            },
            '/webhook': {
                'post': {
                    'summary': 'Webhook fetch (SSRF)',
                    'operationId': 'webhook_fetch',
                },
            },
            '/fetch': {
                'get': {
                    'summary': 'Allowlisted fetch (broken)',
                    'operationId': 'allowlist_fetch',
                },
            },
            '/health': {'get': {'summary': 'Health', 'operationId': 'health'}},
        },
    })


@app.get('/preview')
def preview():
    """Intentionally vulnerable: fetches any URL and reflects body."""
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'url required'}), 400
    return jsonify(_fetch(url))


@app.post('/webhook')
def webhook():
    data = request.get_json(silent=True) or {}
    url = data.get('url') or data.get('target') or ''
    if not url:
        return jsonify({'error': 'url required'}), 400
    return jsonify(_fetch(url))


@app.get('/fetch')
def allowlist_fetch():
    """
    Broken allowlist: host must 'end with' example.com — bypass via userinfo
    or other tricks (e.g. http://127.0.0.1:9999/secret@example.com is NOT used;
    we check netloc endswith example.com only after naive parse).
    """
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'url required'}), 400
    parsed = urlparse(url)
    host = parsed.hostname or ''
    # Intentionally weak: only checks string endswith on netloc (userinfo tricks)
    netloc = parsed.netloc or ''
    if not (netloc.endswith('example.com') or host.endswith('example.com')):
        # Still allow if 'example.com' appears anywhere in netloc (extra weak)
        if 'example.com' not in netloc:
            return jsonify({'error': 'host not allowlisted', 'host': host}), 403
    return jsonify(_fetch(url))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
