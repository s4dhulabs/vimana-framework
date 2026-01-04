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
import sys
import json
import asyncio
from time import sleep
from typing import Dict, Any, Optional, List
from neotermcolor import colored, cprint
from tabulate import tabulate
from core.vmnf_channels import register_channel
import hashlib
from urllib.parse import urlparse

class siddhi:
    """
    PySerial - Python Serialization Security Testing Plugin
    
    A specialized plugin for testing serialization vulnerabilities in Python applications,
    particularly FastAPI applications using Pydantic models.
    """
    
    def __init__(self, **vmnf_handler):
        """Initialize PySerial plugin with vmnf_handler arguments."""
        self.vmnf_handler = vmnf_handler
        
        # Core configuration
        self.target_url = self.vmnf_handler.get('target_url')
        self.api_specs = self.vmnf_handler.get('apispec_enabled') or self.vmnf_handler.get('oas')
        self.spec_id = self.api_specs if isinstance(self.api_specs, str) else None
        
        # Environment fallback configuration
        self.ENV_FALLBACK_SPEC_ID = None
        self.ENV_FALLBACK_TARGET = None
        self.ENV_FALLBACK_API_VERSION = None
        self.ENV_FALLBACK_SCAN_DATE = None
        
        # Serialization testing parameters
        self.serialization_test = self.vmnf_handler.get('serialization_test', True)  # Always enabled for this plugin
        self.test_types = self.vmnf_handler.get('test_type', None)
        self.pydantic_models = self.vmnf_handler.get('pydantic_models', None)
        self.custom_test = self.vmnf_handler.get('custom_test', None)
        self.set_custom_payload = self.vmnf_handler.get('set_custom_payload', False)
        
        # Output and display options
        self.verbose_enabled = self.vmnf_handler.get('verbose', True)  # Default to verbose for serialization tests
        self.colors_disabled = self.vmnf_handler.get('no_color', False)
        self.export_format = self.vmnf_handler.get('export_format', 'json')
        self.navigation_mode = self.vmnf_handler.get('navigation_mode', False)
        
        # JSON export configuration
        self.json_output = self.vmnf_handler.get('json_output', False)
        self.output_file = self.vmnf_handler.get('output', None)
        
        # Load environment variables from .jcolt_env (shared with JColt)
        self.load_pyserial_env()
        
        # Handle ENV_FALLBACK for api_specs
        if not self.api_specs and self.ENV_FALLBACK_SPEC_ID:
            self.api_specs = self.ENV_FALLBACK_SPEC_ID
            self.spec_id = self.ENV_FALLBACK_SPEC_ID
            if self.verbose_enabled:
                print(f" → Using specification ID from environment: {self.spec_id}")
        
        # Initialize spec info
        self.spec_info = None
        self.loaded_specs = None
        
    def load_pyserial_env(self):
        """Load PySerial environment variables from ~/.jcolt_env (shared with JColt)"""
        env_file = os.path.expanduser('~/.jcolt_env')
        self.pyserial_env = {}
        
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            self.pyserial_env[key] = value
                            os.environ[key] = value
                            if self.verbose_enabled:
                                print(f" → Loaded environment variable: {key}={value}")

                # Load common environment variables
                self.ENV_FALLBACK_SPEC_ID = self.pyserial_env.get('JCOLT_SCAN_SPEC_ID')
                self.ENV_FALLBACK_TARGET = self.pyserial_env.get('JCOLT_SCAN_TARGET')
                self.ENV_FALLBACK_API_VERSION = self.pyserial_env.get('JCOLT_API_VERSION')
                self.ENV_FALLBACK_SCAN_DATE = self.pyserial_env.get('JCOLT_LAST_SCAN_DATE')

            except Exception as e:
                if self.verbose_enabled:
                    print(f" → Failed to load environment variables from {env_file}: {str(e)}")

    def load_spec_from_db(self):
        """Load API specification from database if spec_id is provided."""
        if not self.spec_id:
            return None
            
        try:
            from core._dbops_.vmnf_dbops import VFDBOps
            self.spec_info = VFDBOps().get_by_id('_SPECS_', 'spec_id', self.spec_id)
            
            if self.spec_info and self.spec_info.spec_file_path:
                import os
                spec_file = self.spec_info.spec_file_path
                if os.path.exists(spec_file):
                    with open(spec_file, 'r') as f:
                        self.loaded_specs = json.load(f)
                        return self.loaded_specs
                else:
                    print(f" → Error: Spec file {spec_file} not found!")
                    return None
        except Exception as e:
            print(f" → Error loading spec from database: {e}")
            
        return None
        
    def validate_target_and_spec(self):
        """Validate that we have either a target URL or API specification."""
        if not self.target_url and not self.spec_id:
            # Check if we have ENV_FALLBACK_SPEC_ID available
            if self.ENV_FALLBACK_SPEC_ID:
                self.spec_id = self.ENV_FALLBACK_SPEC_ID
                self.api_specs = self.ENV_FALLBACK_SPEC_ID
                if self.verbose_enabled:
                    print(f" → Using specification ID from environment: {self.spec_id}")
            else:
                print(colored(" → Error: No target URL or API specification provided", 'red'))
                print(colored("    Use --target-url or --apispec to specify target", 'yellow'))
                print(colored("    Or run JColt first to scan an API and set environment", 'yellow'))
                return False
            
        if self.spec_id:
            specs = self.load_spec_from_db()
            if not specs:
                print(colored(f" → Error: Could not load specification {self.spec_id}", 'red'))
                return False
            self.loaded_specs = specs
            
            # Extract target URL from spec if not provided
            if not self.target_url and self.spec_info:
                self.target_url = self.spec_info.spec_host
                self.vmnf_handler['target_url'] = self.target_url
                print(f" → Using target URL from spec: {self.target_url}")
                
        return True
        
    def prepare_serialization_parameters(self):
        """Prepare parameters for serialization testing."""
        # Process test types (serialization categories)
        if self.test_types:
            if isinstance(self.test_types, str):
                test_types = [t.strip() for t in self.test_types.split(',')]
            else:
                test_types = self.test_types
        else:
            test_types = None  # Use all categories
            
        # Process model names
        if self.pydantic_models:
            if isinstance(self.pydantic_models, str):
                model_names = [m.strip() for m in self.pydantic_models.split(',')]
            else:
                model_names = self.pydantic_models
        else:
            model_names = None  # Test all models
            
        # Update handler with processed parameters
        self.vmnf_handler['test_type'] = test_types
        self.vmnf_handler['pydantic_models'] = model_names
        self.vmnf_handler['schema'] = self.loaded_specs
        
        # Handle custom test file if provided
        if self.custom_test:
            if os.path.exists(self.custom_test):
                print(f" → Using custom serialization test file: {self.custom_test}")
                self.vmnf_handler['custom_test'] = self.custom_test
            else:
                print(f" → Warning: Custom test file {self.custom_test} not found")
                
        # Pass the set_custom_payload flag
        if self.set_custom_payload:
            print(f" → Interactive payload builder enabled")
            self.vmnf_handler['set_custom_payload'] = True
            # Always enable verbose mode when using interactive payload builder
            self.vmnf_handler['verbose'] = True
            
    def run_serialization_tests(self):
        """Execute serialization tests against the target."""
        # Use loaded_specs if available, otherwise try to load from database
        if not self.loaded_specs:
            self.loaded_specs = self.load_spec_from_db()
            
        # If we still don't have specs but have a target URL, try to scan it
        if not self.loaded_specs and self.target_url:
            print(colored(f" → No API specification found, attempting to scan target: {self.target_url}", 'yellow'))
            try:
                # Try to extract the OpenAPI specification using similar logic to JColt
                import httpx
                from urllib.parse import urljoin
                
                api_url = self.target_url.rstrip('/')
                
                # Common OpenAPI spec locations
                spec_paths = [
                    '/openapi.json',
                    '/docs/openapi.json', 
                    '/api/openapi.json',
                    '/swagger/v1/swagger.json'
                ]
                
                spec_found = False
                for spec_path in spec_paths:
                    try:
                        full_url = urljoin(api_url, spec_path)
                        if self.verbose_enabled:
                            print(f"   Trying: {full_url}")
                        
                        response = httpx.get(full_url, timeout=10.0)
                        
                        if response.status_code == 200:
                            try:
                                spec_data = response.json()
                                if isinstance(spec_data, dict) and 'paths' in spec_data:
                                    self.loaded_specs = spec_data
                                    spec_found = True
                                    print(colored(f" → Successfully extracted API specification from {full_url}", 'green'))
                                    
                                    # Create basic spec info for JSON export
                                    self.spec_info = type('SpecInfo', (), {
                                        'spec_id': 'auto_scanned',
                                        'spec_name': f'Auto-scanned from {self.target_url}',
                                        'spec_host': self.target_url,
                                        'framework_type': 'FastAPI',
                                        'description': 'Auto-scanned API specification for serialization testing'
                                    })()
                                    break
                            except json.JSONDecodeError:
                                continue
                                
                    except Exception as e:
                        if self.verbose_enabled:
                            print(f"   Failed to fetch from {spec_path}: {str(e)}")
                        continue
                
                if not spec_found:
                    print(colored(f" → Warning: Could not extract API specification from {self.target_url}", 'yellow'))
                    print(colored("    Continuing with basic serialization tests...", 'yellow'))
                    
            except Exception as e:
                print(colored(f" → Warning: Failed to scan target URL: {str(e)}", 'yellow'))
                print(colored("    Continuing with basic serialization tests...", 'yellow'))
            
        if not self.loaded_specs and not self.target_url:
            print(colored(" → Error: No API specification or target URL available", 'red'))
            return False

        print()
        cprint(" → Running Python serialization security tests...", 'green')
        print()
        
        # Prepare parameters
        self.prepare_serialization_parameters()
        
        # Import and run serialization tests
        from .engines.serialization_engine import run_serialization_tests
        results = run_serialization_tests(self.vmnf_handler, self.loaded_specs or {})
        
        # Register channels for exploitable vectors
        if results:
            import hashlib
            for model_name, model_results in results.items():
                fields = model_results.get('fields', {})
                serialization_tests = fields.get('serialization_tests', [])
                for test in serialization_tests:
                    
                    
                    if isinstance(test, dict) and 'vulnerability_details' in test:
                        # Build a unique channel_id
                        base = f"{self.target_url}:{model_name}:{test.get('category','')}:" + str(test.get('name',''))
                        channel_id = hashlib.sha1(base.encode()).hexdigest()[:8]
                        # Extract endpoint from test details (real API path)
                        endpoint_url = test.get('details', {}).get('request', {}).get('url', None)
                        endpoint = None
                        if endpoint_url:
                            parsed = urlparse(endpoint_url)
                            endpoint = parsed.path  # e.g., '/nested-structure/create'
                        if not endpoint:
                            # Try to get from model metadata or fallback to model_name
                            endpoint = model_name
                        # Try to categorize the channel type
                        vuln_details = str(test.get('vulnerability_details', '')).lower()
                        if 'code execution' in vuln_details or 'rce' in vuln_details:
                            channel_type = 'RCE'
                        elif 'file write' in vuln_details:
                            channel_type = 'File Write'
                        elif 'file read' in vuln_details:
                            channel_type = 'File Read'
                        elif 'denial of service' in vuln_details or 'dos' in vuln_details:
                            channel_type = 'DoS'
                        else:
                            channel_type = 'Exploit'
                            
                        # Patch: Ensure payload_template is always a JSON dict with required fields
                        payload = test.get('payload','')
                        if isinstance(payload, dict):
                            payload_template = payload
                        else:
                            payload_template = {
                                'name': 'cmd',
                                'data_type': 'pickle',
                                'data': payload
                            }
                        channel_data = {
                            'channel_id': channel_id,
                            'type': channel_type,
                            'plugin': 'pyserial',
                            'target_url': self.target_url,
                            'endpoint': endpoint,
                            'method': test.get('request',{}).get('method','POST'),
                            'payload_template': json.dumps(payload_template),
                            'description': str(test.get('vulnerability_details','Exploitable serialization vector')),
                            'status': 'active',
                            'metadata': {
                                'model': model_name,
                                'category': test.get('category',''),
                                'test_name': test.get('name',''),
                                'details': test.get('vulnerability_details',''),
                            }
                        }
                        register_channel(channel_data)
                    
                
                
            if self.json_output or self.output_file:
                # Prepare spec info for JSON export
                spec_info = {}
                if self.spec_info:
                    spec_info = {
                        'spec_id': getattr(self.spec_info, 'spec_id', 'unknown'),
                        'spec_name': getattr(self.spec_info, 'spec_name', 'unknown'),
                        'host': getattr(self.spec_info, 'spec_host', 'unknown'),
                        'framework_type': getattr(self.spec_info, 'framework_type', 'unknown'),
                        'description': getattr(self.spec_info, 'description', 'Python serialization security testing')
                    }
                
                # Use custom output file if provided, otherwise generate default
                output_file = self.output_file if self.output_file else None
                
                # Export to JSON
                from .exporters.json_exporter import PySerialJsonExporter
                exporter = PySerialJsonExporter(output_file=output_file, spec_info=spec_info)
                exporter.export_results(results)
            
            # Display results summary
            self._display_serialization_results_summary(results)
            
            if self.navigation_mode:
                from .navi.pydantic_handler import PydanticNaviHandler
                PydanticNaviHandler(self.vmnf_handler, results).manage()
                
            return results
        else:
            print(" → No serialization test results generated.")
            return None
            
    def _display_serialization_results_summary(self, results):
        """Display a summary of serialization test results."""
        if not results:
            print("No test results to display")
            return
            
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        vulnerable_tests = 0
        model_summaries = []
        
        for model_name, model_results in results.items():
            model_total = 0
            model_passed = 0
            model_failed = 0
            model_vulnerable = 0
            
            # Check if fields exists and contains serialization_tests
            fields = model_results.get('fields', {})
            if not isinstance(fields, dict):
                continue
                
            # Handle serialization_tests structure
            serialization_tests = fields.get('serialization_tests', [])
            if not isinstance(serialization_tests, list):
                continue
                
            for test in serialization_tests:
                if not isinstance(test, dict):
                    continue
                    
                model_total += 1
                
                # Check test result
                if test.get('pass', False):
                    model_passed += 1
                    passed_tests += 1
                else:
                    model_failed += 1
                    failed_tests += 1
                    
                    # Check if it's a vulnerability
                    if 'vulnerability_details' in test:
                        model_vulnerable += 1
                        vulnerable_tests += 1
            
            total_tests += model_total
            if model_total > 0:
                model_summaries.append({
                    'model': model_name,
                    'tests': model_total,
                    'passed': model_passed,
                    'failed': model_failed,
                    'vulnerable': model_vulnerable,
                    'pass_rate': f"{(model_passed / model_total * 100) if model_total else 0:.1f}%"
                })

        # Print summary table
        print()
        print(colored(" Python Serialization Security Test Summary ", "white", "on_blue"))
        print()
        
        if not model_summaries:
            print("No testable models found in results")
            return
            
        headers = ["Model", "Tests", "Passed", "Failed", "Vulnerable", "Pass Rate"]
        table_data = [[m['model'], m['tests'], m['passed'], m['failed'], m['vulnerable'], m['pass_rate']] for m in model_summaries]
        
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
        
        if total_tests > 0:
            overall_pass_rate = f"{(passed_tests / total_tests * 100):.1f}%"
            print(f" → Total Tests: {total_tests}")
            print(f" → Passed: {colored(passed_tests, 'green')}")
            print(f" → Failed: {colored(failed_tests, 'red')}")
            if vulnerable_tests > 0:
                print(f" → Vulnerabilities Found: {colored(vulnerable_tests, 'red', attrs=['bold'])}")
            print(f" → Overall Pass Rate: {colored(overall_pass_rate, 'cyan')}")
        else:
            print(" → No tests were executed")
        print()
        
    def show_banner(self):
        """Display PySerial plugin banner."""
        banner = """
        ╔══════════════════════════════════════════════════════════════╗
        ║                                                              ║
        ║                      PYSERIAL v1.0.0                         ║
        ║                                                              ║
        ║          Python Serialization Security Testing               ║
        ║                                                              ║
        ║  [*] Specialized serialization vulnerability detection       ║
        ║  [*] Pydantic model security analysis                        ║
        ║  [*] Custom payload generation and testing                   ║
        ║  [*] Powered by Vimana Framework - @s4dhulabs                ║
        ║                                                              ║
        ╚══════════════════════════════════════════════════════════════╝
        """
        if not self.colors_disabled:
            print(colored(banner, 'cyan', attrs=['bold']))
        else:
            print(banner)
            
    def start(self):
        """Main entry point for PySerial plugin."""
        # Clear screen and show banner
        print('\033[2J\033[1;1H' * 3)
        self.show_banner()
        
        # Validate target and specification
        if not self.validate_target_and_spec():
            sys.exit(1)
            
        # Run serialization tests
        results = self.run_serialization_tests()
        
        if results:
            print(colored("\n → Serialization testing completed successfully!", 'green'))
        else:
            print(colored("\n → Serialization testing completed with no results", 'yellow'))
            sys.exit(1) 