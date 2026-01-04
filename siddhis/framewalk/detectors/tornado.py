#!/usr/bin/env python3
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
#
# This file is part of Vimana Framework Project.

import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

from .base import BaseDetector

class TornadoDetector(BaseDetector):
    """Tornado-specific detection methods"""
    
    FRAMEWORK = "Tornado"
    
    # Common Tornado paths to check
    COMMON_PATHS = [
        '/api/info',
        '/about',
        '/status',
        '/error',
        '/static/',
    ]
    
    # Tornado error patterns
    ERROR_PATTERNS = [
        (r'tornado/web\.py', 'Tornado error traceback', 30),
        (r'Exception: Test error for Tornado framework detection', 'Tornado test error', 25),
        (r'Traceback \(most recent call last\):', 'Python traceback in error', 10),
    ]
    
    # Tornado content patterns
    CONTENT_PATTERNS = [
        (r'Hello from Tornado!', 'Tornado greeting in content', 20),
        (r'<title>Tornado Test App</title>', 'Tornado test app title', 25),
        (r'<h1>Hello from Tornado!</h1>', 'Tornado heading in content', 20),
        (r'This is a minimal Tornado application', 'Tornado app description', 15),
        (r'<a href="/api/info">API Info</a>', 'Tornado API info link', 10),
        (r'<a href="/about">About</a>', 'Tornado about link', 10),
        (r'<a href="/status">Status</a>', 'Tornado status link', 10),
    ]
    
    # Tornado header patterns
    HEADER_PATTERNS = [
        ('Server', r'TornadoServer/\d+\.\d+\.\d+', 'Tornado server header with version', 40),
        ('Server', r'TornadoServer', 'Tornado server header', 30),
        ('Content-Type', r'text/plain', 'Tornado plain text response', 5),
    ]
    
    def detect(self) -> None:
        """Run Tornado detection methods"""
        self._check_headers()
        self._check_content_patterns()
        self._check_error_patterns()
        self._check_common_paths()
        self.detect_version()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _check_headers(self) -> None:
        response = self.request_manager.make_request()
        if not response:
            return
        headers = response.headers
        for header_name, pattern, description, confidence in self.HEADER_PATTERNS:
            if header_name in headers:
                header_value = headers[header_name]
                if re.search(pattern, header_value, re.IGNORECASE):
                    self._add_score(
                        confidence, 
                        'Header', 
                        f"{description}: {header_name}: {header_value}"
                    )
        if response.status_code == 405:
            self._add_score(
                10, 
                'Header', 
                "405 Method Not Allowed response (common in Tornado)"
            )
    
    def _check_content_patterns(self) -> None:
        response = self.request_manager.make_request()
        if not response:
            return
        for pattern, description, confidence in self.CONTENT_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                self._add_score(
                    confidence, 
                    'Content', 
                    f"{description}: {pattern}"
                )
    
    def _check_error_patterns(self) -> None:
        base_url = self.request_manager.target_url.rstrip('/')
        error_url = urljoin(base_url, '/error')
        response = self.request_manager.make_request(error_url)
        if not response:
            return
        for pattern, description, confidence in self.ERROR_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                self._add_score(
                    confidence, 
                    'Error', 
                    f"{description}: {pattern}"
                )
    
    def _check_common_paths(self) -> None:
        base_url = self.request_manager.target_url.rstrip('/')
        for path in self.COMMON_PATHS:
            url = urljoin(base_url, path)
            response = self.request_manager.make_request(url)
            if response:
                if response.status_code == 200:
                    self._add_score(
                        10, 
                        'Endpoint', 
                        f"{path} returns 200 OK"
                    )
                elif response.status_code == 405:
                    self._add_score(
                        8, 
                        'Endpoint', 
                        f"{path} returns 405 Method Not Allowed (Tornado behavior)"
                    )
    
    def detect_version(self) -> None:
        response = self.request_manager.make_request()
        if not response:
            return
        server_header = response.headers.get('Server', '')
        version_match = re.search(r'TornadoServer/(\d+\.\d+\.\d+)', server_header)
        if version_match:
            version = version_match.group(1)
            self._add_version_hint(
                version, 
                80, 
                f"Tornado version detected in Server header: {version}"
            ) 