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

class SanicDetector(BaseDetector):
    """Sanic-specific detection methods (improved for specificity)"""
    
    FRAMEWORK = "Sanic"
    
    COMMON_PATHS = [
        '/api/status',
        '/error',
        '/about',
        '/health',
        '/metrics',
        '/docs',
        '/openapi.json',
        '/api/docs',
    ]
    
    ERROR_PATTERNS = [
        (r'SanicException', 'SanicException in error page', 30),
        (r'sanic_test_app', 'Sanic test app traceback', 30),
        (r'Sanic\s+\d+\.\d+\.\d+', 'Sanic version in error', 20),
        (r'sanic/app\.py', 'Sanic app.py in traceback', 25),
        (r'sanic.server', 'Sanic server in traceback', 20),
        (r'Exception: Test error for framework detection', 'Sanic test error', 20),
        (r'(?i)sanic', 'Sanic reference in error', 10),
    ]
    
    CONTENT_PATTERNS = [
        (r'Hello from Sanic!', 'Sanic greeting in content', 20),
        (r'<title>Sanic Test App</title>', 'Sanic test app title', 25),
        (r'<h1>Hello from Sanic!</h1>', 'Sanic heading in content', 20),
        (r'Sanic Framework Detection Test', 'Sanic detection test string', 20),
        (r'Sanic is a Python 3.7\+ web server', 'Sanic description', 15),
        (r'(?i)sanic', 'Sanic reference in HTML', 10),
    ]
    
    HEADER_PATTERNS = [
        ('server', r'uvicorn', 'Uvicorn server header (common for Sanic)', 5),
        ('content-type', r'application/json', 'JSON API response', 3),
    ]
    
    API_PATTERNS = [
        (r'"framework": ?"sanic"', 'Sanic framework in API response', 30),
        (r'"status": ?"running"', 'Status running in API response', 10),
        (r'"version": ?"[0-9.]+"', 'Version in API response', 10),
    ]
    
    def detect(self) -> None:
        evidence = set()
        evidence_types = set()
        # Check error page for Sanic-specific patterns
        if self._check_error_patterns(evidence, evidence_types):
            pass
        # Check API status endpoint for Sanic-specific JSON
        if self._check_api_status(evidence, evidence_types):
            pass
        # Check main page and about for Sanic content
        if self._check_content_patterns(evidence, evidence_types):
            pass
        # Check headers for Uvicorn and JSON
        if self._check_headers(evidence, evidence_types):
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
        strong_types = {'error', 'api', 'content'}
        strong_evidence = strong_types.intersection(evidence_types)
        if len(strong_evidence) >= 2:
            self._add_score(90, 'Composite', f"Sanic detected by: {sorted(strong_evidence)} | {sorted(evidence)}")
        elif 'error' in evidence_types and 'api' in evidence_types:
            self._add_score(70, 'Composite', f"Sanic error and API evidence: {sorted(evidence)}")
        elif 'error' in evidence_types:
            self._add_score(30, 'Error', f"Sanic error evidence: {sorted(evidence)}")
        elif 'api' in evidence_types:
            self._add_score(30, 'API', f"Sanic API evidence: {sorted(evidence)}")
        elif 'content' in evidence_types:
            self._add_score(20, 'Content', f"Sanic content evidence: {sorted(evidence)}")
        elif 'header' in evidence_types:
            self._add_score(10, 'Header', f"Sanic header evidence: {sorted(evidence)}")
        elif 'endpoint' in evidence_types:
            self._add_score(5, 'Endpoint', f"Sanic endpoint evidence: {sorted(evidence)}")
    
    def detect_version(self) -> None:
        base_url = self.request_manager.target_url.rstrip('/')
        api_url = urljoin(base_url, '/api/status')
        response = self.request_manager.make_request(api_url)
        if response:
            version_match = re.search(r'"version": ?"([0-9.]+)"', response.text)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(version, 80, f"Sanic version detected in API response: {version}") 