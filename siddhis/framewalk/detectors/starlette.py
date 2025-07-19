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

class StarletteDetector(BaseDetector):
    """Starlette-specific detection methods"""
    
    FRAMEWORK = "Starlette"
    
    COMMON_PATHS = [
        '/',
        '/about',
        '/api/status',
        '/error',
    ]
    
    CONTENT_PATTERNS = [
        (r'Starlette', 'Starlette reference in content', 20),
        (r'<title>Starlette Test App</title>', 'Starlette test app title', 25),
        (r'<h1>Hello from Starlette!</h1>', 'Starlette heading in content', 20),
        (r'Starlette Framework Detection Test', 'Starlette detection test string', 20),
        (r'Starlette is a lightweight ASGI framework', 'Starlette description', 15),
    ]
    
    HEADER_PATTERNS = [
        ('server', r'uvicorn', 'Uvicorn server header (common for Starlette)', 10),
        ('content-type', r'application/json', 'JSON API response', 5),
        ('content-type', r'text/html', 'HTML response', 3),
    ]
    
    API_PATTERNS = [
        (r'"framework": ?"starlette"', 'Starlette framework in API response', 30),
        (r'"status": ?"running"', 'Status running in API response', 10),
        (r'"version": ?"[0-9.]+"', 'Version in API response', 10),
    ]
    
    def detect(self) -> None:
        self._check_headers()
        self._check_content_patterns()
        self._check_api_status()
        self._check_common_paths()
        self.detect_version()
    
    def _add_score(self, points: int, evidence_type: str, detail: str, raw_data: Optional[Dict[str, Any]] = None) -> None:
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
    
    def _add_version_hint(self, version: str, confidence: int, evidence: str) -> None:
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
    
    def _add_component(self, component: str, evidence: str) -> None:
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
                    self._add_score(confidence, 'Header', f"{description}: {header_name}: {header_value}")
    
    def _check_content_patterns(self) -> None:
        response = self.request_manager.make_request()
        if not response:
            return
        for pattern, description, confidence in self.CONTENT_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                self._add_score(confidence, 'Content', f"{description}: {pattern}")
    
    def _check_api_status(self) -> None:
        base_url = self.request_manager.target_url.rstrip('/')
        api_url = urljoin(base_url, '/api/status')
        response = self.request_manager.make_request(api_url)
        if not response:
            return
        for pattern, description, confidence in self.API_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                self._add_score(confidence, 'API', f"{description}: {pattern}")
        if response.headers.get('content-type', '').startswith('application/json'):
            self._add_score(10, 'API', 'API status endpoint returns JSON')
    
    def _check_common_paths(self) -> None:
        base_url = self.request_manager.target_url.rstrip('/')
        for path in self.COMMON_PATHS:
            url = urljoin(base_url, path)
            response = self.request_manager.make_request(url)
            if response and response.status_code == 200:
                self._add_score(5, 'Endpoint', f"{path} returns 200 OK")
    
    def detect_version(self) -> None:
        base_url = self.request_manager.target_url.rstrip('/')
        api_url = urljoin(base_url, '/api/status')
        response = self.request_manager.make_request(api_url)
        if response:
            version_match = re.search(r'"version": ?"([0-9.]+)"', response.text)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(version, 80, f"Starlette version detected in API response: {version}") 