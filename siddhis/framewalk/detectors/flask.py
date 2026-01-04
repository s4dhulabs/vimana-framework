#!/usr/bin/env python3
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
#
# This file is part of Vimana Framework Project.

import re
from typing import Dict, List, Any, Optional

from .base import BaseDetector


class FlaskDetector(BaseDetector):
    """Flask-specific detection methods"""
    
    FRAMEWORK = "Flask"
    
    def detect(self) -> None:
        """Run Flask detection methods"""
        self._check_headers()
        self._check_werkzeug_debugger()
        self._check_common_flask_paths()
        self._check_flask_content()
        self._check_flask_error_page()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """Add score for Flask"""
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """Add version hint for Flask"""
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """Add component for Flask"""
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _check_headers(self) -> None:
        """Check for Flask-specific headers"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        headers = response.headers
        
        # Check for Werkzeug in server header
        if 'server' in headers and 'werkzeug' in headers['server'].lower():
            self._add_score(
                10, 
                'Header', 
                f"Server header contains Werkzeug: {headers['server']}"
            )
            
            # Try to extract version
            version_match = re.search(r'werkzeug/(\d+\.\d+\.\d+)', headers['server'], re.IGNORECASE)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(
                    f"Werkzeug {version}", 
                    8, 
                    f"Werkzeug version in server header: {version}"
                )
            
        # Check for Flask-specific headers
        for name, value in headers.items():
            if 'flask' in value.lower():
                self._add_score(
                    8, 
                    'Header', 
                    f"{name} header contains Flask reference: {value}"
                )
                
    def _check_werkzeug_debugger(self) -> None:
        """Check for Werkzeug debugger console and debug pages"""
        # Check console path
        response = self.request_manager.make_request('/console')
        if response and response.status_code == 200:
            content = response.text.lower()
            if 'werkzeug debugger' in content or 'interactive console' in content:
                self._add_score(
                    15, 
                    'Debug', 
                    "Werkzeug debugger console found at /console"
                )
                self._add_component(
                    "Werkzeug Debugger", 
                    "Interactive console found"
                )
                
                # Check for DON'T PANIC message
                if "don't panic" in content:
                    self._add_score(
                        5, 
                        'Debug', 
                        "Werkzeug 'DON'T PANIC' message found"
                    )
                    
        # Check debug page
        response = self.request_manager.make_request('/this_should_not_exist_12345')
        if response:
            content = response.text.lower()
            if 'werkzeug' in content and ('traceback' in content or 'debugger' in content):
                self._add_score(
                    12, 
                    'Debug', 
                    "Werkzeug debugger traceback found on 404 page"
                )
                self._add_component(
                    "Werkzeug Debugger", 
                    "Debug traceback on error page"
                )
                
                # Try to extract version
                version_match = re.search(r'werkzeug/(\d+\.\d+\.\d+)', content)
                if version_match:
                    version = version_match.group(1)
                    self._add_version_hint(
                        f"Werkzeug {version}", 
                        8, 
                        f"Werkzeug version in debug page: {version}"
                    )
                    
    def _check_common_flask_paths(self) -> None:
        """Check for common Flask-specific paths"""
        paths = [
            '/static/',
            '/.well-known/security.txt',  # Often exposed in Flask apps
            '/flask-static/',
            '/api/',  # Common API prefix
            '/swagger/',  # Common for Flask REST APIs
            '/docs/',
            '/api/docs/',
        ]
        
        for path in paths:
            response = self.request_manager.make_request(path)
            if not response:
                continue
                
            if response.status_code == 200:
                self._add_score(
                    4, 
                    'Path', 
                    f"Common Flask path exists: {path}"
                )
                
                # Check for Flask-specific content
                if path == '/static/' and response.headers.get('content-type', '').startswith('text/directory'):
                    self._add_score(
                        6, 
                        'Path', 
                        "Flask static directory listing"
                    )
                    
    def _check_flask_content(self) -> None:
        """Check for Flask-specific content in the response"""
        response = self.request_manager.make_request()
        if not response or not response.text:
            return
            
        content = response.text.lower()
        
        # Check for Flask references
        flask_patterns = [
            ('flask', 5, "Flask reference in HTML"),
            ('jinja', 5, "Jinja template reference in HTML"),
            ('werkzeug', 5, "Werkzeug reference in HTML"),
            ('itsdangerous', 5, "itsdangerous reference in HTML"),
            ('flask-wtf', 6, "Flask-WTF form library reference"),
            ('flask-login', 6, "Flask-Login reference in HTML"),
            ('flask-sqlalchemy', 6, "Flask-SQLAlchemy reference in HTML"),
            ('flask-restful', 6, "Flask-RESTful reference in HTML"),
            ('flask-jwt', 6, "Flask-JWT reference in HTML"),
        ]
        
        for pattern, points, detail in flask_patterns:
            if pattern in content:
                self._add_score(points, 'Content', detail)
                
                # Add components
                if pattern.startswith('flask-'):
                    component_name = pattern.replace('-', ' ').title()
                    self._add_component(component_name, f"{component_name} reference in HTML")
                    
        # Look for common Flask HTML patterns
        if ('<form' in content and 'csrf_token' in content) or \
           ('method="post"' in content and 'csrf_token' in content):
            self._add_score(6, 'Content', "Flask WTForms CSRF token")
            self._add_component("Flask-WTF", "CSRF token in form")
            
        # Check for common Flask error patterns
        if 'the server encountered an internal error' in content and \
           ('werkzeug' in content or 'flask' in content):
            self._add_score(8, 'Error', "Flask default error page")
            
    def _check_flask_error_page(self) -> None:
        """Check for Flask-specific error pages"""
        # Trigger a server error with an invalid method
        response = self.request_manager.make_request(method="INVALID")
        if not response:
            # Try a different approach - request a page that's likely to 500
            response = self.request_manager.make_request('/?error=true')
            
        if response and response.status_code >= 400:
            content = response.text.lower()
            
            if 'werkzeug' in content or 'flask' in content:
                self._add_score(6, 'Error', "Flask error page detected")
                
            # Check for other Flask-specific error patterns
            if 'the requested url was not found' in content:
                self._add_score(8, 'Error', "Flask 404 error page")
                
            if 'method not allowed' in content:
                self._add_score(8, 'Error', "Flask 405 error page")