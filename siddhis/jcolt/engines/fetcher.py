# -*- coding: utf-8 -*-
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

from neotermcolor import colored
from urllib.parse import urlparse, urljoin
import time
import asyncio
import aiohttp
import logging
import json
import sys
from typing import Dict, List, Optional, Any, Union, Tuple
from ..cmd.list import jcList 
from ..cmd.show import jcShow, PydanticTestDisplay
from core.auth.vf_auth import VimanaAuthenticationManager
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("jcolt.fetcher")

class RequestFailure(Exception):
    """Exception raised when a request fails"""
    def __init__(self, message, status=None, response=None, error=None):
        self.message = message
        self.status = status
        self.response = response
        self.error = error
        super().__init__(self.message)


class jcfetcher:
    """
    ** VimanaAuthenticationManager:
    Enhanced FastAPI API fetcher with comprehensive authentication support
    and robust request handling capabilities.
    """
    
    def __init__(self, fuzz_scope=None, **kwargs):
        """
        Initialize the JColt fetcher.
        
        Args:
            fuzz_scope: List of request dictionaries to process
            **kwargs: Additional configuration options
        """
        self.kwargs = kwargs
        self.fuzz_scope = fuzz_scope if fuzz_scope is not None else []
        self.len_fuzzscope = len(self.fuzz_scope)
        self.fuzz_results = {}
        self.jc_show = jcShow(self.len_fuzzscope)
        
        # Get target host from first request if available
        self.target_url = None
        if fuzz_scope and 'host' in fuzz_scope[0]:
            self.target_url = fuzz_scope[0]['host']
        elif 'target_url' in kwargs:
            self.target_url = kwargs['target_url']
        
        # Initialize session
        self.session = requests.Session()
            
        # Initialize Authentication Manager
        self.auth_manager = None
        if self.target_url:
            self.auth_manager = VimanaAuthenticationManager(self.target_url, self.session)
            self._configure_authentication()
            
        # Configure request settings
        self.timeout = aiohttp.ClientTimeout(
            total=kwargs.get('timeout', 30),
            connect=kwargs.get('connect_timeout', 10),
            sock_connect=kwargs.get('sock_connect_timeout', 10),
            sock_read=kwargs.get('sock_read_timeout', 10)
        )
        
        self.max_retries = kwargs.get('max_retries', 2)
        self.retry_delay = kwargs.get('retry_delay', 1)
        self.verify_ssl = kwargs.get('verify_ssl', False)

    def _configure_authentication(self):
        """Configure authentication based on provided arguments"""
        if not self.target_url:
            logger.warning("No target URL provided, authentication cannot be configured")
            return
        
        # Configure authentication from file if provided
        if self.kwargs.get('auth_file'):
            from core.auth.auth_from_file import VFAuthFromFile
            
            logger.info(f"Attempting to configure authentication from file: {self.kwargs.get('auth_file')}")
            
            # Create VFAuthFromFile with the target URL and current session
            auth_from_file = VFAuthFromFile(self.target_url, self.session)
            
            if auth_from_file.load_authentication_from_file(self.kwargs.get('auth_file')):
                # Use the authenticated session and manager from VFAuthFromFile
                self.auth_manager = auth_from_file.auth_manager
                
                # The session should already be updated since we passed it in
                logger.info(f"Authentication configured successfully from file: {self.kwargs.get('auth_file')}")
                return
            else:
                logger.error(f"Failed to configure authentication from file: {self.kwargs.get('auth_file')}")

        # JWT Authentication (legacy mode with --jwt flag)
        if self.kwargs.get('jwt_token'):
            token = self.kwargs.get('jwt_token')
            refresh_token = self.kwargs.get('refresh_token')
            auth_url = self.kwargs.get('auth_url')
            
            if not self.auth_manager:
                self.auth_manager = VimanaAuthenticationManager(self.target_url, self.session)
                
            self.auth_manager.configure_jwt(token, refresh_token, auth_url)
            
            # Also set Authorization header directly for backward compatibility
            self.kwargs['headers'] = self.kwargs.get('headers', {})
            self.kwargs['headers']['Authorization'] = f"Bearer {token}"
            logger.info("Configured JWT authentication (legacy mode)")
            return
            
        # New authentication with --auth-type
        auth_type = self.kwargs.get('auth_type')
        
        if not self.auth_manager:
            self.auth_manager = VimanaAuthenticationManager(self.target_url, self.session)
        
        if auth_type == "jwt" and self.kwargs.get('auth_token'):
            token = self.kwargs.get('auth_token')
            refresh_token = self.kwargs.get('auth_refresh_token')
            auth_url = self.kwargs.get('auth_url')
            
            # Configure via Vimana AuthenticationManager
            self.auth_manager.configure_jwt(token, refresh_token, auth_url)
            
            # Also set Authorization header for compatibility
            self.kwargs['headers'] = self.kwargs.get('headers', {})
            self.kwargs['headers']['Authorization'] = f"Bearer {token}"
            logger.info("Configured JWT authentication via --auth-type")
            
        # OAuth2 Authentication
        elif auth_type == "oauth2" and all(k in self.kwargs for k in ['client_id', 'client_secret', 'token_url']):
            client_id = self.kwargs.get('client_id')
            client_secret = self.kwargs.get('client_secret')
            token_url = self.kwargs.get('token_url')
            scope = self.kwargs.get('scope', '')
            self.auth_manager.configure_oauth2(client_id, client_secret, token_url, scope)
            logger.info("Configured OAuth2 authentication")
            
        # Basic Authentication
        elif auth_type == "basic" and all(k in self.kwargs for k in ['username', 'password']):
            username = self.kwargs.get('username')
            password = self.kwargs.get('password')
            self.auth_manager.configure_basic_auth(username, password)
            logger.info("Configured Basic authentication")
            
        # API Key Authentication
        elif auth_type == "api_key" and self.kwargs.get('api_key'):
            api_key = self.kwargs.get('api_key')
            header_name = self.kwargs.get('api_key_header', 'X-API-Key')
            as_query_param = self.kwargs.get('api_key_in_query', False)
            param_name = self.kwargs.get('api_key_param_name', 'api_key')
            self.auth_manager.configure_api_key(
                api_key, header_name, as_query_param, param_name
            )
            logger.info(f"Configured API Key authentication ({header_name})")
            
        # Form Authentication
        elif auth_type == "form" and all(k in self.kwargs for k in ['login_url', 'username_field', 'password_field', 'form_username', 'form_password']):
            login_url = self.kwargs.get('login_url')
            username_field = self.kwargs.get('username_field')
            password_field = self.kwargs.get('password_field')
            username = self.kwargs.get('form_username')
            password = self.kwargs.get('form_password')
            extra_fields = self.kwargs.get('extra_fields', {})
            success_indicator = self.kwargs.get('success_indicator')
            self.auth_manager.configure_form_auth(
                login_url, username_field, password_field, username, password, 
                extra_fields, success_indicator
            )
            logger.info("Configured Form authentication")
            
        # Custom Authentication
        elif auth_type == "custom" and (self.kwargs.get('custom_headers') or self.kwargs.get('custom_cookies')):
            headers = self.kwargs.get('custom_headers', {})
            cookies = self.kwargs.get('custom_cookies', {})
            self.auth_manager.configure_custom(headers, cookies)
            logger.info("Configured Custom authentication")

    def get_base_headers(self) -> Dict[str, str]:
        """
        Get base headers for requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        host = urlparse(self.target_url).netloc if self.target_url else '127.0.0.1:8000'
        
        # Default User-Agent
        user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0'
        if 'user_agent' in self.kwargs and self.kwargs['user_agent'] is not None:
            user_agent = str(self.kwargs['user_agent'])
        
        # Base URL for Referer and Origin
        base_url = self.target_url or 'http://127.0.0.1:8000'
        
        headers = {
            'Host': host,
            'User-Agent': user_agent,
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': base_url,
            'Content-Type': 'application/json',
            'Origin': base_url,
            'Connection': 'close',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        
        # Add custom headers if provided, ensuring all values are strings
        if self.kwargs.get('headers'):
            for k, v in self.kwargs.get('headers').items():
                if v is not None:  # Skip None values
                    headers[k] = str(v)
            
        return headers

    def get_headers(self, path=None) -> Dict[str, str]:
        """
        Get headers for a specific request, including authentication if configured.
        
        Args:
            path: The API path for the request
            
        Returns:
            Dictionary of HTTP headers with authentication applied
        """
        headers = self.get_base_headers()
        
        # Apply authentication if configured
        if self.auth_manager and self.auth_manager.authenticated:
            # Debug logging to verify authentication is being applied
            logger.debug(f"Applying authentication headers for {path}")
            request_kwargs = {'headers': headers}
            request_kwargs = self.auth_manager.apply_auth(request_kwargs)
            headers = request_kwargs['headers']
            
            # Also check if Authorization header is in the session headers
            if 'Authorization' in self.auth_manager.session.headers:
                auth_header = self.auth_manager.session.headers['Authorization']
                headers['Authorization'] = auth_header
                logger.debug(f"Added Authorization header from session: {auth_header[:15]}...")
            
            # Add other session headers that might be relevant for auth
            for header_name in ['Cookie', 'X-CSRF-Token', 'X-API-Key']:
                if header_name in self.auth_manager.session.headers:
                    headers[header_name] = self.auth_manager.session.headers[header_name]
        else:
            logger.debug(f"No authentication applied for {path}")
            
        return headers
    
    async def maybe_refresh_token(self, response):
        """
        Attempt to refresh tokens if response indicates authentication failure.
        
        Args:
            response: The HTTP response object
            
        Returns:
            bool: True if token was refreshed, False otherwise
        """
        if not self.auth_manager:
            return False
            
        # Try to refresh token if we get a 401 Unauthorized response
        if response.status == 401 and self.auth_manager.auth_type in ('jwt', 'oauth2'):
            logger.info("Received 401, attempting token refresh")
            return self.auth_manager.refresh_token()
            
        return False

    async def fetch_url(self, session, request_dict, retry_count=0):
        """
        Fetch a single URL and process the response.
        
        Args:
            session: The aiohttp client session
            request_dict: Dictionary with request information
            retry_count: Current retry attempt (for internal use)
        """
        fuzz_obj = request_dict.copy()
        method = request_dict['method'].upper()
        path = request_dict['path']
        url = request_dict['host'] + path if '://' in request_dict['host'] else f"http://{request_dict['host']}{path}"
        body = request_dict.get('body')
        properties = request_dict['properties']
        summary = properties.get('summary')
        tags = ','.join(properties.get('tags', []))
        
        # Prepare headers with authentication
        headers = self.get_headers(path)

        # Initialize results container if needed
        if not self.fuzz_results.get(path):
            self.fuzz_results[path] = []

        # Make the request with timing
        start_time = time.time()
        try:
            # Convert body to JSON if it's a dict or list
            request_body = body
            if isinstance(body, (dict, list)) and body:
                request_body = json.dumps(body)
                
            # Make the request
            async with session.request(
                method, 
                url, 
                headers=headers, 
                data=request_body,
                timeout=self.timeout,
                ssl=self.verify_ssl
            ) as response:
                end_time = time.time()
                response_time = end_time - start_time
                
                # Get response text/json
                try:
                    response_text = await self.jc_show.get_response_text(response)
                except Exception as e:
                    logger.error(f"Error parsing response: {e}")
                    response_text = str(e)
                
                # Try token refresh if authentication failed
                if response.status == 401 and await self.maybe_refresh_token(response):
                    if retry_count < self.max_retries:
                        logger.info(f"Token refreshed, retrying request to {path}")
                        await asyncio.sleep(self.retry_delay)
                        return await self.fetch_url(session, request_dict, retry_count + 1)
                
                # Record the response
                fuzz_obj['response'] = response
                fuzz_obj['response_time'] = response_time
                fuzz_obj['response_size'] = len(await response.read())
                fuzz_obj['response_text'] = response_text
                
                # Detailed auditing information
                fuzz_obj['response_status_audit'] = {
                    'expected_status_codes': self._get_expected_status_codes(properties),
                    'actual_status_code': response.status,
                    'status_mismatch': not self._is_expected_status(properties, response.status),
                    'headers': dict(response.headers),
                    'content_type': response.headers.get('Content-Type', '')
                }
                
        except aiohttp.ClientError as e:
            end_time = time.time()
            logger.error(f"Connection error: {e}")
            
            # Retry on connection errors
            if retry_count < self.max_retries:
                logger.info(f"Retrying request to {path} after error: {e}")
                await asyncio.sleep(self.retry_delay)
                return await self.fetch_url(session, request_dict, retry_count + 1)
            
            fuzz_obj['error'] = str(e)
            fuzz_obj['response_time'] = end_time - start_time
            fuzz_obj['response'] = None
            response_text = str(e)
            response = None
            
        except asyncio.TimeoutError:
            end_time = time.time()
            logger.error(f"Request timed out: {url}")
            
            # Retry on timeouts
            if retry_count < self.max_retries:
                logger.info(f"Retrying request to {path} after timeout")
                await asyncio.sleep(self.retry_delay)
                return await self.fetch_url(session, request_dict, retry_count + 1)
            
            fuzz_obj['error'] = "Request timed out"
            fuzz_obj['response_time'] = end_time - start_time
            fuzz_obj['response'] = None
            response_text = "Request timed out"
            response = None
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"Unexpected error: {e}")
            fuzz_obj['error'] = str(e)
            fuzz_obj['response_time'] = end_time - start_time
            fuzz_obj['response'] = None
            response_text = str(e)
            response = None
        
        # Record session and headers for analysis
        fuzz_obj['session'] = session
        fuzz_obj['headers'] = headers
        
        # Add to results
        self.fuzz_results[path].append(fuzz_obj)
        
        if self.kwargs.get('pydantic_test'):
            pydantic_display = PydanticTestDisplay(colors_disabled=self.kwargs.get('colors_disabled'))
            pydantic_display.show_test_request(fuzz_obj)
            pydantic_display.show_test_response(fuzz_obj)
        else:
            # Regular request/response display for fuzzspec
            self.jc_show.show_request_info(method, request_dict['path'], session.version, headers, body)
            if response:
                self.jc_show.show_response_info(response, response_text)
            else:
                self._show_error_as_response(fuzz_obj)
        
    def _show_error_as_response(self, fuzz_obj):
        """Display error information in a response-like format"""
        class MockResponse:
            def __init__(self, error):
                self.status = 0
                self.reason = "Error"
                self.version = type('obj', (object,), {'major': 1, 'minor': 1})
                self.headers = {'Error': error}
                self.content_length = len(error) if error else 0
                
        error_msg = fuzz_obj.get('error', 'Unknown error')
        mock_response = MockResponse(error_msg)
        
        # Set the response in fuzz_obj for downstream processing
        fuzz_obj['response'] = mock_response
        
        # Display the mock response
        self.jc_show.show_response_info(mock_response, error_msg)

    def _get_expected_status_codes(self, properties):
        """Extract expected status codes from API specification"""
        expected_codes = []
        responses = properties.get('responses', {})
        
        if isinstance(responses, dict):
            for code in responses.keys():
                try:
                    expected_codes.append(int(code))
                except (ValueError, TypeError):
                    # Handle special cases like 'default'
                    pass
        
        # If no explicit codes defined, assume common success codes
        if not expected_codes:
            expected_codes = [200, 201, 204]
            
        return expected_codes

    def _is_expected_status(self, properties, status_code):
        """Check if a status code matches what's defined in the API spec"""
        expected_codes = self._get_expected_status_codes(properties)
        return status_code in expected_codes

    async def fetch_all_urls(self):
        """
        Fetch all URLs defined in the fuzz scope concurrently.
        """
        # Client session settings
        connector = aiohttp.TCPConnector(
            limit=self.kwargs.get('connection_limit', 10),
            ttl_dns_cache=300,
            verify_ssl=self.verify_ssl
        )
        
        trace_config = None
        if self.kwargs.get('debug_logging', False):
            # Setup request tracing for debugging
            trace_config = aiohttp.TraceConfig()
            async def on_request_start(session, ctx, params):
                logger.debug(f"Starting request to {params.url}")
            trace_config.on_request_start.append(on_request_start)
            
        client_timeout = aiohttp.ClientTimeout(
            total=self.kwargs.get('timeout', 30)
        )
            
        async with aiohttp.ClientSession(
            connector=connector,
            trace_configs=[trace_config] if trace_config else None,
            timeout=client_timeout
        ) as session:
            tasks = []
            
            # Create tasks for each request in the fuzz scope
            for request in self.fuzz_scope:
                task = asyncio.create_task(self.fetch_url(session, request))
                tasks.append(task)
                
                # Add small delay between task creation to avoid overwhelming the server
                if self.kwargs.get('request_delay'):
                    await asyncio.sleep(self.kwargs.get('request_delay'))
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
            # Perform post-processing analysis
            self._analyze_results()
    
    def _analyze_results(self):
        """
        Analyze the results after all requests have been made.
        Looks for patterns in responses, potential vulnerabilities, etc.
        """
        # Count response status codes
        status_counts = {}
        for path, responses in self.fuzz_results.items():
            for response_data in responses:
                if 'response' in response_data and response_data['response']:
                    status = response_data['response'].status
                    status_counts[status] = status_counts.get(status, 0) + 1
        
        # Look for interesting patterns
        if self.kwargs.get('verbose_logging', False):
            logger.info(f"Response status code distribution: {status_counts}")
            
            for path, responses in self.fuzz_results.items():
                for response_data in responses:
                    # Check for status code mismatches
                    if 'response_status_audit' in response_data:
                        audit = response_data['response_status_audit']
                        if audit.get('status_mismatch'):
                            logger.warning(
                                f"Status code mismatch for {path}: "
                                f"Got {audit['actual_status_code']}, expected one of {audit['expected_status_codes']}"
                            )

    async def start_async(self):
        """Asynchronous entry point for fetching all URLs"""
        await self.fetch_all_urls()
        return self.fuzz_results

    def start(self):
        """
        Synchronous entry point for fetching all URLs.
        Returns the results after all requests have completed.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        loop.run_until_complete(self.fetch_all_urls())
        return self.fuzz_results