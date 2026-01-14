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
import os
import json
import base64
import logging
import requests
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, Optional, Union, Tuple

logger = logging.getLogger("vte.auth")



# Fixing the django_authenticate function by removing debugging input calls
def django_authenticate(url, username, password, next_path="/admin/"):
    """
    Robust Django authentication that properly handles CSRF protection
    
    Args:
        url: Base URL of the Django application
        username: Admin username
        password: Admin password
        next_path: Redirect path after login
        
    Returns:
        session: Authenticated session object or None if authentication failed
    """
    import requests
    import re
    from bs4 import BeautifulSoup
    
    # Remove blocking debug input call
    # input(f">>> Django_Authenticate: {url}, {username}, {password}, {next_path}")
    
    session = requests.Session()
    
    # Step 1: Get the login page and collect the CSRF token
    login_url = f"{url.rstrip('/')}{login_url}" if login_url.startswith('/') else login_url
    
    try:
        # Add trailing slash to prevent redirect
        if not login_url.endswith('/'):
            login_url += '/'
            
        # Get the login page
        response = session.get(login_url, timeout=30)
        response.raise_for_status()
        
        # Extract CSRF token from the form
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        
        if not csrf_input or not csrf_input.get('value'):
            # Try regex as fallback
            csrf_pattern = re.compile(r'name=["\']csrfmiddlewaretoken["\'] value=["\'](.*?)["\']')
            match = csrf_pattern.search(response.text)
            csrf_token = match.group(1) if match else None
        else:
            csrf_token = csrf_input.get('value')
            
        if not csrf_token:
            print("Failed to extract CSRF token")
            return None
            
        print(f"CSRF Token extracted: {csrf_token[:10]}...")
        
        # Step 2: Prepare the login POST with proper headers and cookies
        login_data = {
            'csrfmiddlewaretoken': csrf_token,
            'username': username,
            'password': password,
            'next': next_path
        }
        
        # Build correct headers
        headers = {
            'Referer': login_url,
            'Origin': url.rstrip('/'),
            'X-CSRFToken': csrf_token
        }
        
        # Step 3: Submit the login form
        response = session.post(
            login_url,
            data=login_data,
            headers=headers,
            timeout=30
        )
        
        # Step 4: Verify login success
        if response.status_code == 200 and "authentication failed" in response.text.lower():
            print("Login failed: Invalid credentials")
            return None
            
        # Check if redirected to admin (success case)
        if "/admin/" in response.url:
            print("Login successful!")
            return session
        
        # Check for other success indicators
        if "Welcome" in response.text and username in response.text:
            print("Login successful based on welcome message!")
            return session
            
        print(f"Login failed with status code: {response.status_code}")
        print(f"Response URL: {response.url}")
        print(f"Response content (first 100 chars): {response.text[:100]}")
        return None
        
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None
    
