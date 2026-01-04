#!/usr/bin/env python3
"""
CherryPy Test Application for Framework Detection
"""

import cherrypy
import os

class CherryPyTestApp:
    @cherrypy.expose
    def index(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CherryPy Test App</title>
        </head>
        <body>
            <h1>Hello from CherryPy!</h1>
            <p>CherryPy Framework Detection Test</p>
            <p>CherryPy is a pythonic, object-oriented HTTP framework.</p>
            <ul>
                <li><a href="/about">About</a></li>
                <li><a href="/api/status">API Status</a></li>
                <li><a href="/error">Test Error</a></li>
                <li><a href="/admin">Admin Interface</a></li>
            </ul>
        </body>
        </html>
        """.encode('utf-8')
    
    @cherrypy.expose
    def about(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>About - CherryPy Test App</title>
        </head>
        <body>
            <h1>About CherryPy</h1>
            <p>CherryPy is a pythonic, object-oriented HTTP framework.</p>
            <p>It allows developers to build web applications in much the same way they would build any other object-oriented Python program.</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """.encode('utf-8')
    
    @cherrypy.expose
    def api(self, status=None):
        if status == "status":
            cherrypy.response.headers['Content-Type'] = 'application/json'
            return '{"framework": "cherrypy", "status": "running", "version": "18.8.0"}'.encode('utf-8')
        return "API endpoint".encode('utf-8')
    
    @cherrypy.expose
    def error(self):
        # Trigger an error for testing
        raise cherrypy.HTTPError(500, "Test error for framework detection")
    
    @cherrypy.expose
    def admin(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CherryPy Admin</title>
        </head>
        <body>
            <h1>CherryPy Admin Interface</h1>
            <p>This is the CherryPy admin interface for testing.</p>
            <p>CherryPy admin features:</p>
            <ul>
                <li>Session management</li>
                <li>Configuration</li>
                <li>Logging</li>
            </ul>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """.encode('utf-8')

if __name__ == '__main__':
    # Configure CherryPy
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 8080,
        'server.thread_pool': 10,
        'tools.sessions.on': True,
        'tools.sessions.storage_type': 'file',
        'tools.sessions.storage_path': '/tmp/cherrypy_sessions',
        'log.screen': True,
        'log.access_file': '/tmp/cherrypy_access.log',
        'log.error_file': '/tmp/cherrypy_error.log'
    })
    
    # Mount the application
    cherrypy.quickstart(CherryPyTestApp(), '/') 