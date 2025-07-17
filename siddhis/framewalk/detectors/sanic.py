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
from urllib.parse import urljoin

from .base import BaseDetector


class SanicDetector(BaseDetector):
    """Sanic-specific detection methods"""
    
    FRAMEWORK = "Sanic"
    
    # Common Sanic paths to check
    COMMON_PATHS = [
        '/api/status',
        '/about',
        '/error',
        '/health',
        '/metrics',
        '/docs',
        '/openapi.json',
        '/api/docs',
    ]
    
    # Sanic error patterns
    ERROR_PATTERNS = [
        # Pattern, Description, Confidence
        (r'⚠️ \d+ — [^=]+', 'Sanic error page format', 25),
        (r'Traceback of \w+_test_app', 'Sanic test app traceback', 30),
        (r'Exception: [^=]+ while handling path', 'Sanic exception handling', 25),
        (r'File /usr/local/lib/python3\.9/site-packages/sanic/app\.py', 'Sanic app.py reference', 35),
        (r'==============================', 'Sanic error separator', 15),
        (r'Exception: Test error for framework detection', 'Sanic test error', 20),
    ]
    
    # Sanic content patterns
    CONTENT_PATTERNS = [
        # Pattern, Description, Confidence
        (r'Hello from Sanic!', 'Sanic greeting in content', 20),
        (r'<title>Sanic Test App</title>', 'Sanic test app title', 25),
        (r'<h1>Hello from Sanic!</h1>', 'Sanic heading in content', 20),
        (r'This is a minimal Sanic application', 'Sanic app description', 15),
        (r'<a href="/api/status">API Status</a>', 'Sanic API status link', 10),
        (r'<a href="/about">About</a>', 'Sanic about link', 10),
    ]
    
    # Sanic header patterns (though Sanic doesn't have many unique headers)
    HEADER_PATTERNS = [
        # Header name, Pattern, Description, Confidence
        ('content-type', r'text/plain; charset=utf-8', 'Sanic plain text response', 5),
        ('Allow', r'GET', 'Sanic GET method allowance', 3),
    ]
    
    # Sanic API response patterns
    API_PATTERNS = [
        # Pattern, Description, Confidence
        (r'"status": "running"', 'Sanic API status response', 20),
        (r'"framework": "sanic"', 'Sanic framework identification', 25),
        (r'"version": "\d+\.\d+\.\d+"', 'Sanic version in API', 15),
    ]
    
    def detect(self) -> None:
        """Run Sanic detection methods"""
        self._check_headers()
        self._check_content_patterns()
        self._check_error_patterns()
        self._check_api_endpoints()
        self._check_common_paths()
        self.detect_version()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """Add score for Sanic"""
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """Add version hint for Sanic"""
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """Add component for Sanic"""
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _check_headers(self) -> None:
        """Check for Sanic-specific headers"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        headers = response.headers
        
        # Check header patterns
        for header_name, pattern, description, confidence in self.HEADER_PATTERNS:
            if header_name in headers:
                header_value = headers[header_name]
                if re.search(pattern, header_value, re.IGNORECASE):
                    self._add_score(
                        confidence, 
                        'Header', 
                        f"{description}: {header_name}: {header_value}"
                    )
                    
        # Check for 405 Method Not Allowed (common in Sanic for HEAD requests)
        if response.status_code == 405:
            self._add_score(
                10, 
                'Header', 
                f"405 Method Not Allowed response (common in Sanic)"
            )
                
    def _check_content_patterns(self) -> None:
        """Check for Sanic content patterns"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        # Check content patterns
        for pattern, description, confidence in self.CONTENT_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                self._add_score(
                    confidence, 
                    'Content', 
                    f"{description}: {pattern}"
                )
                
    def _check_error_patterns(self) -> None:
        """Check for Sanic error patterns"""
        base_url = self.request_manager.target_url.rstrip('/')
        error_url = urljoin(base_url, '/error')
        
        response = self.request_manager.make_request(error_url)
        if not response:
            return
            
        # Check error patterns in response text
        for pattern, description, confidence in self.ERROR_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                self._add_score(
                    confidence, 
                    'Error', 
                    f"{description}: {pattern}"
                )
                
    def _check_api_endpoints(self) -> None:
        """Check for Sanic API endpoints"""
        base_url = self.request_manager.target_url.rstrip('/')
        api_url = urljoin(base_url, '/api/status')
        
        response = self.request_manager.make_request(api_url)
        if not response:
            return
            
        # Check API response patterns
        for pattern, description, confidence in self.API_PATTERNS:
            if re.search(pattern, response.text, re.IGNORECASE):
                self._add_score(
                    confidence, 
                    'API', 
                    f"{description}: {pattern}"
                )
                
        # Check for JSON response
        if response.headers.get('content-type', '').startswith('application/json'):
            self._add_score(
                15, 
                'API', 
                "JSON API response detected"
            )
            
    def _check_common_paths(self) -> None:
        """Check for Sanic-specific paths"""
        base_url = self.request_manager.target_url.rstrip('/')
        
        for path in self.COMMON_PATHS:
            url = urljoin(base_url, path)
            response = self.request_manager.make_request(url)
            
            if response:
                # Check for successful responses
                if response.status_code == 200:
                    self._add_score(
                        10, 
                        'Endpoint', 
                        f"{path} returns 200 OK"
                    )
                    
                # Check for 405 responses (common in Sanic)
                elif response.status_code == 405:
                    self._add_score(
                        8, 
                        'Endpoint', 
                        f"{path} returns 405 Method Not Allowed (Sanic behavior)"
                    )
                    
    def detect_version(self) -> None:
        """Attempt to detect Sanic version"""
        # Check error page for version hints
        base_url = self.request_manager.target_url.rstrip('/')
        error_url = urljoin(base_url, '/error')
        
        response = self.request_manager.make_request(error_url)
        if not response:
            return
            
        # Look for version in error traceback
        version_match = re.search(r'sanic/app\.py', response.text)
        if version_match:
            self._add_version_hint(
                "Unknown", 
                50, 
                "Sanic app.py referenced in error traceback"
            )
            
        # Check API endpoint for version
        api_url = urljoin(base_url, '/api/status')
        api_response = self.request_manager.make_request(api_url)
        if api_response:
            version_match = re.search(r'"version": "(\d+\.\d+\.\d+)"', api_response.text)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(
                    version, 
                    80, 
                    f"Sanic version detected in API response: {version}"
                ) 