class VimanaAuthenticationManager:
    """
    Authentication manager for VTE to handle various authentication methods
    """
    
    def __init__(self, target: str = None, session: Optional[requests.Session] = None):
        """
        Initialize the authentication manager
        
        Args:
            target: Base URL of the target application
            session: Optional requests session to use
        """
        self.target = target
        self.session = session or requests.Session()
        self.authenticated = False
        self.auth_type = None
        self.auth_data = {}
        self.tokens = {}

    def configure_django_auth(self, username, password, login_url='/admin/login/'):
        """Configure Django authentication with proper CSRF handling"""
        self.auth_type = "django"
        self.auth_data = {
            "username": username,
            "password": password,
            "login_url": login_url
        }
        
        # Use the specialized Django authentication
        session = django_authenticate(self.target, username, password, login_url)
        
        # Remove blocking debug input call
        # input(f">>> ConfigureDjangoAuth_Session: {session}")

        if session:
            # Transfer cookies and session state
            self.session.cookies.update(session.cookies)
            self.authenticated = True
            logger.info(f"Django Authentication successful for user: {username}")
            return True
        else:
            logger.warning(f"Django Authentication failed for user: {username}")
            return False
        
            
    def configure_basic_auth(self, username: str, password: str) -> bool:
        """
        Configure HTTP Basic Authentication
        
        Args:
            username: Username for basic auth
            password: Password for basic auth
            
        Returns:
            bool: True if configured successfully
        """
        self.auth_type = "basic"
        self.auth_data = {
            "username": username,
            "password": password
        }
        
        # Set basic auth for all requests in this session
        self.session.auth = (username, password)
        
        logger.info(f"Configured Basic Authentication for user: {username}")
        return True
    
    def configure_form_auth(self, login_url: str, username_field: str, password_field: str,
                           username: str, password: str, extra_fields: Optional[Dict[str, Any]] = None,
                           success_indicator: Optional[str] = None) -> bool:
        """
        Configure Form-based Authentication
        
        Args:
            login_url: URL of the login form
            username_field: Name of the username field in the form
            password_field: Name of the password field in the form
            username: Username value
            password: Password value
            extra_fields: Additional form fields to include
            success_indicator: String to check in response to confirm successful login
            
        Returns:
            bool: True if login was successful
        """
        self.auth_type = "form"
        self.auth_data = {
            "login_url": login_url,
            "username_field": username_field,
            "password_field": password_field,
            "username": username,
            "password": password,
            "extra_fields": extra_fields or {}
        }
        
        # Build form data
        form_data = {
            username_field: username,
            password_field: password
        }
        
        if extra_fields:
            form_data.update(extra_fields)
        
        # Need to determine if login URL is relative or absolute
        if not login_url.startswith(('http://', 'https://')):
            login_url = urljoin(self.target, login_url)
        
        try:
            # First make a GET request to the login page to get any CSRF tokens
            response = self.session.get(login_url, timeout=10)
            
            # Extract CSRF token if it exists (common pattern)
            csrf_token = self._extract_csrf_token(response.text)
            if csrf_token:
                form_data['csrfmiddlewaretoken'] = csrf_token
                logger.debug(f"Extracted CSRF token: {csrf_token}")
            
            # Now submit the login form
            response = self.session.post(
                login_url,
                data=form_data,
                headers={
                    'Referer': login_url
                },
                allow_redirects=True,
                timeout=10
            )
            
            # Check if login was successful
            self.authenticated = (
                response.status_code == 200 and
                (not success_indicator or success_indicator in response.text)
            )
            
            if self.authenticated:
                logger.info(f"Form Authentication successful for user: {username}")
            else:
                logger.warning(f"Form Authentication failed for user: {username}")
            
            return self.authenticated
            
        except Exception as e:
            logger.error(f"Form Authentication error: {str(e)}")
            return False
    
    def configure_api_key(self, api_key: str, header_name: str = 'X-API-Key',
                         as_query_param: bool = False, param_name: str = 'api_key') -> bool:
        """
        Configure API Key Authentication
        
        Args:
            api_key: The API key value
            header_name: Name of the header to use if sending as header
            as_query_param: Whether to send as query parameter instead of header
            param_name: Name of the query parameter if using query parameter
            
        Returns:
            bool: True if configured successfully
        """
        self.auth_type = "api_key"
        self.auth_data = {
            "api_key": api_key,
            "header_name": header_name,
            "as_query_param": as_query_param,
            "param_name": param_name
        }
        
        if not as_query_param:
            # Add API key header to all requests
            self.session.headers.update({header_name: api_key})
        
        logger.info(f"Configured API Key Authentication with key: {api_key[:4]}...")
        return True
    
    def configure_jwt(self, token: str, refresh_token: Optional[str] = None,
                    auth_url: Optional[str] = None, username: Optional[str] = None,
                    password: Optional[str] = None) -> bool:
        """
        Configure JWT Authentication
        
        Args:
            token: JWT token
            refresh_token: Optional refresh token
            auth_url: URL to get a new token if username/password provided
            username: Username for token acquisition
            password: Password for token acquisition
            
        Returns:
            bool: True if configured successfully
        """
        if not token:
            logger.error("JWT token is required for JWT authentication")
            return False
            
        self.auth_type = "jwt"
        self.tokens = {
            "access_token": token,
            "refresh_token": refresh_token
        }
        
        self.auth_data = {
            "auth_url": auth_url,
            "username": username,
            "password": password
        }
        
        # Add JWT token to Authorization header
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        
        # Set authenticated flag to True
        self.authenticated = True
        
        logger.info(f"Configured JWT Authentication with token: {token[:10]}...")
        return True
        
    def configure_oauth2(self, client_id: str, client_secret: str, token_url: str,
                        scope: Optional[str] = None) -> bool:
        """
        Configure OAuth2 Authentication
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_url: URL to get the access token
            scope: OAuth2 scope
            
        Returns:
            bool: True if token acquisition was successful
        """
        self.auth_type = "oauth2"
        self.auth_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "token_url": token_url,
            "scope": scope
        }
        
        # Acquire token using client credentials grant
        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            if scope:
                data['scope'] = scope
            
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.tokens = {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in")
            }
            
            # Add token to Authorization header
            self.session.headers.update({
                'Authorization': f'{token_data.get("token_type", "Bearer")} {token_data.get("access_token")}'
            })
            
            self.authenticated = True
            logger.info(f"OAuth2 Authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"OAuth2 Authentication error: {str(e)}")
            return False
    
    def configure_custom(self, headers: Optional[Dict[str, str]] = None,
                        cookies: Optional[Dict[str, str]] = None) -> bool:
        """
        Configure custom authentication with arbitrary headers and cookies
        
        Args:
            headers: Custom headers to include in all requests
            cookies: Custom cookies to include in all requests
            
        Returns:
            bool: True if configured successfully
        """
        self.auth_type = "custom"
        self.auth_data = {
            "headers": headers or {},
            "cookies": cookies or {}
        }
        
        # Add custom headers
        if headers:
            self.session.headers.update(headers)
        
        # Add custom cookies
        if cookies:
            for key, value in cookies.items():
                self.session.cookies.set(key, value)
        
        logger.info(f"Configured Custom Authentication")
        return True
    
    def apply_auth(self, request_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply authentication to a request
        
        Args:
            request_kwargs: Keyword arguments for requests.request
            
        Returns:
            Dict: Updated keyword arguments with authentication applied
        """
        if not self.auth_type:
            return request_kwargs
        
        # Handle query parameter API key
        if self.auth_type == "api_key" and self.auth_data.get("as_query_param", False):
            # Ensure 'params' exists in request_kwargs
            if 'params' not in request_kwargs:
                request_kwargs['params'] = {}
            
            # Add API key as query parameter
            request_kwargs['params'][self.auth_data.get("param_name", "api_key")] = \
                self.auth_data.get("api_key")
        
        return request_kwargs
    
    def refresh_token(self) -> bool:
        """
        Refresh the authentication token if possible
        
        Returns:
            bool: True if token refresh was successful
        """
        if self.auth_type == "jwt" and self.tokens.get("refresh_token") and self.auth_data.get("auth_url"):
            try:
                # Attempt to refresh the token
                response = requests.post(
                    self.auth_data["auth_url"],
                    json={
                        "refresh_token": self.tokens["refresh_token"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.tokens["access_token"] = token_data.get("access_token")
                    
                    if "refresh_token" in token_data:
                        self.tokens["refresh_token"] = token_data.get("refresh_token")
                    
                    # Update Authorization header
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.tokens["access_token"]}'
                    })
                    
                    logger.info("JWT token refreshed successfully")
                    return True
                else:
                    logger.warning(f"JWT token refresh failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error refreshing JWT token: {str(e)}")
                return False
        
        elif self.auth_type == "oauth2" and self.tokens.get("refresh_token"):
            try:
                data = {
                    'grant_type': 'refresh_token',
                    'refresh_token': self.tokens["refresh_token"],
                    'client_id': self.auth_data["client_id"],
                    'client_secret': self.auth_data["client_secret"]
                }
                
                response = requests.post(self.auth_data["token_url"], data=data, timeout=10)
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.tokens["access_token"] = token_data.get("access_token")
                    
                    if "refresh_token" in token_data:
                        self.tokens["refresh_token"] = token_data.get("refresh_token")
                    
                    # Update Authorization header
                    self.session.headers.update({
                        'Authorization': f'{token_data.get("token_type", "Bearer")} {token_data.get("access_token")}'
                    })
                    
                    logger.info("OAuth2 token refreshed successfully")
                    return True
                else:
                    logger.warning(f"OAuth2 token refresh failed: {response.status_code}")
                    return False
            
            except Exception as e:
                logger.error(f"Error refreshing OAuth2 token: {str(e)}")
                return False
        
        return False
    
    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """
        Extract CSRF token from HTML response
        
        Args:
            html: HTML content to parse
            
        Returns:
            str: CSRF token if found, None otherwise
        """
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try different patterns to find CSRF token
            # Django style
            csrf = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            if csrf and csrf.get('value'):
                return csrf['value']
            
            # Meta tag style
            csrf = soup.find('meta', {'name': 'csrf-token'})
            if csrf and csrf.get('content'):
                return csrf['content']
            
            # Another common pattern
            csrf = soup.find('input', {'name': '_csrf_token'})
            if csrf and csrf.get('value'):
                return csrf['value']
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting CSRF token: {str(e)}")
            return None
    
    def save_auth_state(self, filepath: str) -> bool:
        """
        Save authentication state to a file for reuse
        
        Args:
            filepath: Path to save the auth state file
            
        Returns:
            bool: True if successful
        """
        try:
            # Prepare auth data (excluding sensitive fields)
            auth_data_copy = self.auth_data.copy()
            if 'password' in auth_data_copy:
                auth_data_copy['password'] = '********'
                
            state = {
                'auth_type': self.auth_type,
                'authenticated': self.authenticated,
                'auth_data': auth_data_copy,
                'tokens': self.tokens,
                'cookies': dict(self.session.cookies),
                'headers': dict(self.session.headers)
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
                
            logger.info(f"Authentication state saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving authentication state: {str(e)}")
            return False
    
    def load_auth_state(self, filepath: str) -> bool:
        """
        Load authentication state from a file
        
        Args:
            filepath: Path to the auth state file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.auth_type = state.get('auth_type')
            self.authenticated = state.get('authenticated', False)
            self.auth_data = state.get('auth_data', {})
            self.tokens = state.get('tokens', {})
            
            # Restore cookies
            for name, value in state.get('cookies', {}).items():
                self.session.cookies.set(name, value)
            
            # Restore headers
            self.session.headers.update(state.get('headers', {}))
            
            logger.info(f"Authentication state loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading authentication state: {str(e)}")
            return False