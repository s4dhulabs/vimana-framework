# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-2py scanner csrf scanner
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import re
import datetime
import random
import string
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse, parse_qs


class CSRFScanner:
    """
    Scanner for Web2py CSRF protection vulnerabilities.
    
    Detects CSRF token bypasses and weak CSRF protection mechanisms.
    """
    
    def __init__(self, http_client, config: Dict[str, Any]):
        self.http_client = http_client
        self.config = config
        self.debug_fn = config.get('debug_fn', print)
        
        # CSRF token patterns to look for
        self.csrf_patterns = [
            # Web2py specific CSRF tokens
            r'name=["\']_formkey["\']\s+value=["\']([^"\']+)["\']',
            r'name=["\']_formname["\']\s+value=["\']([^"\']+)["\']',
            r'_formkey["\']?\s*:\s*["\']([^"\']+)["\']',
            r'_formname["\']?\s*:\s*["\']([^"\']+)["\']',
            r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']',
            r'csrf["\']?\s*:\s*["\']([^"\']+)["\']',
            
            # Generic CSRF token patterns
            r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']',
            r'name=["\']csrf["\']\s+value=["\']([^"\']+)["\']',
            r'name=["\']token["\']\s+value=["\']([^"\']+)["\']',
            r'name=["\']authenticity_token["\']\s+value=["\']([^"\']+)["\']',
            r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']',
            r'name=["\']security_token["\']\s+value=["\']([^"\']+)["\']',
            
            # Hidden input patterns
            r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']*token[^"\']*)["\'][^>]*value=["\']([^"\']+)["\']',
            r'<input[^>]*type=["\']hidden["\'][^>]*value=["\']([^"\']+)["\'][^>]*name=["\']([^"\']*token[^"\']*)["\']',
            
            # Meta tag patterns
            r'<meta[^>]*name=["\']csrf-token["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']csrf["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*name=["\']token["\'][^>]*content=["\']([^"\']+)["\']',
            
            # JavaScript patterns
            r'csrfToken["\']?\s*=\s*["\']([^"\']+)["\']',
            r'token["\']?\s*=\s*["\']([^"\']+)["\']',
            r'csrf["\']?\s*=\s*["\']([^"\']+)["\']',
        ]
        
        # Common form endpoints to test
        self.form_endpoints = [
            '/admin/',
            '/admin/default/login',
            '/admin/default/logout',
            '/admin/default/change_password',
            '/admin/default/register',
            '/admin/default/profile',
            '/welcome/default/login',
            '/welcome/default/logout',
            '/welcome/default/register',
            '/welcome/default/profile',
            '/welcome/default/contact',
            '/welcome/default/submit',
            '/default/login',
            '/default/logout',
            '/default/register',
            '/default/profile',
            '/default/contact',
            '/default/submit',
            '/user/login',
            '/user/logout',
            '/user/register',
            '/user/profile',
            '/auth/login',
            '/auth/logout',
            '/auth/register',
            '/api/login',
            '/api/register',
            '/api/profile',
            '/api/update',
            '/api/delete',
        ]
        
        # HTTP methods that should have CSRF protection
        self.csrf_protected_methods = ['POST', 'PUT', 'DELETE', 'PATCH']
        
        # For reporting findings
        self.csrf_tokens = []
        self.csrf_tests = []
        self.vulnerabilities = []
        self.forms_discovered = []

    def _debug(self, message: str, context: str = None, emoji: str = None):
        """Debug logging function."""
        if not self.config.get("verbose", False):
            return
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[DEBUG]"
        if context:
            prefix += f"[{context}]"
        if emoji:
            prefix += f" {emoji}"
        self.debug_fn(f"{ts} {prefix} {message}")

    def _create_vuln(self, title: str, risk: str, description: str, evidence: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a vulnerability report."""
        return {
            "title": title,
            "risk": risk,
            "description": description,
            "evidence": evidence,
            "metadata": metadata,
            "scanner": "csrf_scanner"
        }

    def _extract_csrf_tokens(self, content: str, url: str) -> List[Dict[str, str]]:
        """Extract CSRF tokens from HTML content."""
        tokens = []
        for pattern in self.csrf_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle patterns with multiple groups
                    if len(match) == 2:
                        token_name, token_value = match
                        if token_value and len(token_value) > 5:  # Basic validation
                            tokens.append({
                                "name": token_name,
                                "value": token_value,
                                "pattern": pattern,
                                "url": url
                            })
                else:
                    # Handle patterns with single group
                    if match and len(match) > 5:  # Basic validation
                        tokens.append({
                            "name": "csrf_token",
                            "value": match,
                            "pattern": pattern,
                            "url": url
                        })
        return tokens

    def _extract_forms(self, content: str, url: str) -> List[Dict[str, Any]]:
        """Extract forms from HTML content."""
        forms = []
        # More flexible regex that matches forms with action and method attributes in any order
        form_pattern = r'<form[^>]*method=["\']([^"\']*)["\'][^>]*action=["\']([^"\']*)["\'][^>]*>|<form[^>]*action=["\']([^"\']*)["\'][^>]*method=["\']([^"\']*)["\'][^>]*>'
        matches = re.findall(form_pattern, content, re.IGNORECASE)
        
        for match in matches:
            # Handle both patterns: method first or action first
            if match[0] and match[1]:  # method first
                method, action = match[0], match[1]
            elif match[2] and match[3]:  # action first
                action, method = match[2], match[3]
            else:
                continue
                
            if method.upper() in self.csrf_protected_methods:
                # Extract form action URL
                if action.startswith('/'):
                    form_url = urljoin(url, action)
                elif action.startswith('http'):
                    form_url = action
                else:
                    form_url = urljoin(url, action)
                
                forms.append({
                    "action": form_url,
                    "method": method.upper(),
                    "source_url": url
                })
        
        return forms

    def _generate_fake_token(self) -> str:
        """Generate a fake CSRF token for testing."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def _generate_empty_token(self) -> str:
        """Generate an empty token for testing."""
        return ""

    def _generate_null_token(self) -> str:
        """Generate a null token for testing."""
        return "null"

    async def _test_csrf_protection(self, target_url: str, form: Dict[str, Any], original_token: str = None) -> Dict[str, Any]:
        """Test CSRF protection for a specific form."""
        test_results = []
        
        # Test cases for CSRF bypass
        test_cases = [
            {
                "name": "no_token",
                "token": None,
                "description": "Request without CSRF token"
            },
            {
                "name": "empty_token",
                "token": "",
                "description": "Request with empty CSRF token"
            },
            {
                "name": "null_token",
                "token": "null",
                "description": "Request with null CSRF token"
            },
            {
                "name": "fake_token",
                "token": self._generate_fake_token(),
                "description": "Request with fake CSRF token"
            },
            {
                "name": "short_token",
                "token": "abc",
                "description": "Request with short CSRF token"
            },
            {
                "name": "same_token_reuse",
                "token": original_token,
                "description": "Request reusing the same CSRF token"
            } if original_token else None,
            {
                "name": "modified_token",
                "token": original_token + "modified" if original_token else "modified",
                "description": "Request with modified CSRF token"
            },
            {
                "name": "token_in_header",
                "token": original_token,
                "description": "Request with CSRF token in header instead of body",
                "use_header": True
            },
            {
                "name": "token_in_url",
                "token": original_token,
                "description": "Request with CSRF token in URL parameter",
                "use_url": True
            }
        ]
        
        # Remove None test cases
        test_cases = [tc for tc in test_cases if tc is not None]
        
        for test_case in test_cases:
            try:
                self._debug(f"Testing CSRF bypass: {test_case['name']}", context="csrf_test", emoji="🛡️")
                
                # Prepare request data
                data = {}
                headers = {}
                url = form["action"]
                
                # Add CSRF token based on test case
                if test_case.get("use_header"):
                    # Put token in header
                    headers["X-CSRF-Token"] = test_case["token"]
                elif test_case.get("use_url"):
                    # Put token in URL
                    if "?" in url:
                        url += f"&csrf_token={test_case['token']}"
                    else:
                        url += f"?csrf_token={test_case['token']}"
                elif test_case["token"] is not None:
                    # Put token in form data
                    data["_formkey"] = test_case["token"]
                    data["_formname"] = "test_form"
                
                # Make the request
                if form["method"] == "POST":
                    response = await self.http_client.post(url, data=data, headers=headers)
                elif form["method"] == "PUT":
                    response = await self.http_client.post(url, data=data, headers=headers)  # PUT via POST
                elif form["method"] == "DELETE":
                    response = await self.http_client.post(url, data=data, headers=headers)  # DELETE via POST
                else:
                    response = await self.http_client.get(url, headers=headers)
                
                # Analyze response
                status = response.get("status", 0)
                content = response.get("content", "")
                
                # Check if request was successful (potential CSRF bypass)
                is_successful = (
                    status == 200 and 
                    not any(error in content.lower() for error in [
                        "csrf", "token", "forbidden", "unauthorized", "invalid", "error"
                    ])
                )
                
                # Check for specific success indicators
                success_indicators = [
                    "success", "welcome", "dashboard", "profile", "logged in",
                    "redirect", "location", "set-cookie"
                ]
                
                has_success_indicators = any(
                    indicator in content.lower() or 
                    indicator in response.get("headers", {}).get("location", "").lower()
                    for indicator in success_indicators
                )
                
                test_result = {
                    "test_name": test_case["name"],
                    "description": test_case["description"],
                    "url": url,
                    "method": form["method"],
                    "status": status,
                    "is_successful": is_successful,
                    "has_success_indicators": has_success_indicators,
                    "content_length": len(content),
                    "response_preview": content[:200] if content else ""
                }
                
                test_results.append(test_result)
                
                # Check if this indicates a CSRF vulnerability
                if is_successful or has_success_indicators:
                    self._debug(f"POTENTIAL CSRF BYPASS: {test_case['name']} succeeded", context="vuln", emoji="💥")
                
            except Exception as e:
                self._debug(f"Error in CSRF test {test_case['name']}: {e}", context="csrf_test", emoji="⚠️")
                test_results.append({
                    "test_name": test_case["name"],
                    "description": test_case["description"],
                    "error": str(e),
                    "url": form["action"],
                    "method": form["method"]
                })
        
        return {
            "form": form,
            "test_results": test_results,
            "vulnerable": any(tr.get("is_successful", False) or tr.get("has_success_indicators", False) for tr in test_results)
        }

    async def _discover_forms(self, target_url: str) -> List[Dict[str, Any]]:
        """Discover forms on the target website."""
        discovered_forms = []
        
        # Test common form endpoints
        for endpoint in self.form_endpoints:
            try:
                url = urljoin(target_url, endpoint)
                response = await self.http_client.get(url)
                
                if response.get("status") == 200:
                    content = response.get("content", "")
                    forms = self._extract_forms(content, url)
                    discovered_forms.extend(forms)
                    
            except Exception as e:
                self._debug(f"Error discovering forms at {endpoint}: {e}", context="discovery", emoji="⚠️")
                continue
        
        # Try to discover forms through crawling
        try:
            main_response = await self.http_client.get(target_url)
            if main_response.get("status") == 200:
                content = main_response.get("content", "")
                forms = self._extract_forms(content, target_url)
                discovered_forms.extend(forms)
        except Exception as e:
            self._debug(f"Error discovering forms on main page: {e}", context="discovery", emoji="⚠️")
        
        return list({form["action"]: form for form in discovered_forms}.values())  # Remove duplicates

    async def scan(self, target_url: str) -> Dict[str, Any]:
        """
        Scan target for CSRF protection vulnerabilities.
        
        Args:
            target_url: Target URL to scan
            
        Returns:
            Dictionary containing scan results and vulnerabilities
        """
        self.csrf_tokens = []
        self.csrf_tests = []
        self.vulnerabilities = []
        self.forms_discovered = []
        
        try:
            self._debug("Starting CSRF scanner phase...", context="csrf_scanner", emoji="🛡️")
            
            # Discover forms
            discovered_forms = await self._discover_forms(target_url)
            self._debug(f"Discovered {len(discovered_forms)} forms", context="discovery", emoji="🔍")
            
            # Extract CSRF tokens from discovered forms
            for form in discovered_forms:
                try:
                    response = await self.http_client.get(form["source_url"])
                    if response.get("status") == 200:
                        content = response.get("content", "")
                        tokens = self._extract_csrf_tokens(content, form["source_url"])
                        self.csrf_tokens.extend(tokens)
                        
                        if tokens:
                            self._debug(f"Found {len(tokens)} CSRF tokens in {form['action']}", context="token_discovery", emoji="🔑")
                        else:
                            self._debug(f"No CSRF tokens found in {form['action']}", context="token_discovery", emoji="⚠️")
                            
                except Exception as e:
                    self._debug(f"Error extracting tokens from {form['action']}: {e}", context="token_discovery", emoji="⚠️")
                    continue
            
            # Test CSRF protection for each form
            for form in discovered_forms:
                self._debug(f"Testing CSRF protection for {form['action']}", context="csrf_test", emoji="🧪")
                
                # Get original token for this form
                original_token = None
                for token in self.csrf_tokens:
                    if token["url"] == form["source_url"]:
                        original_token = token["value"]
                        break
                
                # Test CSRF protection
                test_result = await self._test_csrf_protection(target_url, form, original_token)
                self.csrf_tests.append(test_result)
                
                # Check for vulnerabilities
                if test_result["vulnerable"]:
                    vulnerable_tests = [
                        tr for tr in test_result["test_results"] 
                        if tr.get("is_successful", False) or tr.get("has_success_indicators", False)
                    ]
                    
                    if vulnerable_tests:
                        evidence = []
                        for vt in vulnerable_tests:
                            evidence.append(f"Test '{vt['test_name']}': {vt['description']}")
                            evidence.append(f"Status: {vt['status']}")
                            evidence.append(f"URL: {vt['url']}")
                        
                        self.vulnerabilities.append(self._create_vuln(
                            "CSRF Protection Bypass",
                            "high",
                            f"CSRF protection can be bypassed on {form['action']}",
                            evidence,
                            {
                                "endpoint": form["action"],
                                "method": form["method"],
                                "vulnerable_tests": [vt["test_name"] for vt in vulnerable_tests],
                                "cwe": "CWE-352"
                            }
                        ))
                        self._debug(f"HIGH: CSRF bypass possible on {form['action']}", context="vuln", emoji="💥")
            
            # Check for missing CSRF tokens
            forms_without_tokens = [
                form for form in discovered_forms
                if not any(token["url"] == form["source_url"] for token in self.csrf_tokens)
            ]
            
            if forms_without_tokens:
                evidence = [f"Form: {form['action']} (Method: {form['method']})" for form in forms_without_tokens]
                self.vulnerabilities.append(self._create_vuln(
                    "Missing CSRF Protection",
                    "medium",
                    f"Forms found without CSRF tokens",
                    evidence,
                    {
                        "forms_affected": len(forms_without_tokens),
                        "cwe": "CWE-352"
                    }
                ))
                self._debug(f"MEDIUM: {len(forms_without_tokens)} forms without CSRF tokens", context="vuln", emoji="⚠️")
            
            # Check for weak CSRF tokens
            weak_tokens = [
                token for token in self.csrf_tokens
                if len(token["value"]) < 16 or token["value"] in ["test", "123", "token", "csrf"]
            ]
            
            if weak_tokens:
                evidence = [f"Token: {token['value']} (Length: {len(token['value'])})" for token in weak_tokens]
                self.vulnerabilities.append(self._create_vuln(
                    "Weak CSRF Tokens",
                    "medium",
                    "Weak or predictable CSRF tokens detected",
                    evidence,
                    {
                        "weak_tokens_count": len(weak_tokens),
                        "cwe": "CWE-352"
                    }
                ))
                self._debug(f"MEDIUM: {len(weak_tokens)} weak CSRF tokens found", context="vuln", emoji="🔓")
            
            self._debug(f"CSRF scanner completed. Found {len(self.vulnerabilities)} vulnerabilities", context="summary", emoji="📊")
            
        except Exception as e:
            self._debug(f"CSRF scanner error: {str(e)}", context="csrf_scanner", emoji="⚠️")
            self.vulnerabilities.append(self._create_vuln(
                "CSRF Scanner Error",
                "medium",
                f"Error during CSRF scanning: {str(e)}",
                [f"Scanner error: {str(e)}"],
                {"error": str(e)}
            ))
        
        return {
            "vulnerabilities": self.vulnerabilities,
            "csrf_tokens": self.csrf_tokens,
            "csrf_tests": self.csrf_tests,
            "forms_discovered": discovered_forms
        } 