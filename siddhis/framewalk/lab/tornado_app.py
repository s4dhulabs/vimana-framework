#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
import json

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Tornado Test App</title>
        </head>
        <body>
            <h1>Hello from Tornado!</h1>
            <p>This is a minimal Tornado application for testing Framewalk.</p>
            <ul>
                <li><a href="/api/info">API Info</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/status">Status</a></li>
            </ul>
        </body>
        </html>
        """)

class ApiInfoHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
            "framework": "tornado",
            "version": "6.1",
            "status": "running",
            "description": "Tornado web framework"
        }))

class AboutHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>About - Tornado</title>
        </head>
        <body>
            <h1>About Tornado</h1>
            <p>Tornado Framework Detection Test</p>
            <p>Tornado is a Python web framework and asynchronous networking library.</p>
        </body>
        </html>
        """)

class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
            "status": "ok",
            "framework": "tornado"
        }))

class ErrorHandler(tornado.web.RequestHandler):
    def get(self):
        # This will trigger an error for testing
        raise Exception("Test error for Tornado framework detection")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/api/info", ApiInfoHandler),
        (r"/about", AboutHandler),
        (r"/status", StatusHandler),
        (r"/error", ErrorHandler),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8080, address="0.0.0.0")
    print("Tornado server starting on port 8080...")
    tornado.ioloop.IOLoop.current().start() 