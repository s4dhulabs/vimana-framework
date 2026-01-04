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
from typing import Dict, List, Any, Optional, Set

from .base import BaseEngine


class HeaderEngine(BaseEngine):
    """Engine for analyzing HTTP headers for framework fingerprints"""
    
    def analyze(self) -> None:
        """Run header analysis"""
        self._analyze_response_headers()
        self._check_security_headers()
        self._analyze_server_header()
        self._analyze_set_cookie()
        
    def _analyze_response_headers(self) -> None:
        """Analyze response headers for framework indicators"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        headers = response.headers
        
        # Track all headers for patterns
        for name, value in headers.items():
            name_lower = name.lower()
            value_lower = str(value).lower()
            
            # Framework-specific headers
            self._check_framework_headers(name_lower, value_lower)
            
            # WSGI/ASGI server indicators
            self._check_server_indicators(name_lower, value_lower)
            
    def _check_framework_headers(self, name: str, value: str) -> None:
        """Check for framework-specific headers"""
        # Django indicators
        if 'django' in value:
            self._add_score('Django', 10, 'Header', f"Header contains Django reference: {name}")
            
        # Flask/Werkzeug indicators
        if any(x in value for x in ['flask', 'werkzeug']):
            self._add_score('Flask', 10, 'Header', f"Header contains Flask/Werkzeug reference: {name}")
            
            # Check for Werkzeug version
            werkzeug_match = re.search(r'werkzeug/(\d+\.\d+\.\d+)', value)
            if werkzeug_match:
                werkzeug_version = werkzeug_match.group(1)
                self._add_version_hint(
                    'Flask', 
                    f"Werkzeug {werkzeug_version}", 
                    8, 
                    f"Werkzeug version in header: {werkzeug_version}"
                )
                
        # FastAPI/Starlette indicators
        if any(x in value for x in ['fastapi', 'starlette']):
            self._add_score('FastAPI', 10, 'Header', f"Header contains FastAPI/Starlette reference: {name}")
            
        # Pyramid indicators
        if 'pyramid' in value:
            self._add_score('Pyramid', 10, 'Header', f"Header contains Pyramid reference: {name}")
            
        # Bottle indicators
        if 'bottle' in value:
            self._add_score('Bottle', 10, 'Header', f"Header contains Bottle reference: {name}")
            
        # General Python indicators
        if 'python' in value:
            # Add a small score to all Python frameworks
            frameworks = ['Django', 'Flask', 'FastAPI', 'Pyramid', 'Bottle']
            for framework in frameworks:
                self._add_score(framework, 1, 'Header', f"Header contains Python reference: {name}")
                
    def _check_server_indicators(self, name: str, value: str) -> None:
        """Check for WSGI/ASGI server indicators"""
        # Common WSGI/ASGI servers
        servers = {
            'gunicorn': ('WSGI server', 2),
            'uvicorn': ('ASGI server', 3),
            'daphne': ('ASGI server', 3),
            'hypercorn': ('ASGI server', 3),
            'waitress': ('WSGI server', 2),
            'nginx': ('Web server', 1),
            'apache': ('Web server', 1),
        }
        
        for server, (server_type, score) in servers.items():
            if server in value:
                # Add to server info
                server_version = self._extract_version(value, server)
                self.result_manager.add_server_info(server, server_version)
                
                # Add score to potential frameworks
                if server in ['uvicorn', 'daphne', 'hypercorn']:
                    self._add_score('FastAPI', score, 'Server', f"{server_type} detected: {server}")
                    self._add_score('Django', score - 1, 'Server', f"{server_type} detected: {server}")
                elif server in ['gunicorn', 'waitress']:
                    self._add_score('Django', score, 'Server', f"{server_type} detected: {server}")
                    self._add_score('Flask', score, 'Server', f"{server_type} detected: {server}")
                    
    def _extract_version(self, header_value: str, server_name: str) -> Optional[str]:
        """Extract version from header value"""
        version_match = re.search(rf'{server_name}[/\s]+(\d+\.\d+\.\d+)', header_value, re.IGNORECASE)
        if version_match:
            return version_match.group(1)
        return None
        
    def _check_security_headers(self) -> None:
        """Check for standard security headers"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        headers = response.headers
        security_headers = {
            'strict-transport-security': 'HSTS',
            'content-security-policy': 'CSP',
            'x-content-type-options': 'X-Content-Type-Options',
            'x-frame-options': 'X-Frame-Options',
            'x-xss-protection': 'X-XSS-Protection',
            'referrer-policy': 'Referrer-Policy',
            'permissions-policy': 'Permissions-Policy',
            'cross-origin-embedder-policy': 'COEP',
            'cross-origin-opener-policy': 'COOP',
            'cross-origin-resource-policy': 'CORP',
        }
        
        # Check for present headers
        for header_key, header_name in security_headers.items():
            if header_key in headers:
                self.result_manager.add_security_header(
                    header_name, 
                    present=True, 
                    value=headers[header_key]
                )
            else:
                self.result_manager.add_security_header(header_name, present=False)
                
        # Django security headers
        if 'x-frame-options' in headers and headers['x-frame-options'].upper() == 'SAMEORIGIN':
            self._add_score('Django', 2, 'Security Header', "Django default X-Frame-Options: SAMEORIGIN")
            
        # Check CSP header format
        if 'content-security-policy' in headers:
            csp = headers['content-security-policy']
            # Django usually has specific CSP structure
            if "frame-ancestors 'self'" in csp:
                self._add_score('Django', 2, 'Security Header', "Django-like CSP frame-ancestors directive")
                
    def _analyze_server_header(self) -> None:
        """Analyze the Server header in detail"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        if 'server' in response.headers:
            server = response.headers['server']
            
            # Extract server info
            self._check_server_indicators('server', server.lower())
            
            # Check for Python version leakage
            python_match = re.search(r'python[/\s]+(\d+\.\d+\.\d+)', server, re.IGNORECASE)
            if python_match:
                python_version = python_match.group(1)
                frameworks = ['Django', 'Flask', 'FastAPI', 'Pyramid', 'Bottle']
                for framework in frameworks:
                    self._add_score(
                        framework, 
                        2, 
                        'Server', 
                        f"Python version leak: {python_version}"
                    )
                    
    def _analyze_set_cookie(self) -> None:
        """Analyze Set-Cookie headers for framework fingerprints"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        cookies = response.cookies
        
        # Django session cookie
        if 'sessionid' in cookies:
            self._add_score('Django', 8, 'Cookie', "Django session cookie detected")
            self._add_component('Django', 'Django Sessions', "sessionid cookie")
            
        # Django CSRF cookie
        if 'csrftoken' in cookies:
            self._add_score('Django', 8, 'Cookie', "Django CSRF cookie detected")
            
            # Analyze CSRF token format for version hints
            csrf_token = cookies['csrftoken']
            if csrf_token:
                if len(str(csrf_token)) == 64:  # Django 1.10+
                    self._add_version_hint(
                        'Django', 
                        '1.10+', 
                        5, 
                        "64-character CSRF token length"
                    )
                elif len(str(csrf_token)) == 32:  # Django 1.4 - 1.9
                    self._add_version_hint(
                        'Django', 
                        '1.4-1.9', 
                        5, 
                        "32-character CSRF token length"
                    )
                    
        # Flask session cookie
        if 'session' in cookies:
            self._add_score('Flask', 6, 'Cookie', "Flask session cookie detected")
            
        # Sanic cookie
        if any(cookie.startswith('sanic') for cookie in cookies.keys()):
            self._add_score('Sanic', 8, 'Cookie', "Sanic cookie detected")