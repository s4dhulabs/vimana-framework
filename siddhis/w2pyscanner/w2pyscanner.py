# -*- coding: utf-8 -*-
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

import asyncio
import json
import sys
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import datetime

# Import scanner modules
from .scanners.admin_scanner import AdminScanner
from .scanners.session_scanner import SessionScanner
from .scanners.upload_scanner import UploadScanner
from .scanners.database_scanner import DatabaseScanner
from .scanners.csrf_scanner import CSRFScanner
from .scanners.info_disclosure import InfoDisclosureScanner
from .utils.http_client import HTTPClient


class siddhi:
    """
    W2PyScanner - Web2py Security Scanner Plugin
    
    A comprehensive security testing tool for Web2py applications that
    identifies common vulnerabilities including admin interface exposure,
    session management issues, file upload vulnerabilities, database
    exposure, CSRF protection bypasses, and information disclosure.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the siddhi handler
        
        Args:
            **kwargs: Optional keyword arguments for configuration from Vimana
        """
        self.name = "W2PyScanner"
        self.description = "Web2py Security Scanner and Vulnerability Assessment Tool"
        self.version = "1.0.0"
        self.author = "s4dhu"
        
        # Store Vimana handler arguments
        self.vmnf_handler = kwargs
        self.config = kwargs.copy()
        self.ci_mode = kwargs.get("ci_mode", False)
        
        # Scanner instances
        self.scanners = {}
        self.http_client = None
        
        # Results storage
        self.results = {
            "targets": [],
            "summary": {
                "total_targets": 0,
                "vulnerable_targets": 0,
                "total_vulnerabilities": 0,
                "scanners_run": []
            }
        }
        
        # Default configuration
        self.default_config = {
            "timeout": 10,
            "max_retries": 3,
            "concurrent": 5,
            "stealth": False,
            "min_delay": 0.5,
            "max_delay": 2.0,
            "user_agent": "W2PyScanner/1.0.0",
            "verbose": False,
            "no_evidence": False,
            "no_metadata": False,
            "summary_only": False
        }
        
        # Scanner configuration
        self.scanner_config = {
            "admin": True,
            "session": True,
            "upload": True,
            "database": True,
            "csrf": True,
            "info_disclosure": True
        }

    def _debug(self, message: str, context: str = None, emoji: str = None):
        # Only print debug messages if verbose or debug is enabled
        if not (self.config.get("verbose", False) or self.config.get("debug", False)):
            return
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[DEBUG]"
        if context:
            prefix += f"[{context}]"
        if emoji:
            prefix += f" {emoji}"
        print(f"{ts} {prefix} {message}")

    def start(self, args=None) -> None:
        """
        Main entry point for the W2PyScanner plugin.
        
        Args:
            args: Not used in Vimana integration, kept for backward compatibility
        """
        try:
            # Parse and validate arguments from vmnf_handler
            self._parse_arguments()
            
            # Initialize HTTP client
            self.http_client = HTTPClient(
                timeout=self.config.get("timeout", self.default_config["timeout"]),
                max_retries=self.config.get("max_retries", self.default_config["max_retries"]),
                user_agent=self.config.get("user_agent", self.default_config["user_agent"]),
                stealth=self.config.get("stealth", self.default_config["stealth"]),
                min_delay=self.config.get("min_delay", self.default_config["min_delay"]),
                max_delay=self.config.get("max_delay", self.default_config["max_delay"])
            )
            
            # Initialize scanners
            self._initialize_scanners()
            
            # Get targets
            targets = self._get_targets()
            if not targets:
                self._print_error("No targets specified. Use --target-url or --file")
                return
            
            # Run scans
            asyncio.run(self._run_scans(targets))
            
            # Generate output
            self._generate_output()
            
        except KeyboardInterrupt:
            self._print_warning("\n[!] Scan interrupted by user")
        except Exception as e:
            self._print_error(f"Error during scan: {str(e)}")
            if self.config.get("verbose", False):
                import traceback
                traceback.print_exc()

    def _parse_arguments(self) -> None:
        """Parse and validate command line arguments from vmnf_handler."""
        # Type-cast and set config keys only if user set them
        for key in ["timeout", "max_retries", "concurrent"]:
            val = self.vmnf_handler.get(key)
            if val is not None:
                self.config[key] = int(val)
        for key in ["min_delay", "max_delay"]:
            val = self.vmnf_handler.get(key)
            if val is not None:
                self.config[key] = float(val)
        if self.vmnf_handler.get("user_agent"):
            self.config["user_agent"] = self.vmnf_handler["user_agent"]
        # Boolean flags
        for flag in [
            "stealth", "verbose", "debug", "no_evidence", "no_metadata", "summary_only",
            "discovery_only", "no_results", "sarif", "ci_mode"
        ]:
            if self.vmnf_handler.get(flag):
                self.config[flag] = True
        # Output files
        for key in ["output", "o", "output_sarif"]:
            val = self.vmnf_handler.get(key)
            if val:
                self.config[key] = val
        # Args list for extra CLI flags
        args_list = self.vmnf_handler.get('args', [])
        if "--sarif" in args_list:
            self.config["sarif"] = True
        for i, arg in enumerate(args_list):
            if arg in ("--output-sarif", "--sarif-output") and i+1 < len(args_list):
                self.config["output_sarif"] = args_list[i+1]
        # Handle --ci-mode
        if self.ci_mode or self.vmnf_handler.get("ci_mode"):
            self.config["verbose"] = True
            self.config["no_results"] = True
            self.config["sarif"] = True
            self.config["output"] = "w2pyscanner_results.json"
        # Merge with defaults so all required keys are present, but do not override with None
        self.config = {**self.default_config, **{k: v for k, v in self.config.items() if v is not None}}
        # Ensure user_agent is always set
        if not self.config.get("user_agent"):
            self.config["user_agent"] = self.default_config["user_agent"]
        # Scanner selection: only/skip
        if self.vmnf_handler.get("admin_only") or "--admin-only" in args_list:
            self._set_single_scanner("admin")
        elif self.vmnf_handler.get("session_only") or "--session-only" in args_list:
            self._set_single_scanner("session")
        elif self.vmnf_handler.get("upload_only") or "--upload-only" in args_list:
            self._set_single_scanner("upload")
        elif self.vmnf_handler.get("db_only") or "--db-only" in args_list:
            self._set_single_scanner("database")
        elif self.vmnf_handler.get("csrf_only") or "--csrf-only" in args_list:
            self._set_single_scanner("csrf")
        elif self.vmnf_handler.get("info_only") or "--info-only" in args_list:
            self._set_single_scanner("info_disclosure")
        else:
            # Skip options
            if self.vmnf_handler.get("skip_admin") or "--skip-admin" in args_list:
                self.scanner_config["admin"] = False
            if self.vmnf_handler.get("skip_session") or "--skip-session" in args_list:
                self.scanner_config["session"] = False
            if self.vmnf_handler.get("skip_upload") or "--skip-upload" in args_list:
                self.scanner_config["upload"] = False
            if self.vmnf_handler.get("skip_db") or "--skip-db" in args_list:
                self.scanner_config["database"] = False
            if self.vmnf_handler.get("skip_csrf") or "--skip-csrf" in args_list:
                self.scanner_config["csrf"] = False
            if self.vmnf_handler.get("skip_info") or "--skip-info" in args_list:
                self.scanner_config["info_disclosure"] = False

    def _set_single_scanner(self, scanner_name: str) -> None:
        """Enable only one scanner and disable all others."""
        for scanner in self.scanner_config:
            self.scanner_config[scanner] = (scanner == scanner_name)

    def _get_targets(self) -> List[str]:
        """Get list of targets from vmnf_handler."""
        targets = []
        
        # Check for single target
        target_url = self.vmnf_handler.get('target_url')
        if target_url:
            targets.append(target_url)
        
        # Check for file with multiple targets (Vimana uses file_scope)
        file_path = self.vmnf_handler.get('file_scope') or self.vmnf_handler.get('file')
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    file_targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    targets.extend(file_targets)
            except FileNotFoundError:
                self._print_error(f"Target file not found: {file_path}")
                return []
            except Exception as e:
                self._print_error(f"Error reading target file: {str(e)}")
                return []
        
        # Validate targets
        valid_targets = []
        for target in targets:
            if self._is_valid_url(target):
                valid_targets.append(target)
            else:
                self._print_warning(f"Invalid URL: {target}")
        
        return valid_targets

    def _is_valid_url(self, url: str) -> bool:
        """Validate if URL is properly formatted."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _initialize_scanners(self) -> None:
        """Initialize scanner instances based on configuration."""
        if self.scanner_config["admin"]:
            self.scanners["admin"] = AdminScanner(self.http_client, self.config)
        if self.scanner_config["session"]:
            self.scanners["session"] = SessionScanner(self.http_client, self.config)
        if self.scanner_config["upload"]:
            self.scanners["upload"] = UploadScanner(self.http_client, self.config)
        if self.scanner_config["database"]:
            self.scanners["database"] = DatabaseScanner(self.http_client, self.config)
        if self.scanner_config["csrf"]:
            self.scanners["csrf"] = CSRFScanner(self.http_client, self.config)
        if self.scanner_config["info_disclosure"]:
            self.scanners["info_disclosure"] = InfoDisclosureScanner(self.http_client, self.config)

    async def _run_scans(self, targets: List[str]) -> None:
        """Run scans against all targets."""
        self._print_banner()
        
        self.results["summary"]["total_targets"] = len(targets)
        self.results["summary"]["scanners_run"] = list(self.scanners.keys())
        
        # Create semaphore for concurrent requests
        semaphore = asyncio.Semaphore(self.config.get("concurrent", self.default_config["concurrent"]))
        
        # Run scans for each target
        tasks = []
        for target in targets:
            task = asyncio.create_task(self._scan_target(target, semaphore))
            tasks.append(task)
        
        # Wait for all scans to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Generate summary
        self._generate_summary()
        
        # Print final summary
        self._print_final_summary()

    async def _scan_target(self, target: str, semaphore: asyncio.Semaphore) -> None:
        async with semaphore:
            print(f"🎯 Scanning target: {target}")
            target_result = {
                "url": target,
                "scope": [],  # Will be filled after discovery
                "scanners": {},
                "vulnerabilities": [],
                "summary": {
                    "total_vulnerabilities": 0,
                    "high_risk": 0,
                    "medium_risk": 0,
                    "low_risk": 0
                }
            }
            discovered_scope = None
            verbose_or_debug = self.config.get("verbose", False) or self.config.get("debug", False) or self.config.get("ci_mode", False)
            if self.config.get("discovery_only", False):
                session_scanner = self.scanners.get("session")
                if session_scanner:
                    if not verbose_or_debug:
                        print("🚦 Starting session scanner...")
                    self._debug("Starting endpoint discovery...", context="discovery", emoji="🔍")
                    login_result = await session_scanner._login(target, debug=self.config.get("verbose", False))
                    session_cookie = login_result.get("session_cookie")
                    discovered_scope = await session_scanner._discover_endpoints(target, session_cookie, debug=self.config.get("verbose", False))
                    target_result["scope"] = discovered_scope
                    self._debug(f"Discovery complete: {len(discovered_scope)} endpoints found.", context="discovery", emoji="🔍")
                    if self.config.get("verbose", False):
                        self._debug("Discovered endpoints:", context="discovery", emoji="🔍")
                        for ep in discovered_scope:
                            self._debug(f"  - {ep}", context="discovery")
                self.results["targets"].append(target_result)
                return
            for scanner_name, scanner in self.scanners.items():
                if not verbose_or_debug:
                    print(f"🚦 Starting {scanner_name} scanner...")
                self._debug(f"Starting {scanner_name} scanner...", context=scanner_name, emoji="🚦")
                try:
                    if self.config.get("verbose", False):
                        self._print_scan_progress(target, scanner_name)
                    scanner_result = await scanner.scan(target)
                    if "scope" in scanner_result:
                        discovered_scope = scanner_result["scope"]
                    scanner_meta = {k: v for k, v in scanner_result.items() if k not in ("vulnerabilities", "scope")}
                    target_result["scanners"][scanner_name] = scanner_meta
                    if "vulnerabilities" in scanner_result:
                        target_result["vulnerabilities"].extend(scanner_result["vulnerabilities"])
                except Exception as e:
                    error_msg = f"Error in {scanner_name} scanner: {str(e)}"
                    self._print_error(f"  {error_msg}")
                    target_result["scanners"][scanner_name] = {"error": error_msg}
            if discovered_scope is not None:
                target_result["scope"] = discovered_scope
            self._calculate_target_summary(target_result)
            self.results["targets"].append(target_result)
            self._print_target_results(target_result)

    def _calculate_target_summary(self, target_result: Dict[str, Any]) -> None:
        """Calculate vulnerability summary for a target."""
        summary = target_result["summary"]
        
        for vuln in target_result["vulnerabilities"]:
            summary["total_vulnerabilities"] += 1
            risk = vuln.get("risk", "low").lower()
            if risk == "high":
                summary["high_risk"] += 1
            elif risk == "medium":
                summary["medium_risk"] += 1
            else:
                summary["low_risk"] += 1

    def _generate_summary(self) -> None:
        """Generate overall scan summary."""
        summary = self.results["summary"]
        
        for target_result in self.results["targets"]:
            if target_result["summary"]["total_vulnerabilities"] > 0:
                summary["vulnerable_targets"] += 1
            summary["total_vulnerabilities"] += target_result["summary"]["total_vulnerabilities"]

    def _print_banner(self) -> None:
        # Minimal, professional plugin banner
        scanners_count = len([k for k, v in self.scanner_config.items() if v])
        print("\n" + "─" * 60)
        print(f"  W2PyScanner | Web2py Security Scanner Plugin")
        print(f"  Version: {self.version}   Author: {self.author}   Scanners: {scanners_count} Active")
        print("─" * 60 + "\n")

    def _print_target_results(self, target_result: Dict[str, Any]) -> None:
        if self.config.get("no_results", False):
            return
        url = target_result["url"]
        summary = target_result["summary"]
        
        if summary["total_vulnerabilities"] == 0:
            print(f"\n🎯 TARGET: {url}")
            print(f"✅ STATUS: No vulnerabilities found")
            return
        
        # Print target header with scan metadata
        print(f"\n🎯 TARGET: {url}")
        print(f"📊 VULNERABILITY SUMMARY: {summary['total_vulnerabilities']} findings")
        
        # Risk breakdown with priority indicators
        risk_breakdown = []
        if summary['high_risk'] > 0:
            risk_breakdown.append(f"🔴 {summary['high_risk']} Critical")
        if summary['medium_risk'] > 0:
            risk_breakdown.append(f"🟡 {summary['medium_risk']} High")
        if summary['low_risk'] > 0:
            risk_breakdown.append(f"🔵 {summary['low_risk']} Medium")
        
        print(f"📈 RISK DISTRIBUTION: {' | '.join(risk_breakdown)}")
        print()
        
        # Print vulnerabilities with enhanced formatting
        for i, vuln in enumerate(target_result["vulnerabilities"], 1):
            self._print_vulnerability_card(vuln, i)

    def _print_vulnerability_card(self, vuln: Dict[str, Any], index: int = 1) -> None:
        """Print a detailed vulnerability card with remediation guidance."""
        risk = vuln.get("risk", "low").lower()
        
        # Risk level indicators with priority
        risk_indicators = {
            "high": ("🔴 CRITICAL", "IMMEDIATE", "This vulnerability requires immediate attention"),
            "medium": ("🟡 HIGH", "HIGH", "This vulnerability should be addressed within 24-48 hours"),
            "low": ("🔵 MEDIUM", "MEDIUM", "This vulnerability should be addressed within 1 week")
        }
        
        risk_indicator, priority, priority_desc = risk_indicators.get(risk, ("⚪ UNKNOWN", "UNKNOWN", "Priority level unknown"))
        
        # Vulnerability card header
        print(f"┌─ VULNERABILITY #{index:02d} ─{'─' * 50}")
        print(f"│ 🚨 {vuln['title']}")
        print(f"│ {risk_indicator} | 🔍 {vuln.get('scanner', 'Unknown')} | ⏰ {priority} PRIORITY")
        print(f"│ {'─' * 70}")
        
        # Description - clean up if it contains endpoint lists
        description = vuln.get('description', 'No description available')
        if "accessible at:" in description and "admin" in vuln.get('scanner', ''):
            # Extract only the actually discovered endpoints from evidence
            evidence = vuln.get('evidence', [])
            discovered_endpoints = [e for e in evidence if e.startswith('Admin endpoint accessible:')]
            if discovered_endpoints:
                endpoint_list = [e.replace('Admin endpoint accessible: ', '') for e in discovered_endpoints]
                description = f"Web2py admin interface endpoints discovered: {len(endpoint_list)} endpoints found"
            else:
                description = "Web2py admin interface is accessible"
        
        print(f"│ 📝 DESCRIPTION:")
        print(f"│    {description}")
        
        # Evidence - format as proper list
        if not self.config.get("no_evidence", False) and "evidence" in vuln:
            print(f"│ 📋 EVIDENCE:")
            evidence = vuln["evidence"]
            
            # Filter and format evidence
            if "admin" in vuln.get('scanner', '') and any(e.startswith('Admin endpoint accessible:') for e in evidence):
                # Show discovered endpoints as a clean list
                endpoints = [e.replace('Admin endpoint accessible: ', '') for e in evidence if e.startswith('Admin endpoint accessible:')]
                for endpoint in endpoints:
                    print(f"│    • {endpoint}")
                
                # Show other evidence
                other_evidence = [e for e in evidence if not e.startswith('Admin endpoint accessible:')]
                for evidence_item in other_evidence:
                    print(f"│    • {evidence_item}")
            else:
                # Regular evidence formatting
                for evidence_item in evidence:
                    print(f"│    • {evidence_item}")
        
        # Metadata
        if not self.config.get("no_metadata", False) and "metadata" in vuln:
            print(f"│ 📊 TECHNICAL DETAILS:")
            for key, value in vuln["metadata"].items():
                if key != "endpoints":  # Don't show raw endpoint list in metadata
                    print(f"│    • {key}: {value}")
        
        # Remediation guidance
        print(f"│ 🔧 REMEDIATION:")
        remediation = self._get_remediation_guidance(vuln)
        for step in remediation:
            print(f"│    • {step}")
        
        # Priority guidance
        print(f"│ ⚡ PRIORITY: {priority_desc}")
        
        print(f"└─{'─' * 70}")

    def _get_remediation_guidance(self, vuln: Dict[str, Any]) -> List[str]:
        """Get specific remediation guidance based on vulnerability type."""
        vuln_type = vuln.get('scanner', '').lower()
        title = vuln.get('title', '').lower()
        
        guidance = {
            'admin_scanner': {
                'default': [
                    "Remove or restrict access to admin interface endpoints",
                    "Implement strong authentication mechanisms",
                    "Use IP whitelisting for admin access",
                    "Enable HTTPS for all admin communications",
                    "Implement rate limiting on admin endpoints"
                ],
                'weak_auth': [
                    "Implement multi-factor authentication (MFA)",
                    "Use strong password policies",
                    "Enable account lockout after failed attempts",
                    "Implement session timeout policies",
                    "Use secure session management"
                ],
                'exposed': [
                    "Move admin interface to non-standard path",
                    "Implement IP-based access restrictions",
                    "Use reverse proxy with authentication",
                    "Disable admin interface in production",
                    "Implement proper access controls"
                ]
            },
            'session_scanner': [
                "Implement secure session management",
                "Use cryptographically strong session IDs",
                "Enable session timeout and expiration",
                "Implement session fixation protection",
                "Use HTTPS for all session communications"
            ],
            'upload_scanner': [
                "Implement strict file type validation",
                "Use allowlist approach for file extensions",
                "Scan uploaded files for malware",
                "Store files outside web root",
                "Implement file size limits"
            ],
            'database_scanner': [
                "Move database files outside web root",
                "Implement proper database access controls",
                "Use environment variables for database credentials",
                "Enable database encryption",
                "Implement connection pooling"
            ],
            'csrf_scanner': [
                "Implement CSRF tokens on all forms",
                "Use SameSite cookie attributes",
                "Validate request origin headers",
                "Implement proper session management",
                "Use framework CSRF protection features"
            ],
            'info_disclosure': [
                "Disable detailed error messages in production",
                "Remove sensitive information from responses",
                "Implement proper logging without sensitive data",
                "Use generic error messages",
                "Review and sanitize all output"
            ]
        }
        
        # Get specific guidance based on vulnerability type
        if vuln_type in guidance:
            if isinstance(guidance[vuln_type], dict):
                # Check for specific guidance based on title
                for key, steps in guidance[vuln_type].items():
                    if key in title or key == 'default':
                        return steps
                return guidance[vuln_type].get('default', [])
            else:
                return guidance[vuln_type]
        
        return [
            "Review the vulnerability details",
            "Implement appropriate security controls",
            "Test the fix thoroughly",
            "Document the remediation steps",
            "Monitor for similar issues"
        ]

    def _print_final_summary(self) -> None:
        if self.config.get("no_results", False):
            return
        summary = self.results["summary"]
        
        print(f"\n📊 SCAN SUMMARY REPORT")
        print(f"─" * 50)
        print(f"🎯 Total Targets Scanned: {summary['total_targets']}")
        print(f"🔴 Vulnerable Targets: {summary['vulnerable_targets']}")
        print(f"🚨 Total Vulnerabilities Found: {summary['total_vulnerabilities']}")
        print(f"🔧 Scanners Used: {', '.join(summary['scanners_run'])}")
        
        # Calculate security score
        if summary['total_targets'] > 0:
            security_score = max(0, 100 - (summary['vulnerable_targets'] / summary['total_targets']) * 100)
            print(f"📈 Security Score: {security_score:.1f}%")
        
        print()
        
        if summary['total_vulnerabilities'] > 0:
            print(f"⚠️  SECURITY ALERT: {summary['total_vulnerabilities']} vulnerabilities detected!")
            print()
            print(f"🔴 IMMEDIATE ACTIONS REQUIRED:")
            print(f"   • Review all critical vulnerabilities first")
            print(f"   • Implement immediate fixes for high-risk findings")
            print(f"   • Schedule remediation for medium-risk issues")
            print(f"   • Document all changes and retest")
            print()
            print(f"📋 NEXT STEPS:")
            print(f"   • Prioritize vulnerabilities by risk level")
            print(f"   • Create remediation timeline")
            print(f"   • Implement security controls")
            print(f"   • Schedule follow-up security assessment")
        else:
            print(f"✅ SECURITY STATUS: No vulnerabilities found!")
            print(f"   • Target appears secure based on current scan")
            print(f"   • Continue regular security monitoring")
            print(f"   • Schedule periodic security assessments")

    def _print_info(self, message: str) -> None:
        """Print info message."""
        print(f"ℹ️  {message}")

    def _print_success(self, message: str) -> None:
        """Print success message."""
        print(f"✅ {message}")

    def _print_warning(self, message: str) -> None:
        """Print warning message."""
        print(f"⚠️  {message}")

    def _print_error(self, message: str) -> None:
        """Print error message."""
        print(f"❌ {message}")

    def _print_scan_progress(self, target: str, scanner_name: str) -> None:
        # Only print progress if not in no_results mode
        if self.config.get("no_results", False):
            return
        print(f"   🔍 {scanner_name.replace('_', ' ').title()}...")

    def _generate_output(self) -> None:
        """Generate and save output."""
        output_file = self.config.get("output") or self.vmnf_handler.get("output") or self.vmnf_handler.get("o")
        sarif_file = self.config.get("output_sarif") or (output_file.replace('.json', '.sarif') if output_file and self.config.get("sarif") else None)
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    json.dump(self.results, f, indent=2)
                if self.config.get("no_results", False):
                    print(f"[DEBUG] Results saved to: {output_file}")
                else:
                    self._print_success(f"Results saved to: {output_file}")
            except Exception as e:
                self._print_error(f"Error saving results: {str(e)}")
        if sarif_file:
            try:
                sarif = self._to_sarif()
                with open(sarif_file, 'w') as f:
                    json.dump(sarif, f, indent=2)
                if self.config.get("no_results", False):
                    print(f"[DEBUG] SARIF results saved to: {sarif_file}")
                else:
                    self._print_success(f"SARIF results saved to: {sarif_file}")
            except Exception as e:
                self._print_error(f"Error saving SARIF: {str(e)}")

    def _to_sarif(self) -> dict:
        # SARIF v2.1.0 skeleton
        sarif = {
            "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "W2PyScanner",
                            "informationUri": "https://web2py.com/",
                            "rules": []
                        }
                    },
                    "results": []
                }
            ]
        }
        rules = {}
        results = []
        for target in self.results.get("targets", []):
            for vuln in target.get("vulnerabilities", []):
                rule_id = vuln.get("metadata", {}).get("cwe", vuln.get("title", "W2PyVuln"))
                if rule_id not in rules:
                    rules[rule_id] = {
                        "id": rule_id,
                        "name": vuln.get("title", rule_id),
                        "shortDescription": {"text": vuln.get("title", rule_id)},
                        "fullDescription": {"text": vuln.get("description", "")},
                        "help": {"text": "; ".join(self._get_remediation_guidance(vuln))}
                    }
                level = "error" if vuln.get("risk", "low").lower() == "high" else ("warning" if vuln.get("risk", "low").lower() == "medium" else "note")
                location = {
                    "physicalLocation": {
                        "artifactLocation": {"uri": target.get("url", "")},
                        "region": {"startLine": 1}
                    }
                }
                # For DAST, add endpoint as logicalLocation
                endpoint = vuln.get("metadata", {}).get("endpoint") or vuln.get("metadata", {}).get("endpoints", [None])[0]
                if endpoint:
                    location["logicalLocations"] = [{"name": endpoint, "kind": "endpoint"}]
                results.append({
                    "ruleId": rule_id,
                    "level": level,
                    "message": {"text": vuln.get("description", "")},
                    "locations": [location],
                    "properties": {
                        "evidence": vuln.get("evidence", []),
                        "remediation": self._get_remediation_guidance(vuln),
                        "scanner": vuln.get("scanner", "")
                    }
                })
        sarif["runs"][0]["tool"]["driver"]["rules"] = list(rules.values())
        sarif["runs"][0]["results"] = results
        return sarif


def main():
    """Main entry point for standalone execution."""
    scanner = siddhi()
    # This would be called by Vimana framework
    # scanner.start(args)


if __name__ == "__main__":
    main() 