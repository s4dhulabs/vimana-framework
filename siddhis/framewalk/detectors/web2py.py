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


class Web2pyDetector(BaseDetector):
    """Web2py-specific detection methods"""
    
    FRAMEWORK = "Web2py"
    
    # Common Web2py paths to check
    COMMON_PATHS = [
        '/admin/',
        '/appadmin/',
        '/static/',
        '/welcome/',
        '/default/',
        '/_admin/',
        '/admin/default/',
        '/admin/default/index',
        '/admin/default/login',
    ]
    
    # Web2py error patterns
    ERROR_PATTERNS = [
        # Pattern, Description, Confidence
        (r'web2py_error:', 'Web2py error header', 15),
        (r'web2py_error: invalid application', 'Web2py invalid application error', 20),
        (r'web2py_error: ticket', 'Web2py ticket error', 15),
        (r'web2py_error: ticket invalid', 'Web2py invalid ticket error', 18),
        (r'web2py_error: application', 'Web2py application error', 12),
    ]
    
    # Web2py server patterns
    SERVER_PATTERNS = [
        # Pattern, Description, Confidence
        (r'Rocket\d+', 'Rocket server (Web2py default)', 25),
        (r'Rocket3', 'Rocket3 server (Web2py default)', 30),
        (r'web2py', 'Web2py server reference', 20),
    ]
    
    # Web2py session cookie patterns
    SESSION_PATTERNS = [
        # Pattern, Description, Confidence
        (r'session_id_\w+=', 'Web2py session cookie pattern', 25),
        (r'session_id_admin=', 'Web2py admin session cookie', 30),
        (r'session_id_welcome=', 'Web2py welcome app session cookie', 25),
    ]
    
    # Web2py content patterns
    CONTENT_PATTERNS = [
        # Pattern, Description, Confidence
        (r'web2py', 'Web2py reference in content', 5),
        (r'{{=', 'Web2py template syntax', 15),
        (r'{{extend', 'Web2py template extend', 20),
        (r'{{include', 'Web2py template include', 20),
        (r'{{block', 'Web2py template block', 20),
        (r'{{pass', 'Web2py template pass', 20),
        (r'{{if', 'Web2py template if', 15),
        (r'{{for', 'Web2py template for', 15),
        (r'{{try', 'Web2py template try', 15),
        (r'{{except', 'Web2py template except', 15),
        (r'{{finally', 'Web2py template finally', 15),
        (r'{{def', 'Web2py template def', 20),
        (r'{{return', 'Web2py template return', 15),
    ]
    
    # Web2py header patterns
    HEADER_PATTERNS = [
        # Header name, Pattern, Description, Confidence
        ('X-Powered-By', r'web2py', 'X-Powered-By header contains web2py', 30),
        ('Server', r'Rocket\d+', 'Server header contains Rocket', 25),
        ('Server', r'web2py', 'Server header contains web2py', 20),
    ]
    
    def detect(self) -> None:
        """Run Web2py detection methods"""
        self._check_headers()
        self._check_common_paths()
        self._check_error_patterns()
        self._check_server_patterns()
        self._check_session_patterns()
        self._check_content_patterns()
        self._check_admin_interface()
        self.detect_version()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """Add score for Web2py"""
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """Add version hint for Web2py"""
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """Add component for Web2py"""
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _check_headers(self) -> None:
        """Check for Web2py-specific headers"""
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
                    
        # Check for web2py in any header
        for name, value in headers.items():
            if 'web2py' in value.lower():
                self._add_score(
                    15, 
                    'Header', 
                    f"{name} header contains web2py: {value}"
                )
                
    def _check_common_paths(self) -> None:
        """Check for Web2py-specific paths"""
        base_url = self.request_manager.target_url.rstrip('/')
        
        for path in self.COMMON_PATHS:
            url = urljoin(base_url, path)
            response = self.request_manager.make_request(url)
            
            if response:
                # Check for web2py error patterns in response
                if 'web2py_error:' in response.text:
                    self._add_score(
                        20, 
                        'Endpoint', 
                        f"{path} returns web2py error response"
                    )
                    
                # Check for successful admin access
                if path == '/admin/' and response.status_code == 200:
                    self._add_score(
                        25, 
                        'Endpoint', 
                        f"{path} returns 200 OK (Web2py admin interface)"
                    )
                    
                # Check for web2py session cookies
                if 'session_id_' in response.headers.get('Set-Cookie', ''):
                    self._add_score(
                        20, 
                        'Endpoint', 
                        f"{path} sets web2py session cookie"
                    )
                    
    def _check_error_patterns(self) -> None:
        """Check for Web2py error patterns"""
        response = self.request_manager.make_request()
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
                
        # Check error patterns in headers
        for name, value in response.headers.items():
            for pattern, description, confidence in self.ERROR_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    self._add_score(
                        confidence, 
                        'Error', 
                        f"{description} in {name} header: {value}"
                    )
                    
    def _check_server_patterns(self) -> None:
        """Check for Web2py server patterns"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        server_header = response.headers.get('Server', '')
        
        for pattern, description, confidence in self.SERVER_PATTERNS:
            if re.search(pattern, server_header, re.IGNORECASE):
                self._add_score(
                    confidence, 
                    'Server', 
                    f"{description}: {server_header}"
                )
                
    def _check_session_patterns(self) -> None:
        """Check for Web2py session patterns"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        # Check Set-Cookie header
        set_cookie = response.headers.get('Set-Cookie', '')
        
        for pattern, description, confidence in self.SESSION_PATTERNS:
            if re.search(pattern, set_cookie, re.IGNORECASE):
                self._add_score(
                    confidence, 
                    'Session', 
                    f"{description}: {set_cookie}"
                )
                
    def _check_content_patterns(self) -> None:
        """Check for Web2py content patterns"""
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
                
    def _check_admin_interface(self) -> None:
        """Check for Web2py admin interface"""
        base_url = self.request_manager.target_url.rstrip('/')
        admin_url = urljoin(base_url, '/admin/')
        
        response = self.request_manager.make_request(admin_url)
        if response and response.status_code == 200:
            # Check for web2py admin characteristics
            if 'session_id_admin=' in response.headers.get('Set-Cookie', ''):
                self._add_score(
                    30, 
                    'Admin', 
                    "Web2py admin interface detected with admin session cookie"
                )
                self._add_component(
                    "Admin Interface", 
                    "Web2py admin interface accessible at /admin/"
                )
                
    def detect_version(self) -> None:
        """Attempt to detect Web2py version"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        # Check server header for Rocket version
        server_header = response.headers.get('Server', '')
        rocket_match = re.search(r'Rocket(\d+\.\d+\.\d+)', server_header)
        if rocket_match:
            rocket_version = rocket_match.group(1)
            self._add_version_hint(
                f"Rocket {rocket_version}", 
                70, 
                f"Rocket server version detected: {rocket_version}"
            )
            
        # Check for web2py version in headers or content
        # This would require more specific version detection logic
        # based on web2py's versioning scheme 