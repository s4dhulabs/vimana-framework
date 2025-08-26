# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-2py scanner info disclosure scanner
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import re
import datetime
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse

class InfoDisclosureScanner:
    """
    Scanner for Web2py information disclosure vulnerabilities.
    Detects sensitive data exposure in error pages, configuration files, and debug info.
    """
    def __init__(self, http_client, config: Dict[str, Any]):
        self.http_client = http_client
        self.config = config
        self.debug_fn = config.get('debug_fn', print)

        # Patterns for sensitive data and error leaks
        self.sensitive_patterns = [
            r'admin@example.com',
            r'admin123',
            r'vulnerable_secret_key_\w+',
            r'sqlite://storage.sqlite',
            r'applications/welcome/databases/storage.sqlite',
            r'Web2py Version: [\d.]+',
            r'Python Version: [^<\n]+',
            r'Debug Mode: True',
            r'Secret Key: [^<\n]+',
            r'Database URL: [^<\n]+',
            r'Admin Credentials: [^<\n]+',
            r'current_directory',
            r'file_permissions',
            r'stack_trace',
            r'debug_info',
            r'session_id[\w\-]*',
            r'leaked in URL',
            r'leaked in JS',
            r'leaked in HTML',
        ]
        self.error_patterns = [
            r'error_message',
            r'stack_trace',
            r'debug_info',
            r'sql_query',
            r'File Error',
            r'Database Error',
            r'This is a test error for security testing',
            r'No such file or directory',
            r'does not exist',
            r'Full stack trace',
            r'Debug information',
            r'Exception',
            r'Traceback',
        ]
        # For reporting which endpoints leak what
        self.sensitive_data = []
        self.error_pages = []
        self.tests_performed = []

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

    def _create_vuln(self, title: str, risk: str, description: str, evidence: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": title,
            "risk": risk,
            "description": description,
            "evidence": evidence,
            "metadata": metadata,
            "scanner": "info_disclosure_scanner"
        }

    async def _discover_endpoints(self, target_url: str, max_depth: int = 2, max_pages: int = 30, debug: bool = False) -> List[str]:
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
                resp = await self.http_client.get(url)
                self._debug(f"[HTTP][GET] {path} -> {resp['status']}", context="discovery", emoji="🌐")
                if resp["status"] >= 400:
                    continue
                endpoints.add(path)
                # Extract links
                for link in re.findall(r'href=["\'](.*?)["\']', resp.get("content", "")):
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

    def _find_patterns(self, content: str, patterns: List[str], endpoint: str, pattern_type: str) -> List[str]:
        findings = []
        for pat in patterns:
            matches = list(re.finditer(pat, content, re.IGNORECASE))
            if matches:
                for m in matches:
                    snippet = content[max(0, m.start()-40):m.end()+40]
                    findings.append(f"Pattern '{pat}' found: ...{snippet}...")
                self._debug(f"{pattern_type} pattern '{pat}' matched {len(matches)} time(s) at {endpoint}", context="pattern_match", emoji="🧩")
                self.tests_performed.append({
                    "endpoint": endpoint,
                    "pattern": pat,
                    "pattern_type": pattern_type,
                    "matches": len(matches)
                })
            else:
                self._debug(f"{pattern_type} pattern '{pat}' not found at {endpoint}", context="pattern_match", emoji="🔎")
                self.tests_performed.append({
                    "endpoint": endpoint,
                    "pattern": pat,
                    "pattern_type": pattern_type,
                    "matches": 0
                })
        return findings

    async def scan(self, target_url: str) -> Dict[str, Any]:
        vulnerabilities = []
        debug = self.config.get("verbose", False)
        discovered_endpoints = []
        self.sensitive_data = []
        self.error_pages = []
        self.tests_performed = []
        try:
            self._debug("Starting info disclosure scanner phase...", context="info_disclosure", emoji="🔎")
            discovered_endpoints = await self._discover_endpoints(target_url, debug=debug)
            if debug:
                self._debug("Discovered endpoints:", context="discovery", emoji="🔍")
                for ep in discovered_endpoints:
                    self._debug(f"  - {ep}", context="discovery")
            # Always add /error and /404 for explicit error checks
            test_endpoints = set(discovered_endpoints)
            test_endpoints.update(["/error", "/error?type=database", "/error?type=file", "/error?type=general", "/404", "/leak_session"])
            for ep in sorted(test_endpoints):
                url = urljoin(target_url, ep)
                try:
                    resp = await self.http_client.get(url)
                    content = resp.get("content", "")
                    status = resp.get("status", 0)
                    self._debug(f"Testing endpoint {ep} (status {status})", context="scan", emoji="🧪")
                    # Sensitive data patterns
                    sens = self._find_patterns(content, self.sensitive_patterns, ep, "Sensitive")
                    if sens:
                        self.sensitive_data.append({"endpoint": ep, "findings": sens})
                        vulnerabilities.append(self._create_vuln(
                            "Sensitive Data Exposure",
                            "high",
                            f"Sensitive data found at {ep}",
                            sens,
                            {"endpoint": ep, "cwe": "CWE-200"}
                        ))
                    # Error/info leak patterns
                    errs = self._find_patterns(content, self.error_patterns, ep, "Error/Debug")
                    if errs:
                        self.error_pages.append({"endpoint": ep, "findings": errs})
                        vulnerabilities.append(self._create_vuln(
                            "Error/Debug Information Disclosure",
                            "medium",
                            f"Error/debug info found at {ep}",
                            errs,
                            {"endpoint": ep, "cwe": "CWE-209"}
                        ))
                    # Generic stack trace/exception
                    if re.search(r'Traceback|Exception|Error:', content, re.IGNORECASE):
                        snippet = re.search(r'(Traceback.*?\n.*?\n.*?\n)', content, re.IGNORECASE)
                        msg = snippet.group(1) if snippet else content[:120]
                        self.error_pages.append({"endpoint": ep, "findings": [msg]})
                        vulnerabilities.append(self._create_vuln(
                            "Stack Trace/Exception Disclosure",
                            "medium",
                            f"Stack trace or exception found at {ep}",
                            [msg],
                            {"endpoint": ep, "cwe": "CWE-209"}
                        ))
                        self._debug(f"Stack trace/exception found at {ep}", context="scan", emoji="💥")
                        if debug:
                            snippet_lines = msg.splitlines()
                            snippet_preview = '\n'.join(snippet_lines[:6]) if snippet_lines else msg
                            self._debug(f"    Exception snippet:\n{snippet_preview}", context="scan")
                        self.tests_performed.append({
                            "endpoint": ep,
                            "pattern": "Traceback|Exception|Error:",
                            "pattern_type": "StackTrace/Exception",
                            "matches": 1
                        })
                    else:
                        self.tests_performed.append({
                            "endpoint": ep,
                            "pattern": "Traceback|Exception|Error:",
                            "pattern_type": "StackTrace/Exception",
                            "matches": 0
                        })
                except Exception as e:
                    self._debug(f"Error scanning {ep}: {e}", context="info_disclosure", emoji="⚠️")
                    continue
            self._debug(f"Total tests performed: {len(self.tests_performed)}", context="summary", emoji="📊")
        except Exception as e:
            self._debug(f"Info disclosure scanner error: {str(e)}", context="info_disclosure", emoji="⚠️")
            vulnerabilities.append(self._create_vuln(
                "Info Disclosure Scanner Error",
                "medium",
                f"Error during info disclosure scanning: {str(e)}",
                [f"Scanner error: {str(e)}"],
                {"error": str(e)}
            ))
        return {
            "scope": discovered_endpoints,
            "vulnerabilities": vulnerabilities,
            "sensitive_data": self.sensitive_data,
            "error_pages": self.error_pages,
            "tests_performed": self.tests_performed
        } 