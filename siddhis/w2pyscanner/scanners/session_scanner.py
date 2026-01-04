#!/usr/bin/env python3
#  __ _
#   \/imana 2016
#   [|-2py scanner
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import re
import math
import asyncio
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse
import datetime

class SessionScanner:
    """
    Advanced Session Management Vulnerability Scanner for Web2py Applications
    """
    def __init__(self, http_client, config: Dict[str, Any]):
        self.http_client = http_client
        self.config = config
        self.session_endpoints = ["/profile", "/session_test"]
        self.login_endpoint = "/login"
        self.logout_endpoint = "/logout"
        self.test_user = {
            "email": config.get("session_user", "admin@example.com"),
            "password": config.get("session_pass", "admin123")
        }
        self.session_timeout = int(config.get("session_timeout", 0))  # seconds, 0 disables
        self.debug_fn = config.get('debug_fn', print)

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

    async def _discover_endpoints(self, target_url: str, session_cookie: Optional[str], max_depth: int = 2, max_pages: int = 30, debug: bool = False) -> List[str]:
        """Crawl the site starting from /, following internal links, and collect endpoints."""
        self._debug("Starting endpoint discovery...", context="discovery", emoji="🔍")
        visited: Set[str] = set()
        to_visit: List[tuple] = [("/", 0)]
        endpoints: Set[str] = set()
        base_netloc = urlparse(target_url).netloc
        while to_visit and len(visited) < max_pages:
            path, depth = to_visit.pop(0)
            if path in visited or depth > max_depth:
                continue
            visited.add(path)
            url = urljoin(target_url, path)
            try:
                resp = await self.http_client.get(url, cookies={"session_id": session_cookie} if session_cookie else None)
                self._debug(f"[HTTP][GET] {path} -> {resp['status']}", context="discovery", emoji="🌐")
                if resp["status"] >= 400:
                    continue
                endpoints.add(path)
                # Extract links
                for link in re.findall(r'href=["\"](.*?)["\"]', resp.get("content", "")):
                    parsed = urlparse(link)
                    if parsed.netloc and parsed.netloc != base_netloc:
                        continue  # external
                    if not parsed.path.startswith("/"):
                        continue  # skip fragments, mailto, etc
                    if parsed.path not in visited:
                        to_visit.append((parsed.path, depth + 1))
            except Exception as e:
                self._debug(f"Discovery error on {url}: {e}", context="discovery", emoji="⚠️")
                continue
        self._debug(f"Discovery complete: {len(endpoints)} endpoints found.", context="discovery", emoji="🔍")
        return sorted(endpoints)

    async def scan(self, target_url: str) -> Dict[str, Any]:
        vulnerabilities = []
        debug = self.config.get("verbose", False)
        discovered_endpoints = []
        try:
            self._debug("Starting session scanner phase...", context="session_scanner", emoji="🚦")
            # 0. Endpoint discovery
            login_result = await self._login(target_url, debug=debug)
            session_cookie = login_result.get("session_cookie")
            discovered_endpoints = await self._discover_endpoints(target_url, session_cookie, debug=debug)
            if debug:
                self._debug("Discovered endpoints:", context="discovery", emoji="🔍")
                for ep in discovered_endpoints:
                    self._debug(f"  - {ep}", context="discovery")
            # 1. Unauthenticated access to protected endpoint
            unauth_resp = await self.http_client.get(urljoin(target_url, "/profile"), allow_redirects=False)
            self._debug(f"[HTTP][GET] /profile -> {unauth_resp['status']}", context="session_scanner", emoji="🌐")
            unauth_status = unauth_resp["status"]
            if debug:
                self._debug(f"[DEBUG] Unauthenticated /profile status: {unauth_status}", context="session_scanner", emoji="🌐")
            if unauth_status == 200:
                vulnerabilities.append(self._create_vuln(
                    "Profile Accessible Without Authentication",
                    "high",
                    "The /profile endpoint is accessible without authentication.",
                    ["/profile returned 200 without login"],
                    {"endpoint": "/profile", "cwe": "CWE-284"}
                ))
            set_cookie_header = login_result.get("set_cookie")
            if debug:
                self._debug(f"[DEBUG] Login session_id: {session_cookie}", context="session_scanner", emoji="🔑")
                self._debug(f"[DEBUG] Set-Cookie header: {set_cookie_header}", context="session_scanner", emoji="🍪")
                self._debug(f"[DEBUG] All headers from login response: {login_result.get('headers', {})}", context="session_scanner", emoji="��")
            # 3. Analyze session cookie flags
            cookie_flags = self._analyze_cookie_flags(set_cookie_header)
            missing_flags = [flag for flag, present in cookie_flags.items() if not present]
            if missing_flags:
                vulnerabilities.append(self._create_vuln(
                    "Session Cookie Missing Security Flags",
                    "high",
                    f"Session cookie is missing flags: {', '.join(missing_flags)}",
                    [f"Set-Cookie: {set_cookie_header}"],
                    {"flags": cookie_flags, "cwe": "CWE-614"}
                ))
            # 4. Entropy/length check
            if session_cookie:
                entropy = self._shannon_entropy(session_cookie)
                if debug:
                    self._debug(f"[DEBUG] Session ID entropy: {entropy:.2f}, length: {len(session_cookie)}", context="session_scanner", emoji="🔑")
                if len(session_cookie) < 16 or entropy < 3.5:
                    vulnerabilities.append(self._create_vuln(
                        "Weak Session ID",
                        "high",
                        f"Session ID is too short or has low entropy (entropy={entropy:.2f}, length={len(session_cookie)})",
                        [f"Session ID: {session_cookie}"],
                        {"entropy": entropy, "length": len(session_cookie), "cwe": "CWE-330"}
                    ))
            # 5. Authenticated access to protected endpoint
            auth_resp = await self.http_client.get(urljoin(target_url, "/profile"), cookies={"session_id": session_cookie}, allow_redirects=False)
            self._debug(f"[HTTP][GET] /profile -> {auth_resp['status']}", context="session_scanner", emoji="🔑")
            auth_status = auth_resp["status"]
            if debug:
                self._debug(f"[DEBUG] Authenticated /profile status: {auth_status}", context="session_scanner", emoji="🔑")
            if auth_status != 200:
                vulnerabilities.append(self._create_vuln(
                    "Authenticated Profile Access Failed",
                    "high",
                    "Could not access /profile after login.",
                    [f"/profile returned {auth_status} after login"],
                    {"endpoint": "/profile", "cwe": "CWE-287"}
                ))
            # 6. Session fixation
            fixation_result = await self._test_session_fixation(target_url, debug=debug)
            if fixation_result["fixation"]:
                vulnerabilities.append(self._create_vuln(
                    "Session Fixation Vulnerability",
                    "high",
                    "Session fixation is possible: server accepts attacker-supplied session ID.",
                    ["Session ID was set before login and reused after login."],
                    {"cwe": "CWE-384"}
                ))
            # 7. Session timeout test
            if self.session_timeout > 0 and session_cookie:
                if debug:
                    self._debug(f"[DEBUG] Waiting {self.session_timeout}s to test session timeout...", context="session_scanner", emoji="⏳")
                await asyncio.sleep(self.session_timeout)
                timeout_resp = await self.http_client.get(urljoin(target_url, "/profile"), cookies={"session_id": session_cookie}, allow_redirects=False)
                self._debug(f"[HTTP][GET] /profile -> {timeout_resp['status']}", context="session_scanner", emoji="⏳")
                timeout_status = timeout_resp["status"]
                if debug:
                    self._debug(f"[DEBUG] /profile after timeout status: {timeout_status}", context="session_scanner", emoji="⏳")
                if timeout_status == 200:
                    vulnerabilities.append(self._create_vuln(
                        "Session Timeout Not Enforced",
                        "medium",
                        f"Session is still valid after {self.session_timeout}s (should expire)",
                        [f"/profile returned 200 after {self.session_timeout}s"],
                        {"timeout": self.session_timeout, "cwe": "CWE-613"}
                    ))
            # 8. Session exposure in URLs/HTML/JS
            exposure_findings = await self._test_session_exposure(target_url, session_cookie, debug=debug, endpoints=discovered_endpoints)
            vulnerabilities.extend(exposure_findings)
        except Exception as e:
            self._debug(f"Session scanner error: {str(e)}", context="session_scanner", emoji="⚠️")
            vulnerabilities.append(self._create_vuln(
                "Session Scanner Error",
                "medium",
                f"Error during session scanning: {str(e)}",
                [f"Scanner error: {str(e)}"],
                {"error": str(e)}
            ))
        return {"scope": discovered_endpoints, "vulnerabilities": vulnerabilities}

    async def _login(self, target_url: str, debug: bool = False) -> Dict[str, Any]:
        login_url = urljoin(target_url, self.login_endpoint)
        data = self.test_user
        resp = await self.http_client.post(login_url, data=data, allow_redirects=False)
        set_cookie = resp.get("set_cookie", "")
        session_cookie = self._extract_session_id(set_cookie)
        if debug:
            self._debug(f"[DEBUG] _login() got session_id: {session_cookie}", context="login", emoji="🔑")
            self._debug(f"[DEBUG] Set-Cookie header: {set_cookie}", context="login", emoji="🍪")
            self._debug(f"[DEBUG] All headers from login response: {resp.get('headers', {})}", context="login", emoji="📦")
        return {"session_cookie": session_cookie, "set_cookie": set_cookie, "headers": resp.get('headers', {})}

    async def _test_session_exposure(self, target_url: str, session_cookie: Optional[str], debug: bool = False, endpoints: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        findings = []
        # Use discovered endpoints if provided, else fallback to default
        if endpoints is None:
            endpoints = ["/", "/profile", "/about", "/session_test", "/leak_session"]
        session_id_pattern = re.escape(session_cookie) if session_cookie else r"session_id=[a-zA-Z0-9]+"
        regex = re.compile(session_id_pattern)
        for ep in endpoints:
            resp = await self.http_client.get(urljoin(target_url, ep), cookies={"session_id": session_cookie} if session_cookie else None)
            self._debug(f"[HTTP][GET] {ep} -> {resp['status']}", context="exposure", emoji="🌐")
            content = resp.get("content", "")
            url = resp.get("url", ep)
            # Check URL
            if session_cookie and session_cookie in url:
                findings.append(self._create_vuln(
                    "Session ID Exposed in URL",
                    "high",
                    f"Session ID found in URL: {url}",
                    [f"URL: {url}"],
                    {"endpoint": ep, "cwe": "CWE-598"}
                ))
            # Check HTML/JS
            if regex.search(content):
                findings.append(self._create_vuln(
                    "Session ID Exposed in HTML/JS",
                    "high",
                    f"Session ID found in page content at {ep}",
                    [f"Content match: {regex.pattern}"],
                    {"endpoint": ep, "cwe": "CWE-598"}
                ))
        return findings

    def _extract_session_id(self, set_cookie: str) -> Optional[str]:
        match = re.search(r'session_id=([a-zA-Z0-9]+)', set_cookie)
        return match.group(1) if match else None

    def _analyze_cookie_flags(self, set_cookie: str) -> Dict[str, bool]:
        flags = {"HttpOnly": False, "Secure": False, "SameSite": False}
        if not set_cookie:
            return flags
        if "httponly" in set_cookie.lower():
            flags["HttpOnly"] = True
        if "secure" in set_cookie.lower():
            flags["Secure"] = True
        if "samesite" in set_cookie.lower():
            flags["SameSite"] = True
        return flags

    async def _test_session_fixation(self, target_url: str, debug: bool = False) -> Dict[str, Any]:
        fake_session = "attackerfixedsessionid123"
        login_url = urljoin(target_url, self.login_endpoint)
        data = self.test_user
        resp = await self.http_client.post(login_url, data=data, cookies={"session_id": fake_session}, allow_redirects=False)
        set_cookie = resp.get("set_cookie", "")
        session_cookie = self._extract_session_id(set_cookie)
        if debug:
            self._debug(f"[DEBUG] Fixation test: sent {fake_session}, got {session_cookie}", context="fixation", emoji="🔑")
        return {"fixation": session_cookie == fake_session}

    def _shannon_entropy(self, data: str) -> float:
        if not data:
            return 0.0
        entropy = 0
        for x in set(data):
            p_x = float(data.count(x)) / len(data)
            entropy -= p_x * math.log2(p_x)
        return entropy

    def _create_vuln(self, title: str, risk: str, description: str, evidence: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": title,
            "risk": risk,
            "description": description,
            "evidence": evidence,
            "metadata": metadata,
            "scanner": "session_scanner"
        } 