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

class CherryPyDetector(BaseDetector):
    """CherryPy-specific detection methods"""
    
    FRAMEWORK = "CherryPy"
    
    COMMON_PATHS = [
        '/admin',
        '/api/status',
        '/about',
        '/error',
        '/tools',
        '/config',
        '/sessions',
    ]
    
    ERROR_PATTERNS = [
        (r'cherrypy\.HTTPError', 'CherryPy HTTPError in error page', 40),
        (r'cherrypy\.lib\.cptools', 'CherryPy tools in error traceback', 35),
        (r'cherrypy\.wsgiserver', 'CherryPy WSGI server in error', 30),
        (r'cherrypy\._cperror', 'CherryPy error module in traceback', 30),
        (r'cherrypy\.expose', 'CherryPy expose decorator in error', 25),
        (r'cherrypy\.quickstart', 'CherryPy quickstart in error', 25),
        (r'cherrypy\.config', 'CherryPy config in error', 20),
        (r'(?i)cherrypy', 'CherryPy reference in error', 15),
    ]
    
    CONTENT_PATTERNS = [
        (r'Hello from CherryPy!', 'CherryPy greeting in content', 30),
        (r'<title>CherryPy Test App</title>', 'CherryPy test app title', 25),
        (r'<h1>Hello from CherryPy!</h1>', 'CherryPy heading in content', 25),
        (r'CherryPy Framework Detection Test', 'CherryPy detection test string', 25),
        (r'CherryPy is a pythonic, object-oriented HTTP framework', 'CherryPy description', 20),
        (r'CherryPy Admin Interface', 'CherryPy admin interface title', 30),
        (r'cherrypy\.quickstart', 'CherryPy quickstart in content', 20),
        (r'(?i)cherrypy', 'CherryPy reference in HTML', 15),
    ]
    
    HEADER_PATTERNS = [
        ('server', r'cherrypy', 'CherryPy server header', 40),
        ('x-powered-by', r'cherrypy', 'CherryPy X-Powered-By header', 35),
        ('content-type', r'application/json', 'JSON API response', 5),
    ]
    
    API_PATTERNS = [
        (r'"framework": ?"cherrypy"', 'CherryPy framework in API response', 40),
        (r'"status": ?"running"', 'Status running in API response', 10),
        (r'"version": ?"[0-9.]+"', 'Version in API response', 10),
    ]
    
    SESSION_PATTERNS = [
        (r'session_id', 'CherryPy session cookie pattern', 25),
        (r'cherrypy_session', 'CherryPy session cookie', 30),
    ]
    
    def detect(self) -> None:
        evidence = set()
        evidence_types = set()
        
        # Check error page for CherryPy-specific patterns
        if self._check_error_patterns(evidence, evidence_types):
            pass
        
        # Check API status endpoint for CherryPy-specific JSON
        if self._check_api_status(evidence, evidence_types):
            pass
        
        # Check main page and about for CherryPy content
        if self._check_content_patterns(evidence, evidence_types):
            pass
        
        # Check headers for CherryPy server and X-Powered-By
        if self._check_headers(evidence, evidence_types):
            pass
        
        # Check for CherryPy session cookies
        if self._check_session_patterns(evidence, evidence_types):
            pass
        
        # Check common paths for 200 OK (low confidence)
        self._check_common_paths(evidence, evidence_types)
        
        # Assign confidence based on evidence
        self._score_evidence(evidence, evidence_types)
        self.detect_version()
    
    def _add_score(self, points: int, evidence_type: str, detail: str, raw_data: Optional[Dict[str, Any]] = None) -> None:
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
    
    def _add_version_hint(self, version: str, confidence: int, evidence: str) -> None:
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
    
    def _add_component(self, component: str, evidence: str) -> None:
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
    
    def _check_headers(self, evidence, evidence_types) -> bool:
        response = self.request_manager.make_request()
        if not response:
            return False
        headers = response.headers
        found = False
        for header_name, pattern, description, confidence in self.HEADER_PATTERNS:
            if header_name in headers:
                header_value = headers[header_name]
                if re.search(pattern, header_value, re.IGNORECASE):
                    evidence.add(f"Header: {description}")
                    evidence_types.add('header')
                    found = True
        return found
    
    def _check_content_patterns(self, evidence, evidence_types) -> bool:
        response = self.request_manager.make_request()
        if not response:
            return False
        found = False
        for pattern, description, confidence in self.CONTENT_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                evidence.add(f"Content: {description}")
                evidence_types.add('content')
                found = True
        return found
    
    def _check_error_patterns(self, evidence, evidence_types) -> bool:
        base_url = self.request_manager.target_url.rstrip('/')
        error_url = urljoin(base_url, '/error')
        response = self.request_manager.make_request(error_url)
        if not response:
            return False
        found = False
        for pattern, description, confidence in self.ERROR_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                evidence.add(f"Error: {description}")
                evidence_types.add('error')
                found = True
        return found
    
    def _check_api_status(self, evidence, evidence_types) -> bool:
        base_url = self.request_manager.target_url.rstrip('/')
        api_url = urljoin(base_url, '/api/status')
        response = self.request_manager.make_request(api_url)
        if not response:
            return False
        found = False
        for pattern, description, confidence in self.API_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                evidence.add(f"API: {description}")
                evidence_types.add('api')
                found = True
        if response.headers.get('content-type', '').startswith('application/json'):
            evidence.add("API: JSON API response detected")
            evidence_types.add('api')
            found = True
        return found
    
    def _check_session_patterns(self, evidence, evidence_types) -> bool:
        response = self.request_manager.make_request()
        if not response:
            return False
        found = False
        cookies = response.cookies
        for name, value in cookies.items():
            for pattern, description, confidence in self.SESSION_PATTERNS:
                if re.search(pattern, name, re.IGNORECASE):
                    evidence.add(f"Session: {description}")
                    evidence_types.add('session')
                    found = True
        return found
    
    def _check_common_paths(self, evidence, evidence_types):
        base_url = self.request_manager.target_url.rstrip('/')
        for path in self.COMMON_PATHS:
            url = urljoin(base_url, path)
            response = self.request_manager.make_request(url)
            if response and response.status_code == 200:
                # Only add as low confidence evidence
                evidence.add(f"Endpoint: {path} returns 200 OK")
                evidence_types.add('endpoint')
    
    def _score_evidence(self, evidence, evidence_types):
        # High confidence: at least 2 unique types of strong evidence
        strong_types = {'error', 'api', 'content', 'header', 'session'}
        strong_evidence = strong_types.intersection(evidence_types)
        
        if len(strong_evidence) >= 3:
            self._add_score(95, 'Composite', f"CherryPy detected by: {sorted(strong_evidence)} | {sorted(evidence)}")
        elif len(strong_evidence) >= 2:
            self._add_score(85, 'Composite', f"CherryPy detected by: {sorted(strong_evidence)} | {sorted(evidence)}")
        elif 'header' in evidence_types and 'content' in evidence_types:
            self._add_score(75, 'Composite', f"CherryPy header and content evidence: {sorted(evidence)}")
        elif 'error' in evidence_types:
            self._add_score(40, 'Error', f"CherryPy error evidence: {sorted(evidence)}")
        elif 'header' in evidence_types:
            self._add_score(35, 'Header', f"CherryPy header evidence: {sorted(evidence)}")
        elif 'session' in evidence_types:
            self._add_score(30, 'Session', f"CherryPy session evidence: {sorted(evidence)}")
        elif 'api' in evidence_types:
            self._add_score(25, 'API', f"CherryPy API evidence: {sorted(evidence)}")
        elif 'content' in evidence_types:
            self._add_score(20, 'Content', f"CherryPy content evidence: {sorted(evidence)}")
        elif 'endpoint' in evidence_types:
            self._add_score(10, 'Endpoint', f"CherryPy endpoint evidence: {sorted(evidence)}")
    
    def detect_version(self) -> None:
        # Try to detect version from server header
        response = self.request_manager.make_request()
        if response and 'server' in response.headers:
            server_header = response.headers['server']
            version_match = re.search(r'cherrypy[/\s]+(\d+\.\d+\.\d+)', server_header, re.IGNORECASE)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(version, 80, f"CherryPy version detected in server header: {version}")
        
        # Try to detect version from API response
        base_url = self.request_manager.target_url.rstrip('/')
        api_url = urljoin(base_url, '/api/status')
        response = self.request_manager.make_request(api_url)
        if response:
            version_match = re.search(r'"version": ?"([0-9.]+)"', response.text)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(version, 85, f"CherryPy version detected in API response: {version}") 