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
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urljoin

from .base import BaseDetector


class FastAPIDetector(BaseDetector):
    """FastAPI-specific detection methods with enhanced capabilities"""
    
    FRAMEWORK = "FastAPI"
    
    # Common FastAPI documentation paths
    DOC_PATHS = [
        '/docs',
        '/redoc',
        '/openapi.json',
        '/api/docs',
        '/api/redoc',
        '/api/openapi.json',
        '/swagger',
        '/api/swagger',
        '/api',
        '/openapi',
    ]
    
    # Common ASGI servers for FastAPI
    ASGI_SERVERS = [
        'uvicorn',
        'hypercorn',
        'daphne',
    ]
    
    # Common FastAPI dependencies
    COMMON_DEPENDENCIES = [
        # Path, Package Name, Description
        ('/docs/oauth2-redirect', 'FastAPI OAuth2', 'OAuth2 authentication'),
        ('/__pydantic_error_page__', 'Pydantic', 'Pydantic data validation'),
        ('/debug/pydantic', 'Pydantic Debug', 'Pydantic debug tools'),
        ('/_starlette/', 'Starlette', 'Starlette framework'),
        ('/openapi.yaml', 'OpenAPI', 'OpenAPI schema in YAML format'),
        ('/metrics', 'Prometheus', 'Prometheus metrics'),
        ('/health', 'Health Check', 'Health check endpoint'),
        ('/api/v1/docs', 'Versioned API', 'Versioned API docs'),
    ]
    
    def detect(self) -> None:
        """Run FastAPI detection methods"""
        self._check_docs_endpoints()
        self._check_headers()
        self._check_error_responses()
        self._check_asgi_servers()
        self._check_dependencies()
        self._analyze_openapi_schema()
        self._check_fastapi_patterns()
        self._check_security_headers()
        self.detect_version()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """Add score for FastAPI"""
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """Add version hint for FastAPI"""
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """Add component for FastAPI"""
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _has_component(self, component_name: str) -> bool:
        """
        Check if a component has been detected
        
        Args:
            component_name: Name of the component to check
            
        Returns:
            True if the component has been detected, False otherwise
        """
        components = self.result_manager.components.get(self.FRAMEWORK, set())
        return component_name in components
        
    def _check_docs_endpoints(self) -> None:
        """Check for FastAPI documentation endpoints"""
        docs_found = False
        docs_path = None
        
        for path in self.DOC_PATHS:
            response = self.request_manager.make_request(path)
            if not response:
                continue
                
            if response.status_code == 200:
                self._add_score(
                    10, 
                    'Endpoint', 
                    f"{path} returns 200 OK"
                )
                
                # If this is a documentation page, add component
                content = response.text.lower() if response.text else ""
                
                # Look for SwaggerUI indicators
                if '/swagger-ui-bundle.js' in content or 'swagger-ui' in content:
                    self._add_score(
                        5,
                        'Documentation',
                        f"Swagger UI detected at {path}"
                    )
                    self._add_component('Swagger UI', f"Documentation at {path}")
                    docs_found = True
                    docs_path = path
                    
                # Look for ReDoc indicators
                if 'redoc' in content or '/redoc-standalone.js' in content:
                    self._add_score(
                        5,
                        'Documentation',
                        f"ReDoc detected at {path}"
                    )
                    self._add_component('ReDoc', f"Documentation at {path}")
                    docs_found = True
                    docs_path = path
                    
                # Look for OpenAPI JSON
                if path.endswith('.json') and 'openapi' in content and 'paths' in content:
                    self._add_score(
                        8,
                        'OpenAPI',
                        f"OpenAPI schema found at {path}"
                    )
                    
                    # Try to parse it for more details
                    try:
                        openapi_data = json.loads(response.text)
                        if 'openapi' in openapi_data:
                            self._add_component('OpenAPI', f"Schema version: {openapi_data['openapi']}")
                            
                            # Look for FastAPI generator info
                            if 'info' in openapi_data and 'x-fastapi-version' in openapi_data.get('info', {}):
                                fastapi_version = openapi_data['info']['x-fastapi-version']
                                self._add_version_hint(
                                    fastapi_version,
                                    10,
                                    f"FastAPI version in OpenAPI schema: {fastapi_version}"
                                )
                    except Exception:
                        pass
                    
        # If we found docs and it's not /docs, check if /docs redirects to it
        if docs_found and docs_path != '/docs':
            redirect_response = self.request_manager.make_request('/docs')
            if redirect_response and redirect_response.status_code == 302:
                location = redirect_response.headers.get('Location', '')
                if docs_path in location:
                    self._add_score(
                        3,
                        'Redirect',
                        f"/docs redirects to {location} (FastAPI pattern)"
                    )
                    
    def _check_headers(self) -> None:
        """Check for FastAPI-specific headers"""
        response = self.request_manager.make_request('/')
        if not response:
            return
            
        headers = response.headers
        
        # Check for server header with ASGI servers commonly used with FastAPI
        if 'server' in headers:
            server = headers['server'].lower()
            
            for asgi_server in self.ASGI_SERVERS:
                if asgi_server in server:
                    self._add_score(
                        8, 
                        'Header', 
                        f"Server header contains {asgi_server}: {headers['server']}"
                    )
                    self._add_component(f"{asgi_server.capitalize()}", f"ASGI server: {asgi_server}")
                    
                    # Try to extract version
                    version_match = re.search(rf'{asgi_server}[/\s]+(\d+\.\d+\.\d+)', server)
                    if version_match:
                        server_version = version_match.group(1)
                        self._add_component(
                            f"{asgi_server.capitalize()} {server_version}",
                            f"ASGI server version: {server_version}"
                        )
                        
        # Check for FastAPI-specific response headers
        fastapi_headers = [
            ('access-control-allow-origin', 'CORS support'),
            ('access-control-allow-credentials', 'CORS credentials support'),
            ('access-control-allow-methods', 'CORS methods support'),
            ('access-control-allow-headers', 'CORS headers support'),
            ('access-control-max-age', 'CORS cache control'),
        ]
        
        cors_headers_count = 0
        for header, description in fastapi_headers:
            if header in headers:
                cors_headers_count += 1
                
        if cors_headers_count >= 3:
            self._add_score(
                5,
                'Header',
                f"FastAPI CORS headers detected ({cors_headers_count} headers)"
            )
            self._add_component('CORS', "Cross-Origin Resource Sharing")
            
        # Check for X-Process-Time header (common in FastAPI tutorials)
        if 'x-process-time' in headers:
            self._add_score(
                10,
                'Header',
                "X-Process-Time header (FastAPI middleware pattern)"
            )
            
        # Check for missing Server header (FastAPI can be configured to hide it)
        if 'server' not in headers:
            # Make a HEAD request to see if OPTIONS shows CORS headers
            options_headers = {'Origin': 'https://example.com'}
            options_response = self.request_manager.make_request('/', method='OPTIONS', headers=options_headers)
            if options_response and 'access-control-allow-origin' in options_response.headers:
                self._add_score(
                    3,
                    'CORS',
                    "CORS headers in OPTIONS response (common in FastAPI)"
                )
                
    def _check_error_responses(self) -> None:
        """Check for FastAPI-specific error responses"""
        # Generate 404 and 422 errors (common FastAPI status codes)
        error_paths = [
            ('/non_existent_path_123456789', 404),
            ('/docs/invalid?param=[invalid', 422),
        ]
        
        for path, expected_status in error_paths:
            response = self.request_manager.make_request(path)
            if not response:
                continue
                
            status_code = response.status_code
            if status_code != expected_status:
                continue
                
            # Check for JSON error responses (FastAPI style)
            try:
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    error_data = json.loads(response.text)
                    
                    # FastAPI error format
                    if 'detail' in error_data:
                        self._add_score(
                            9,
                            'Error',
                            f"FastAPI-style JSON error response with 'detail' field"
                        )
                        
                        # Check for structured errors (422 responses)
                        if status_code == 422 and isinstance(error_data.get('detail'), list):
                            self._add_score(
                                10,
                                'Validation',
                                "FastAPI/Pydantic validation error structure"
                            )
                            self._add_component('Pydantic', "Validation errors")
                            self._add_version_hint('0.60+', 7, "Structured validation errors")
                            
            except Exception:
                pass
                
            # Check for non-JSON error responses
            if status_code == 404 and 'not found' in response.text.lower():
                # Differentiate between FastAPI and other frameworks
                if '<html' not in response.text.lower() and 'traceback' not in response.text.lower():
                    self._add_score(
                        3,
                        'Error',
                        "Plain text 404 error (possible FastAPI)"
                    )
                    
    def _check_asgi_servers(self) -> None:
        """Check for ASGI servers commonly used with FastAPI"""
        # Make request to root
        response = self.request_manager.make_request('/')
        if not response:
            return
            
        # Look for ASGI server signatures in response
        for asgi_server in self.ASGI_SERVERS:
            # Check headers
            if 'server' in response.headers and asgi_server in response.headers['server'].lower():
                self._add_score(
                    7,
                    'Server',
                    f"{asgi_server.capitalize()} ASGI server detected"
                )
                
            # Check HTML comments (sometimes development servers leave traces)
            if response.text and f"<!-- {asgi_server}" in response.text.lower():
                self._add_score(
                    5,
                    'Comment',
                    f"{asgi_server.capitalize()} comment in HTML"
                )
                
        # Check error traces for ASGI references
        error_response = self.request_manager.make_request('/this_should_cause_error_12345')
        if error_response and error_response.text:
            for asgi_server in self.ASGI_SERVERS:
                if asgi_server in error_response.text.lower():
                    self._add_score(
                        5,
                        'Error',
                        f"{asgi_server.capitalize()} reference in error response"
                    )
                    
    def _check_dependencies(self) -> None:
        """Check for FastAPI dependencies and extensions"""
        for path, package, description in self.COMMON_DEPENDENCIES:
            response = self.request_manager.make_request(path)
            if response and response.status_code == 200:
                self._add_score(
                    7,
                    'Dependency',
                    f"{package} detected at {path}"
                )
                self._add_component(package, description)
                
        # Specific check for starlette traces
        starlette_response = self.request_manager.make_request('/_starlette/500')
        if starlette_response and 'starlette' in starlette_response.text.lower():
            self._add_score(
                9,
                'Dependency',
                "Starlette debug traces detected"
            )
            self._add_component('Starlette', "Framework dependency")
            
    def _analyze_openapi_schema(self) -> None:
        """Analyze OpenAPI schema for FastAPI traits"""
        openapi_paths = ['/openapi.json', '/api/openapi.json', '/swagger/openapi.json']
        
        for path in openapi_paths:
            response = self.request_manager.make_request(path)
            if not response or response.status_code != 200:
                continue
                
            # Try to parse JSON
            try:
                schema = json.loads(response.text)
                if not isinstance(schema, dict) or 'openapi' not in schema:
                    continue
                    
                # This is an OpenAPI schema
                self._add_score(
                    8,
                    'Schema',
                    f"OpenAPI schema at {path}"
                )
                
                # Check for FastAPI-specific attributes
                fastapi_indicators = 0
                
                # Look for x-fastapi-* extensions
                for key in schema.get('info', {}):
                    if key.startswith('x-fastapi'):
                        fastapi_indicators += 1
                        if key == 'x-fastapi-version':
                            self._add_version_hint(
                                schema['info'][key],
                                10,
                                f"FastAPI version in schema: {schema['info'][key]}"
                            )
                            
                # Check for typical FastAPI operations
                if 'paths' in schema:
                    for path_info in schema['paths'].values():
                        for operation in path_info.values():
                            # FastAPI "tags" and "summary"
                            if 'tags' in operation and 'summary' in operation:
                                fastapi_indicators += 1
                                
                            # FastAPI response format
                            if 'responses' in operation:
                                for response_info in operation['responses'].values():
                                    if 'content' in response_info and 'application/json' in response_info['content']:
                                        fastapi_indicators += 1
                                        
                            # Look for complex schemas with descriptions (FastAPI/Pydantic style)
                            for param in operation.get('parameters', []):
                                if 'schema' in param and 'description' in param:
                                    fastapi_indicators += 1
                                    
                # Confidence boost based on indicators
                if fastapi_indicators >= 3:
                    self._add_score(
                        5 + min(fastapi_indicators, 5),  # Max +5 bonus
                        'Schema',
                        f"FastAPI schema indicators ({fastapi_indicators} patterns)"
                    )
                    
                # Look for version info in schemas
                openapi_version = schema.get('openapi', '')
                if openapi_version.startswith('3.'):
                    if openapi_version.startswith('3.0'):
                        self._add_version_hint('0.0-0.88', 6, "OpenAPI 3.0.x schema (early FastAPI)")
                    elif openapi_version.startswith('3.1'):
                        self._add_version_hint('0.89+', 8, "OpenAPI 3.1.x schema (newer FastAPI)")
                        
            except Exception:
                continue
                
    def _check_fastapi_patterns(self) -> None:
        """Check for FastAPI-specific code patterns"""
        response = self.request_manager.make_request('/')
        if not response or not response.text:
            return
            
        content = response.text.lower()
        
        # FastAPI common patterns in HTML or error pages
        fastapi_patterns = [
            ('fastapi', "FastAPI reference in HTML"),
            ('uvicorn', "Uvicorn reference in HTML"),
            ('starlette', "Starlette reference in HTML"),
            ('pydantic', "Pydantic reference in HTML"),
            ('swagger-ui', "Swagger UI reference in HTML"),
            ('redoc', "ReDoc reference in HTML"),
            ('@app.get', "FastAPI route decorator pattern"),
            ('@app.post', "FastAPI route decorator pattern"),
            ('asyncapi', "AsyncAPI reference"),
        ]
        
        for pattern, description in fastapi_patterns:
            if pattern in content:
                self._add_score(
                    5,
                    'Content',
                    description
                )
                
        # Check for FastAPI exception traces
        error_patterns = [
            ('raise fastapi', "FastAPI exception reference"),
            ('fastapi.exceptions', "FastAPI exceptions module"),
            ('pydantic.error_wrappers', "Pydantic error handling"),
            ('starlette.exceptions', "Starlette exception handling"),
            ('httpexception', "HTTP exception class"),
        ]
        
        # Check error page
        error_response = self.request_manager.make_request('/this_should_error_12345')
        if error_response and error_response.text:
            error_content = error_response.text.lower()
            
            for pattern, description in error_patterns:
                if pattern in error_content:
                    self._add_score(
                        6,
                        'Error',
                        description
                    )
                    
    def _check_security_headers(self) -> None:
        """Check for security headers used in FastAPI"""
        response = self.request_manager.make_request('/')
        if not response:
            return
            
        headers = response.headers
        
        # Check for FastAPI security headers
        if 'access-control-allow-origin' in headers:
            self._add_score(
                3,
                'Security',
                f"CORS Allow-Origin: {headers['access-control-allow-origin']}"
            )
            
        if 'x-process-time' in headers:
            self._add_score(
                7,
                'Middleware',
                "X-Process-Time middleware (FastAPI example pattern)"
            )
            
        # Extra security headers FastAPI might use
        fastapi_headers = [
            ('x-content-type-options', 'nosniff'),
            ('strict-transport-security', None),
            ('x-xss-protection', None),
        ]
        
        for header, expected_value in fastapi_headers:
            if header in headers:
                if expected_value is None or expected_value in headers[header].lower():
                    self._add_score(
                        2,
                        'Security',
                        f"{header} security header present"
                    )
                    
    def detect_version(self) -> None:
        """Attempt to determine FastAPI version"""
        # Check OpenAPI schema for version
        openapi_response = self.request_manager.make_request('/openapi.json')
        if openapi_response and openapi_response.status_code == 200:
            try:
                schema = json.loads(openapi_response.text)
                if 'info' in schema and 'x-fastapi-version' in schema['info']:
                    version = schema['info']['x-fastapi-version']
                    self._add_version_hint(
                        version,
                        10,
                        f"FastAPI version in OpenAPI schema: {version}"
                    )
                    
                # Check OpenAPI version for hint
                if 'openapi' in schema:
                    openapi_version = schema['openapi']
                    if openapi_version.startswith('3.0'):
                        self._add_version_hint('0.1-0.88', 7, f"OpenAPI 3.0.x schema: {openapi_version}")
                    elif openapi_version.startswith('3.1'):
                        self._add_version_hint('0.89+', 8, f"OpenAPI 3.1.x schema: {openapi_version}")
                        
            except Exception:
                pass
                
        # Check error page for version information
        error_response = self.request_manager.make_request('/this_should_error_fastapi_12345')
        if error_response and error_response.text:
            # Look for FastAPI version in error traceback
            version_match = re.search(r'fastapi[/_-]?(\d+\.\d+\.\d+)', error_response.text, re.IGNORECASE)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(
                    version,
                    8,
                    f"FastAPI version in error page: {version}"
                )
                
        # Check HTTP headers
        response = self.request_manager.make_request('/')
        if response and 'server' in response.headers:
            server = response.headers['server']
            
            # Some FastAPI apps expose version in Server header
            version_match = re.search(r'fastapi[/_-]?(\d+\.\d+\.\d+)', server, re.IGNORECASE)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(
                    version,
                    9,
                    f"FastAPI version in Server header: {version}"
                )
                
            # Check Uvicorn version as a proxy
            uvicorn_match = re.search(r'uvicorn[/_-]?(\d+\.\d+\.\d+)', server, re.IGNORECASE)
            if uvicorn_match:
                version = uvicorn_match.group(1)
                
                # Map Uvicorn version to FastAPI version (approximate)
                if version.startswith('0.11') or version.startswith('0.12'):
                    self._add_version_hint('0.45-0.60', 5, f"Based on Uvicorn {version}")
                elif version.startswith('0.15') or version.startswith('0.16'):
                    self._add_version_hint('0.65-0.80', 5, f"Based on Uvicorn {version}")
                elif version.startswith('0.17') or version.startswith('0.18'):
                    self._add_version_hint('0.85+', 5, f"Based on Uvicorn {version}")
                    
        # Feature detection based detection
        if self._has_component('OpenAPI'):
            self._add_version_hint('0.30+', 5, "OpenAPI schema support")
            
        if self._has_component('ReDoc'):
            self._add_version_hint('0.35+', 4, "ReDoc documentation")