# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-2py scanner admin scanner
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import re
from typing import Dict, Any, List
from urllib.parse import urljoin
import datetime
import traceback


class AdminScanner:
    """
    Scanner for Web2py admin interface vulnerabilities.
    
    Detects exposed admin interfaces and tests for common misconfigurations
    including default credentials, weak authentication, and access control issues.
    """
    
    def __init__(self, http_client, config: Dict[str, Any]):
        self.http_client = http_client
        self.config = config
        self.session_timeout = int(config.get("session_timeout", 0))  # seconds, 0 disables
        self.debug_fn = config.get('debug_fn', print)
        
        # Admin endpoints to test
        self.admin_endpoints = [
            "/admin/",
            "/admin",
            "/admin/default/",
            "/admin/default/index",
            "/admin/default/login",
            "/admin/default/logout",
            "/admin/default/manage",
            "/admin/default/design",
            "/admin/default/edit",
            "/admin/default/delete",
            "/admin/default/upload",
            "/admin/default/download",
            "/admin/default/backup",
            "/admin/default/restore"
        ]
        
        # Common admin credentials
        self.common_credentials = [
            ("admin", "admin"),
            ("admin", "password"),
            ("admin", "123456"),
            ("admin", "admin123"),
            ("admin", "web2py"),
            ("web2py", "web2py"),
            ("web2py", "admin"),
            ("administrator", "admin"),
            ("root", "root"),
            ("root", "admin"),
            ("", ""),  # Empty credentials
        ]
        
        # Admin interface indicators
        self.admin_indicators = [
            "web2py admin",
            "administration",
            "admin interface",
            "manage applications",
            "design applications",
            "edit applications",
            "upload applications",
            "backup applications",
            "restore applications",
            "session_id_admin",
            "admin_password",
            "admin_email"
        ]

    def _debug(self, message: str, context: str = None, emoji: str = None):
        if not self.config.get("verbose", False):
            return
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[DEBUG]"
        if context:
            prefix += f"[{context}]"
        if emoji:
            prefix += f" {emoji}"
        self.debug_fn(f"{ts} {prefix} {message}")

    async def scan(self, target_url: str) -> Dict[str, Any]:
        """
        Scan target for admin interface vulnerabilities.
        
        Args:
            target_url: Target URL to scan
            
        Returns:
            Dictionary containing scan results and vulnerabilities
        """
        vulnerabilities = []
        scan_data = {
            "admin_endpoints_found": [],
            "admin_accessible": False,
            "default_credentials": [],
            "weak_authentication": False,
            "vulnerabilities": vulnerabilities
        }
        
        try:
            # Test admin endpoints
            admin_endpoints = await self._test_admin_endpoints(target_url)
            if self.config.get('verbose', False):
                if not admin_endpoints:
                    self._debug("No admin endpoints found.", context="admin_scanner", emoji="❌")
                else:
                    self._debug(f"Checked endpoints: {admin_endpoints}", context="admin_scanner", emoji="🔍")
            scan_data["admin_endpoints_found"] = admin_endpoints
            
            if admin_endpoints:
                scan_data["admin_accessible"] = True
                
                # Test for default credentials
                default_creds = await self._test_default_credentials(target_url, admin_endpoints)
                if self.config.get('verbose', False):
                    self._debug(f"Default credentials found: {default_creds}", context="admin_scanner", emoji="🔍")
                scan_data["default_credentials"] = default_creds
                
                if default_creds:
                    vulnerabilities.append(self._create_vulnerability(
                        "Web2py Admin Interface - Default Credentials",
                        "high",
                        f"Default credentials found for admin interface: {', '.join([f'{user}:{passwd}' for user, passwd in default_creds])}",
                        ["Admin interface accessible with default credentials"],
                        {
                            "endpoints": admin_endpoints,
                            "credentials": default_creds,
                            "cwe": "CWE-287"
                        }
                    ))
                
                # Test for weak authentication
                weak_auth = await self._test_weak_authentication(target_url, admin_endpoints)
                if self.config.get('verbose', False):
                    self._debug(f"Weak authentication: {weak_auth}", context="admin_scanner", emoji="🔍")
                scan_data["weak_authentication"] = weak_auth
                
                if weak_auth:
                    vulnerabilities.append(self._create_vulnerability(
                        "Web2py Admin Interface - Weak Authentication",
                        "medium",
                        "Admin interface has weak authentication mechanisms",
                        ["Admin interface accessible without proper authentication"],
                        {
                            "endpoints": admin_endpoints,
                            "cwe": "CWE-287"
                        }
                    ))
                
                # Add basic admin interface exposure vulnerability
                vulnerabilities.append(self._create_vulnerability(
                    "Web2py Admin Interface Exposed",
                    "high",
                    f"Web2py admin interface is accessible at: {', '.join(admin_endpoints)}",
                    [f"Admin endpoint accessible: {endpoint}" for endpoint in admin_endpoints],
                    {
                        "endpoints": admin_endpoints,
                        "cwe": "CWE-284"
                    }
                ))
            
            # Test for admin interface indicators in main page
            main_page_indicators = await self._check_main_page_indicators(target_url)
            if self.config.get('verbose', False):
                self._debug(f"Main page indicators: {main_page_indicators}", context="admin_scanner", emoji="🔍")
            if main_page_indicators:
                vulnerabilities.append(self._create_vulnerability(
                    "Web2py Admin Interface Indicators",
                    "low",
                    "Admin interface indicators found in main page content",
                    main_page_indicators,
                    {
                        "indicators": main_page_indicators,
                        "cwe": "CWE-200"
                    }
                ))
            
        except Exception as e:
            vulnerabilities.append(self._create_vulnerability(
                "Admin Scanner Error",
                "low",
                f"Error during admin interface scanning: {str(e)}",
                [f"Scanner error: {str(e)}"],
                {"error": str(e)}
            ))
        
        scan_data["vulnerabilities"] = vulnerabilities
        return scan_data

    async def _test_admin_endpoints(self, target_url: str) -> List[str]:
        """Test for accessible admin endpoints."""
        accessible_endpoints = []
        
        for endpoint in self.admin_endpoints:
            try:
                url = urljoin(target_url, endpoint)
                result = await self.http_client.get(url)
                if self.config.get('verbose', False):
                    self._debug(f"Checked endpoint: {endpoint} status={result['status']}", context="admin_scanner", emoji="🔍")
                    # Log headers for key endpoints
                    if endpoint in ["/admin/", "/admin/default/login"]:
                        self._debug(f"Headers for {endpoint}: {result.get('headers', {})}", context="admin_scanner", emoji="📋")
                
                # Check if endpoint is accessible and shows admin interface
                if result["status"] < 400:
                    content = result["content"].lower()
                    
                    # More strict validation - check for actual admin content
                    if any(indicator in content for indicator in self.admin_indicators):
                        accessible_endpoints.append(endpoint)
                    elif "web2py admin" in content or "web2py administration" in content:
                        accessible_endpoints.append(endpoint)
                    elif "admin interface" in content and "welcome" in content:
                        accessible_endpoints.append(endpoint)
                    else:
                        if self.config.get('verbose', False):
                            self._debug(f"Skipped endpoint: {endpoint} (no admin indicators)", context="admin_scanner", emoji="⏭️")
                else:
                    if self.config.get('verbose', False):
                        self._debug(f"Skipped endpoint: {endpoint} (status={result['status']})", context="admin_scanner", emoji="⏭️")
                        
            except Exception as e:
                if self.config.get('verbose', False):
                    self._debug(f"Error checking endpoint {endpoint}: {e}\n{traceback.format_exc()}", context="admin_scanner", emoji="💥")
                continue
        
        return accessible_endpoints

    async def _test_default_credentials(self, target_url: str, admin_endpoints: List[str]) -> List[tuple]:
        """Test for default admin credentials."""
        working_credentials = []
        
        # Find login endpoint
        login_endpoint = None
        for endpoint in admin_endpoints:
            if "login" in endpoint or "default" in endpoint:
                login_endpoint = endpoint
                break
        
        if not login_endpoint:
            return working_credentials
        
        login_url = urljoin(target_url, login_endpoint)
        
        for username, password in self.common_credentials:
            try:
                # Try to login with credentials
                login_data = {
                    "username": username,
                    "password": password,
                    "email": username if "@" in username else f"{username}@example.com"
                }
                if self.config.get('verbose', False):
                    self._debug(f"POST data: {login_data}", context="admin_scanner", emoji="📤")
                    self._debug(f"Tried credentials: {username}:{password}", context="admin_scanner", emoji="🔍")
                
                result = await self.http_client.post(login_url, data=login_data)
                if self.config.get('verbose', False):
                    self._debug(f"Tried credentials: {username}:{password} status={result['status']}", context="admin_scanner", emoji="🔍")
                
                # Check if login was successful
                if self._is_login_successful(result):
                    working_credentials.append((username, password))
                    if self.config.get('verbose', False):
                        self._debug(f"Set-Cookie: {result.get('set_cookie', '')}", context="admin_scanner", emoji="🍪")
                        self._debug(f"Redirect Location: {result.get('headers', {}).get('Location', '')}", context="admin_scanner", emoji="➡️")
                    
            except Exception as e:
                if self.config.get('verbose', False):
                    self._debug(f"Error trying credentials {username}:{password}: {e}\n{traceback.format_exc()}", context="admin_scanner", emoji="💥")
                continue
        
        return working_credentials

    async def _test_weak_authentication(self, target_url: str, admin_endpoints: List[str]) -> bool:
        """Test for weak authentication mechanisms."""
        
        for endpoint in admin_endpoints:
            try:
                url = urljoin(target_url, endpoint)
                
                # Test without authentication
                result = await self.http_client.get(url)
                
                # Check if we can access admin functions without proper auth
                if result["status"] == 200:
                    content = result["content"].lower()
                    
                    # Look for admin functionality that shouldn't be accessible
                    admin_functions = [
                        "manage applications",
                        "design applications",
                        "edit applications",
                        "upload applications",
                        "backup applications",
                        "restore applications",
                        "delete applications"
                    ]
                    
                    if any(func in content for func in admin_functions):
                        return True
                        
            except Exception:
                continue
        
        return False

    async def _check_main_page_indicators(self, target_url: str) -> List[str]:
        """Check main page for admin interface indicators."""
        indicators_found = []
        
        try:
            result = await self.http_client.get(target_url)
            content = result["content"].lower()
            
            for indicator in self.admin_indicators:
                if indicator in content:
                    idx = content.index(indicator)
                    snippet = content[max(0, idx-20):idx+20]
                    self._debug(f"Found indicator '{indicator}' in: ...{snippet}...", context="admin_scanner", emoji="🔎")
                    indicators_found.append(f"Found indicator: {indicator}")
            
            # Check for admin links in HTML
            admin_links = re.findall(r'href=["\']([^"\']*admin[^"\']*)["\']', content, re.IGNORECASE)
            for link in admin_links:
                self._debug(f"Admin link found in HTML: {link}", context="admin_scanner", emoji="🔗")
                indicators_found.append(f"Admin link found: {link}")
                
        except Exception as e:
            if self.config.get('verbose', False):
                self._debug(f"Error checking main page indicators: {e}\n{traceback.format_exc()}", context="admin_scanner", emoji="💥")
        
        return indicators_found

    def _is_login_successful(self, result: Dict[str, Any]) -> bool:
        """Check if login attempt was successful."""
        if result["status"] == 302:  # Redirect after successful login
            return True
        
        content = result["content"].lower()
        
        # Check for success indicators
        success_indicators = [
            "welcome",
            "dashboard",
            "manage applications",
            "design applications",
            "logout",
            "admin panel"
        ]
        
        # Check for failure indicators
        failure_indicators = [
            "invalid",
            "incorrect",
            "failed",
            "error",
            "login failed",
            "authentication failed"
        ]
        
        # If we see success indicators and no failure indicators
        has_success = any(indicator in content for indicator in success_indicators)
        has_failure = any(indicator in content for indicator in failure_indicators)
        
        return has_success and not has_failure

    def _create_vulnerability(self, title: str, risk: str, description: str, 
                            evidence: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a vulnerability dictionary."""
        return {
            "title": title,
            "risk": risk,
            "description": description,
            "evidence": evidence,
            "metadata": metadata,
            "scanner": "admin_scanner"
        } 