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

from core.vmnf_navicontrols import *


from core._dbops_.vmnf_dbops import VFDBOps
from neotermcolor import colored,cprint
from .engines.fetcher import jcfetcher
from .parsers.jcfzz import Jcfzz
from .ops.ops import jcOps
from prettytable import PrettyTable
from urllib.parse import urljoin
from datetime import datetime
from tabulate import tabulate
from time import sleep
from .utils import *
import requests
import logging
import asyncio
import httpx
import json
import re
import sys
import os

# vflogging
from core.vmnf_log_utils import configure_logging
configure_logging(os.path.basename(__file__))

from .jamzz import ValidateSchema

class siddhi:
    def __init__(self,**vmnf_handler):
        logging.info("Initializing Jc0lt siddhi class...")

        self.vmnf_handler = vmnf_handler
        self.debug_logging = self.vmnf_handler.get('debug_logging')
        self.verbose_logging = self.vmnf_handler.get('verbose_logging') 
        self.verbose_enabled = self.vmnf_handler.get('verbose')

        self.colors_disabled = vmnf_handler.get('colors_disabled')
        self.api_specs = False
        issue_type = 'specs'
        plugin_scope = f'fastapi/{issue_type}'
        self.cache_dir = f'.vimana/cache/{plugin_scope}'
        self.abs_cache_path = os.path.join(os.path.expanduser("~"), self.cache_dir)
        
        self.export_enabled = self.vmnf_handler['export_body']
        self.fuzzer_enabled =  self.vmnf_handler['fuzzerspec_enabled']
        self.api_scan_enabled = self.vmnf_handler['api_scan_enabled']
        self.ENV_FALLBACK_SPEC_ID = None
        self.fingerprint_enabled = self.vmnf_handler['fingerprint']
        self.inspect_spec = self.vmnf_handler['apispec_enabled']
        self.workflow_mode = False
        
        # Load environment variables from .jcolt_env
        self.load_jcolt_env()

        # vimana run -p jcolt --oas OAS9981
        if self.vmnf_handler['apispec_enabled']:

            # vimana run -p jcolt --oas OAS9981 --fuzzspec
            if self.fuzzer_enabled == 'ENV_FALLBACK':
                self.fuzzer_enabled = self.vmnf_handler['apispec_enabled']
            else:
                self.vmnf_handler['list_paths'] = True

        # vimana run -p jcolt --fuzzspec
        else: 
            # vimana run -p jcolt --fuzzspec
            if self.fuzzer_enabled == 'ENV_FALLBACK':
                self.fuzzer_enabled = self.ENV_FALLBACK_SPEC_ID
        
        self.h_color = 95
        self.v_color = 99 
        self.align = 35

        if self.colors_disabled:
            self.h_color = None
            self.v_color = None
            self.align = 25
        
        self.list_pydantic_models = self.vmnf_handler['list_pydantic_models']
        self.list_field_constraints = self.vmnf_handler['list_field_constraints']
        self.list_endpoint_models = self.vmnf_handler['list_endpoint_models']
        self.list_security_fields = self.vmnf_handler['list_security_fields']
        self.list_enums = self.vmnf_handler['list_enums']
        self.list_model_relationships = self.vmnf_handler['list_model_relationships']
        self.list_validation_coverage = self.vmnf_handler['list_validation_coverage']

        self.list_opids = self.vmnf_handler['list_op_ids']
        self.list_parameters = self.vmnf_handler['list_parameters']
        self.list_schemas = self.vmnf_handler['list_schemas']
        self.list_response_codes =  self.vmnf_handler['list_response_codes']
        self.list_examples = self.vmnf_handler['list_examples']
        self.list_tags = self.vmnf_handler['list_tags']
        self.list_paths_mode = self.vmnf_handler['list_paths']
        self.schema_validate = self.vmnf_handler['schema_validate']
        self.list_specs  = self.vmnf_handler['list_specs'] 
        self.list_descriptions  = self.vmnf_handler['list_descriptions'] 
        self.flush_spec = self.vmnf_handler['flush_spec']
        self.flush_specs = self.vmnf_handler['flush_specs']
        
        self.api_scan_enabled = self.vmnf_handler['api_scan_enabled']
        self.target_url = self.vmnf_handler['target_url'] if not self.api_scan_enabled else self.api_scan_enabled
        self.list_response_headers = self.vmnf_handler['list_response_headers']
        self.load_from_env = self.vmnf_handler['load_from_env']
        self.env_name = self.load_from_env
        self.describe_mode = self.vmnf_handler['describe_mode_enabled']

        self.pydantic_test = self.vmnf_handler.get('pydantic_test', False)
        self.pydantic_test_types = self.vmnf_handler.get('pydantic_test_types', [])
        self.pydantic_models = self.vmnf_handler.get('pydantic_models', [])
        self.test_categories = self.vmnf_handler.get('test_categories', [])
        self.export_format = self.vmnf_handler.get('export_format', 'json')
        self.serialization_test = self.vmnf_handler.get('serialization_test', False)
        self.custom_test = self.vmnf_handler.get('custom_test', '')
        self.set_custom_payload = self.vmnf_handler.get('set_custom_payload', False)
        
        # JSON export configuration
        self.json_output = self.vmnf_handler.get('json_output', False)
        self.output_file = self.vmnf_handler.get('output', None)
        
        logging.info("Jc0lt class initialized successfully!")

    def register_channel_for_vulnerability(self, vulnerability_type, endpoint, method, description, payload_template=None, metadata=None):
        """
        Register a discovered vulnerability as a channel for other plugins to consume.
        
        Args:
            vulnerability_type (str): Type of vulnerability (RCE, File Write, etc.)
            endpoint (str): The vulnerable endpoint
            method (str): HTTP method (GET, POST, etc.)
            description (str): Human-readable description
            payload_template (str, optional): Example payload
            metadata (dict, optional): Additional metadata
        """
        try:
            from core.vmnf_channels import register_channel
            import hashlib
            
            # Generate unique channel ID
            channel_data = f"{self.target_url}{endpoint}{method}{vulnerability_type}"
            channel_id = hashlib.md5(channel_data.encode()).hexdigest()[:8]
            
            # Prepare channel data
            channel_info = {
                'channel_id': channel_id,
                'type': vulnerability_type,
                'plugin': 'jcolt',
                'target_url': self.target_url,
                'endpoint': endpoint,
                'method': method,
                'payload_template': payload_template or f"Vulnerability: {vulnerability_type}",
                'description': description,
                'status': 'active',
                'metadata': metadata or {}
            }
            
            # Register the channel
            register_channel(channel_info)
            
            if self.verbose_enabled:
                print(colored(f" → Channel registered: {channel_id} ({vulnerability_type})", 'cyan'))
                
        except ImportError:
            if self.verbose_enabled:
                print(colored(" → Channels API not available", 'yellow'))
        except Exception as e:
            if self.verbose_enabled:
                print(colored(f" → Failed to register channel: {e}", 'red'))

    def load_jcolt_env(self):
        """Load Jcolt environment variables from ~/.jcolt_env"""
        env_file = os.path.expanduser('~/.jcolt_env')
        self.jcolt_env = {}
        
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            self.jcolt_env[key] = value
                            os.environ[key] = value
                            if self.verbose_enabled:
                                print(f" → Loaded environment variable: {key}={value}")

                # Load common environment variables
                self.ENV_FALLBACK_SPEC_ID = self.jcolt_env.get('JCOLT_SCAN_SPEC_ID')
                self.ENV_FALLBACK_TARGET = self.jcolt_env.get('JCOLT_SCAN_TARGET')
                self.ENV_FALLBACK_API_VERSION = self.jcolt_env.get('JCOLT_API_VERSION')
                self.ENV_FALLBACK_SCAN_DATE = self.jcolt_env.get('JCOLT_LAST_SCAN_DATE')

            except Exception as e:
                logging.warning(f"Failed to load environment variables from {env_file}: {str(e)}")
                if self.verbose_enabled:
                    print(f" → Failed to load environment variables from {env_file}: {str(e)}")

    def save_jcolt_env(self, env_data: dict):
        """Save Jcolt environment variables to ~/.jcolt_env"""
        env_file = os.path.expanduser('~/.jcolt_env')
        try:
            with open(env_file, 'w') as f:
                for key, value in env_data.items():
                    f.write(f"{key}={value}\n")
                    if self.verbose_enabled:
                        print(f" → Saved environment variable: {key}={value}")
        except Exception as e:
            logging.warning(f"Failed to save environment variables to {env_file}: {str(e)}")
            if self.verbose_enabled:
                print(f" → Failed to save environment variables to {env_file}: {str(e)}")

    def run_pydantic_tests(self):
        if not self.api_specs:
            if self.target_url:
                asyncio.run(self.check_api())
            else:
                print(" → jcolt@run_pydantic_tests: No API specification available")
                return False

        print()
        cprint(" → Running Pydantic model tests...", 'green')
        print()

        if not self.vmnf_handler.get('target_url') and self.spec_id:
            if not hasattr(self, 'spec_info') or self.spec_info is None:
                from core._dbops_.vmnf_dbops import VFDBOps
                self.spec_info = VFDBOps().get_by_id('_SPECS_', 'spec_id', self.spec_id)
                
            if hasattr(self, 'spec_info') and self.spec_info:
                self.vmnf_handler['target_url'] = self.spec_info.spec_host
                print(f" → Using target URL from spec: {self.spec_info.spec_host}")
        
        # Prepare parameters
        # Check if --test-type was provided and map it to pydantic_test_types
        test_type_param = self.vmnf_handler.get('test_type', None)
        if test_type_param:
            # If --test-type was provided, use it for pydantic test types
            if isinstance(test_type_param, str):
                test_types = [t.strip() for t in test_type_param.split(',')]
            else:
                test_types = test_type_param
        else:
            # Fall back to pydantic_test_types parameter
            if isinstance(self.pydantic_test_types, str):
                test_types = self.pydantic_test_types.split(',')
            else:
                test_types = self.pydantic_test_types or [
                    'type_confusion', 
                    'validation_bypass', 
                    'boundary_testing',
                    'special_chars',
                    'injection'
                ]
            
        if isinstance(self.pydantic_models, str):
            model_names = self.pydantic_models.split(',')
        else:
            model_names = self.pydantic_models
        
        # Process test categories if provided
        if self.test_categories:
            if isinstance(self.test_categories, str):
                categories = [cat.strip() for cat in self.test_categories.split(',')]
            else:
                categories = self.test_categories
        else:
            categories = []
            
        ## Process test types if provided
        if isinstance(test_types, str):
            test_types = [t.strip() for t in test_types.split(',')]
            
        # Add test parameters to handler
        self.vmnf_handler['pydantic_test_types'] = test_types
        self.vmnf_handler['pydantic_models'] = model_names
        self.vmnf_handler['test_categories'] = categories
        self.vmnf_handler['schema'] = self.api_specs
        
        # regular API tests
        from .engines.pydantic_engine import run_pydantic_tests
        results = run_pydantic_tests(self.vmnf_handler)
        
        # fall back to schema-only testinq
        if not results:
            print("\n → No results from API testing, using schema-only testing mode...")
            
            # Import schema tester only when needed
            from .engines.schema_tester import generate_schema_test_results
            
            # Generate test results directly from schema
            results = generate_schema_test_results(self.api_specs)
            
            if results:
                print(f" → Generated tests for {len(results)} models using schema-only mode")
        
        if results:
            # Generate report using ReportManager
            from .reporters.report_manager import ReportManager
            report_manager = ReportManager(
                results=results,
                export_format=self.export_format,
                verbose=self.verbose_enabled,
                json_output=self.json_output,
                output_file=self.output_file
            )
            report_manager.generate_report()
            
            # Display results summary
            self._display_pydantic_results_summary(results)
            
            if self.vmnf_handler.get('navigation_mode', False):
                from .navi.pydantic_handler import PydanticNaviHandler
                PydanticNaviHandler(self.vmnf_handler, results).manage()
        else:
            print(" → No test results generated.")       # Save results to file
            
    
    def run_serialization_tests(self):
        """Run serialization tests against an API by calling PySerial plugin."""
        if not self.api_specs:
            if self.target_url:
                asyncio.run(self.check_api())
            else:
                print(" → jcolt@run_serialization_tests: No API specification available")
                return False

        print()
        cprint(" → Delegating to PySerial plugin for serialization testing...", 'green')
        print()

        # Prepare parameters for PySerial plugin
        pyserial_handler = self.vmnf_handler.copy()
        
        # Ensure we have the API spec ID for PySerial
        if self.spec_id:
            pyserial_handler['apispec_enabled'] = self.spec_id
        
        # Set target URL if available
        if not pyserial_handler.get('target_url') and self.spec_id:
            if not hasattr(self, 'spec_info') or self.spec_info is None:
                from core._dbops_.vmnf_dbops import VFDBOps
                self.spec_info = VFDBOps().get_by_id('_SPECS_', 'spec_id', self.spec_id)
                
            if hasattr(self, 'spec_info') and self.spec_info:
                pyserial_handler['target_url'] = self.spec_info.spec_host
                print(f" → Using target URL from spec: {self.spec_info.spec_host}")
        
        # Process test types (now used for serialization categories)
        test_types = self.vmnf_handler.get('test_type', None)
        
        # If test_type was not provided, check pydantic_test_types for backward compatibility
        if not test_types:
            if isinstance(self.pydantic_test_types, str):
                test_types = self.pydantic_test_types.split(',')
            else:
                test_types = self.pydantic_test_types
            
        if isinstance(self.pydantic_models, str):
            model_names = self.pydantic_models.split(',')
        else:
            model_names = self.pydantic_models
            
        # Add parameters to handler
        pyserial_handler['test_type'] = test_types
        pyserial_handler['pydantic_models'] = model_names
        pyserial_handler['serialization_test'] = True
        
        # Handle custom test file if provided
        if self.custom_test:
            if os.path.exists(self.custom_test):
                print(f" → Passing custom serialization test file to PySerial: {self.custom_test}")
                pyserial_handler['custom_test'] = self.custom_test
            else:
                print(f" → Warning: Custom test file {self.custom_test} not found")
                
        # Pass the set_custom_payload flag
        if self.set_custom_payload:
            print(f" → Interactive payload builder will be enabled in PySerial")
            pyserial_handler['set_custom_payload'] = True
            # Always enable verbose mode when using interactive payload builder
            pyserial_handler['verbose'] = True
        
        # Import and call PySerial plugin
        try:
            from siddhis.pyserial.pyserial import siddhi as PySerialPlugin
            pyserial_plugin = PySerialPlugin(**pyserial_handler)
            
            # Set the loaded specs directly for PySerial
            pyserial_plugin.loaded_specs = self.api_specs
            
            results = pyserial_plugin.run_serialization_tests()
            
            if results:
                print(colored(" → PySerial plugin completed successfully", 'green'))
                return results
            else:
                print(colored(" → PySerial plugin completed with no results", 'yellow'))
                return None
                
        except ImportError as e:
            print(colored(f" → Error: PySerial plugin not found: {e}", 'red'))
            print(colored("   Please ensure PySerial plugin is installed", 'yellow'))
            return None
        except Exception as e:
            print(colored(f" → Error running PySerial plugin: {e}", 'red'))
            return None
        
    def _display_pydantic_results_summary(self, results):
        """Display a summary of Pydantic test results."""
        if not results:
            print("No test results to display")
            return
            
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        model_summaries = []
        
        for model_name, model_results in results.items():
            model_total = 0
            model_passed = 0
            
            # Check if fields exists and is a dictionary
            fields = model_results.get('fields')
            if not isinstance(fields, dict):
                continue
                
            for field_name, field_data in fields.items():
                # Handle both structures: field_data as list or as dict with 'tests' key
                if isinstance(field_data, list):
                    tests = field_data
                elif isinstance(field_data, dict) and 'tests' in field_data:
                    tests = field_data['tests']
                else:
                    continue
                    
                if not isinstance(tests, list):
                    continue
                    
                for test in tests:
                    # Make sure test is a dictionary with a 'pass' key
                    if not isinstance(test, dict):
                        continue
                        
                    model_total += 1
                    if test.get('pass', False):
                        model_passed += 1
                        passed_tests += 1
                    else:
                        failed_tests += 1
            
            total_tests += model_total
            if model_total > 0:
                model_summaries.append({
                    'model': model_name,
                    'tests': model_total,
                    'passed': model_passed,
                    'failed': model_total - model_passed,
                    'pass_rate': f"{(model_passed / model_total * 100) if model_total else 0:.1f}%"
                })

        
        # Print summary table instead of calling original Vimana reporter
        from tabulate import tabulate
        
        print()
        print(colored(" Pydantic Testing Summary ", "white", "on_green"))
        print()
        
        if not model_summaries:
            print("No testable models found in results")
            return
            
        headers = ["Model", "Tests", "Passed", "Failed", "Pass Rate"]
        table_data = [[m['model'], m['tests'], m['passed'], m['failed'], m['pass_rate']] for m in model_summaries]
        
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print()
        
        if total_tests > 0:
            overall_pass_rate = f"{(passed_tests / total_tests * 100):.1f}%"
            print(f" → Total Tests: {total_tests}")
            print(f" → Passed: {colored(passed_tests, 'green')}")
            print(f" → Failed: {colored(failed_tests, 'red')}")
            print(f" → Overall Pass Rate: {colored(overall_pass_rate, 'cyan')}")
        else:
            print(" → No tests were executed")
        print()
                
    def parse_section(self, path:str, section_key:str, section_data:list):
        if self.debug_logging:
            logging.info("Parsing section: %s for path: %s", section_key, path)

        if section_key == 'requestBody' and not self.export_enabled and not self.fuzzer_enabled: 
            print(f"{colored('bodySchema', self.h_color):>{self.align}}:")

        elif section_key == 'responses' and not self.export_enabled and not self.fuzzer_enabled:
            print(f"{colored('responseSchema', self.h_color):>{self.align}}:")

        if isinstance(section_data, dict):
            if not self.export_enabled and not self.fuzzer_enabled:
                json_dump = json.dumps(section_data, indent=4)
                aligned_json_aligned = align_json(json_dump, 12, self.v_color)
                print(aligned_json_aligned)

        elif isinstance(section_data, list):
            params = False

            if section_key == 'parameters':
                params = get_parameters(path, section_data)

            if not self.export_enabled and not self.fuzzer_enabled:
                cl_key = f"{colored(section_key, self.h_color):>{self.align}}"
                
                if section_data and isinstance(section_data[0], str):
                    print(f"{cl_key}: {colored(section_data, self.v_color)}") 
                else:
                    print(f"{cl_key}:")

                    for item in section_data:
                        if isinstance(item, dict):
                            json_dump = json.dumps(item, indent=4)
                            aligned_json_aligned = align_json(json_dump, 12, self.v_color)
                            print(aligned_json_aligned)

            if self.debug_logging:
                logging.info("[Done] Processed responses section with %s parameters", len(params if params else []))

            return params
        
    def is_fastapi(self):
        pass

    def parse_specs(self, api_specs:dict=False, mode:str=False):
        self.handle_filters()
        json_dump = ''
        output_disabled = False
        found_path_id = False
        inspect_path_id = None
        self.lexer_disabled = False
        l_color = 110
        fuzz_scope = {}
        p_color = 45
        _fuzz_ = {}

        if self.colors_disabled:
            self.lexer_disabled = True
            l_color = None
            m_color = None
            p_color = None
        
        # Handle inspect path ID logic
        if self.vmnf_handler['inspect']:
            inspect_value = self.vmnf_handler['inspect']
            # If it's not a spec ID and not ENV_FALLBACK, treat as path ID
            if not inspect_value.startswith('aS') and inspect_value != 'ENV_FALLBACK':
                inspect_path_id = inspect_value
        
        if self.export_enabled or self.fuzzer_enabled:
            output_disabled = True

        if 'paths' not in self.api_specs:
            cprint("\n      It doesn't seem to be FastAPI\n\n",'red')
            return 

        for api_endpoint, methods in self.api_specs['paths'].items():       
            for method, properties in methods.items():
                _opid_ = properties.get('operationId','?').lower()
                _tags_ = properties.get('tags',False)

                if _tags_:
                    _tags_ = [t.lower() for t in _tags_]

                method = method.lower()
                if self.filter_tags and not any(tag in self.filter_tags for tag in _tags_):
                    continue

                if self.filter_by_opid and _opid_ not in self.filter_opids:
                    continue

                if self.filter_by_method and method not in self.filter_methods:
                    continue

                # Raw Fuzzer Round
                _fuzz_ = {
                    'properties': properties,
                    'method': method,
                    'host': self.spec_info.spec_host,
                    'path': api_endpoint,
                    'body': {}
                }

                fuzz_entry = _fuzz_.copy()
                fuzz_scope[api_endpoint] = []
                fuzz_scope[api_endpoint].append(_fuzz_)
                _method_ = method.upper()

                if not self.colors_disabled:
                    m_color = method_colors.get(_method_, None)

                if inspect_path_id:
                    current_path_id = gen_path_id(method, api_endpoint)

                    if current_path_id != inspect_path_id.strip():
                        continue
                
                    found_path_id = True

                dec_method = colored(_method_, m_color, attrs=['bold'])
                dec_endpoint = colored(api_endpoint, p_color, attrs=['bold'])
                
                if not self.export_enabled and not self.fuzzer_enabled:
                    path_id = gen_path_id(method,api_endpoint)
                    dec_path_id = colored(f"({path_id})",239)

                    print(f"  ➤  {dec_method} {dec_endpoint} {dec_path_id}")
                    print()

                for p_key, prop in properties.items():
                    url_params = False
                    url_params = self.parse_section(api_endpoint, p_key, prop)
                    
                    if url_params:
                        '''
                        -- Updates `path` from the raw endpoint `/api/user/register`
                        to `/api/user/register?uuid=$JCF-R&code=$JCF-R` (url params)

                        $JCF-R  - Required Parameters
                        $JCF-P  - Property, not required

                        '''
                        pattern = r'\{([^}]+)\}'
                        matches = re.findall(pattern, api_endpoint)
                        
                        if matches:
                            fuzz_entry['path'] = api_endpoint
                        else:
                            fuzz_entry['path'] = url_params

                        fuzz_scope[api_endpoint].append(fuzz_entry)

                    if p_key in {'requestBody', 'responses'} or isinstance(prop, (dict, list)):
                        if p_key in ['requestBody', 'responses']:
                            if not self.export_enabled and not self.fuzzer_enabled:
                                print(f"{colored(p_key, self.h_color):>{self.align}}:")
                        
                            try:
                                json_dump = json.loads(
                                    parse_requestBody(
                                        self.api_specs, 
                                        prop, 
                                        self.lexer_disabled, 
                                        output_disabled
                                    )
                                )
                            except json.decoder.JSONDecodeError:
                                pass

                            if p_key == 'requestBody':
                                if self.fuzzer_enabled: 
                                    '''
                                    --- Updates the body (using the previously updated with url_params
                                    '''
                                    fuzz_entry_body_parameters = fuzz_entry.copy()
                                    query_string = get_query_string(json_dump)
                                    fuzz_entry_body_parameters['body'] = query_string
                                    fuzz_scope[api_endpoint].append(fuzz_entry_body_parameters)

                            if p_key == 'requestBody' and self.vmnf_handler['export_body']:
                                if json_dump:
                                    export_body(json_dump, self.spec_id)
                    else:
                        if not self.export_enabled and not self.fuzzer_enabled:
                            print(f"{colored(p_key, self.h_color):>{self.align}}: {colored(prop, self.v_color)}")
                        
                if not self.export_enabled and not self.fuzzer_enabled:
                    print(colored('\u2500' * 110, l_color, attrs=[]))
                    sleep(0.10)

        if inspect_path_id and not found_path_id:
            self.vmnf_handler['colors_disabled'] = False
            print(f'Invalid path Id: {colored(inspect_path_id,"red")}. Valid ones:')
            print()
            self.list_paths()

        # jcolt --fuzzspec aSb988 
        if self.fuzzer_enabled:
            self.vmnf_handler['spec_id'] = self.spec_id
            self.vmnf_handler['schema'] = self.api_specs
            self.vmnf_handler['fuzz_scope'] = fuzz_scope
            Jcfzz(self.vmnf_handler).manage()
    
    def handle_filters(self):
        self.filter_by_method = False
        self.single_method = False
        self.filter_methods = False

        self.filter_by_opid = False
        self.single_opid = False
        self.filter_opids = False
        
        self.filter_by_tags = False
        self.single_tags = False
        self.filter_tags = False

        self.filter_by_method = self.vmnf_handler.get('filter_by_method')
        self.filter_by_opid = self.vmnf_handler.get('filter_by_opid')
        self.filter_by_tag = self.vmnf_handler.get('filter_by_tag')

        if self.filter_by_method:
            filter_methods = self.filter_by_method.split(',')
            self.single_method = True if len(filter_methods) == 1 else False
            self.filter_methods = [m.lower() for m in filter_methods]
            
            invalid_methods = []
            
            for m in self.filter_methods:
                if m.upper() not in method_colors:
                    invalid_methods.append(m)

            if invalid_methods:
                error = colored(','.join(invalid_methods),'red')
                print(f"  ➤  Invalid methods {error}\n\n")
                input()
                sys.exit(1)

        if self.filter_by_opid:
            filter_opids = self.filter_by_opid.split(',')
            self.single_opid = True if len(filter_opids) == 1 else False
            self.filter_opids = [o.lower() for o in filter_opids]
        
        if self.filter_by_tag:
            filter_tags = self.filter_by_tag.split(',')
            self.single_tag = True if len(filter_tags) == 1 else False
            self.filter_tags = [o.lower() for o in filter_tags]

    def list_paths(self):
        paths_list = []
        output_table = False
        l=[]

        self.handle_filters()
        api_paths = self.api_specs.get('paths',False)
        if not api_paths:
            print('* Jc0lt > API paths not found!')
            sys.exit(1)

        max_method_length = max(max(len(m) for m in mts) for mts in api_paths.values())
        max_path_length = max(len(pt) for pt in api_paths.keys())
        
        print()
        for api_endpoint, methods in self.api_specs['paths'].items():
            p_padding = ' ' * ((max_path_length - len(api_endpoint)) + 3)

            for method, properties in methods.items():
                _opid_ = properties.get('operationId','?').lower()
                _tags_ = properties.get('tags',False)

                if _tags_:
                    _tags_ = [t.lower() for t in _tags_]

                if self.filter_tags and not any(tag in self.filter_tags for tag in _tags_):
                    continue

                if self.filter_by_opid and _opid_ not in self.filter_opids:
                    continue

                if self.filter_by_method and method not in self.filter_methods:
                    continue

                m_padding = ' ' * ((max_method_length - len(method)) + 2)
                _method_ = method.upper()
                dec_method = _method_
                _path_ = api_endpoint
                path_id = gen_path_id(method,api_endpoint)
                color = 'green'
                sec = properties.get('security',['?'])
                
                if not self.colors_disabled:
                    _path_ = colored(api_endpoint, 45, attrs=[])
                    dec_method = colored(_method_, method_colors.get(_method_, None), attrs=[])

                    # it should to be moved to outside this if block since is about navigation mode
                    # if self.vmnf_handler['navigation_mode']
                    l.append(
                        {
                            'PathId':path_id,
                            'Method':_method_,
                            'Path':api_endpoint,
                            'SecFlow':sec
                        }
                    )
                    
                    paths_list.append(
                        f"{'  ➤ '} {colored(path_id,240):<8}   "
                        f"{dec_method}{m_padding}"
                        f"{_path_}{p_padding}{sec}"
                    )
                else:
                    paths_list.append(
                        f"{'  ➤'} {path_id:<8}"
                        f"{dec_method}{m_padding}"
                        f"{_path_}{p_padding}{sec}"
                    )
                
                if self.vmnf_handler['output_table']:
                    if not output_table:
                        output_table = PrettyTable()
                        output_table.title = f"{self.spec_id} Endpoints"
                        output_table.field_names = ["Id", "Method", "Endpoint", "Security Flows"]
                        output_table.align = 'l'
                    
                    output_table.add_row([path_id, dec_method, _path_, sec])

        if output_table:
            print(output_table)
        
        elif self.vmnf_handler['navigation_mode']:
            from simple_term_menu import TerminalMenu

            preview_command = None
            _options_, header = build_options(
                l, 
                ['PathId', 'Method', 'Path', 'SecFlow'], 
                False
            )

            fuzzmenu = TerminalMenu(
                _options_,
                preview_command=preview_command,
                menu_cursor=' → ',
                accept_keys=['i','q'],
                preview_title=""
                #preview_size=10#self.get_terminal_height() - 15
            )
            '''
            spec_info = VFDBOps().get_by_id(
                '_SPECS_', 'spec_id', self.vmnf_handler['spec_id']
            )
            jcbanner_fmt(spec_info.__dict__)

            kbann = normalize(
                header, hcolor, 'msg', show_banner, 
                random_banner, keep_banner, header_size, False
            )
            keep_banner = kbann
            '''
            header_size = len(header) + 10
            hcolor = 'green'
            random_banner = 'default_naviban'
            msg = '⚙ sessions'
            show_banner = False
            keep_banner = 'default_naviban'
            preview_command = None

            kbann = normalize(
                header, hcolor, 'msg', show_banner, 
                random_banner, keep_banner, header_size, False
            )
            fuzz_index = fuzzmenu.show()

        else:
            print()
            
            for path in sort_list(paths_list):
                print(path)
            print()

        return True

    def generate_spec_id(self, api_specs: dict) -> str:
        from core.vmnf_specs import generate_spec_id
        return generate_spec_id(api_specs)

    async def check_api(self):
        jcbanner_fmt({})
        
        # Handle ENV_FALLBACK for api_scan_enabled
        if self.api_scan_enabled == 'ENV_FALLBACK':
            if not self.ENV_FALLBACK_TARGET:
                print(colored("\n[!] No target URL found in environment. Please specify a target or scan an API first.", 'red'))
                print(colored("    Example: vimana run -p jcolt --scan http://api.example.com\n", 'yellow'))
                sys.exit(1)

            self.target_url = self.ENV_FALLBACK_TARGET
            if self.verbose_enabled:
                print(f" → Using target URL from environment: {self.target_url}")
        
        APIUrl = self.target_url.rstrip('/')
        logging.info(f"Initiating API scan for: {APIUrl}")
        
        if self.verbose_enabled:
            print(f"Initiating API scan for: {APIUrl}")

        # Common OpenAPI spec locations
        spec_paths = [
            '/openapi.json',
            '/docs/openapi.json',
            '/api/openapi.json',
            '/swagger/v1/swagger.json'
        ]
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Try each potential spec location
            for spec_path in spec_paths:
                try:
                    full_url = urljoin(APIUrl, spec_path)
                    logging.debug(f"Attempting to fetch spec from: {full_url}")
                    if self.verbose_enabled:
                        print(f"Attempting to fetch spec from: {full_url}")

                    r = await client.get(full_url)
                    
                    if r.status_code == 200:
                        try:
                            self.api_specs = r.json()
                            break
                        except json.JSONDecodeError:
                            logging.debug(f"Invalid JSON response from {full_url}")
                            if self.verbose_enabled:
                                print(f"Invalid JSON response from {full_url}")
                            continue
                            
                except httpx.RequestError as exc:
                    logging.debug(f"Failed to fetch from {spec_path}: {str(exc)}")
                    if self.verbose_enabled:
                        print(f"Failed to fetch from {spec_path}: {str(exc)}")
                    continue
            
            # If no spec found, try root path as fallback
            if not hasattr(self, 'api_specs'):
                try:
                    r = await client.get(APIUrl)
                    if r.status_code == 200:
                        # Check response headers for FastAPI indicators
                        server_header = r.headers.get('server', '').lower()
                        if 'fastapi' in server_header:
                            logging.warning("FastAPI detected but OpenAPI spec not found in common locations")
                            if self.verbose_enabled:
                                print("FastAPI detected but OpenAPI spec not found in common locations")
                                print()

                        raise Exception("No valid OpenAPI specification found")
                except httpx.RequestError as exc:
                    logging.error(f"Failed to connect to API: {str(exc)}")
                    if self.verbose_enabled:
                        print(f"Failed to connect to API: {str(exc)}")
                    sys.exit(1)

        # Validate the spec
        if not isinstance(self.api_specs, dict) or 'paths' not in self.api_specs:
            logging.error("Invalid or non-FastAPI OpenAPI specification")
            if self.verbose_enabled:
                print("Invalid or non-FastAPI OpenAPI specification")
            sys.exit(1)

        # Generate unique spec ID
        self.spec_id = self.generate_spec_id(self.api_specs)
        
        if self.verbose_enabled:
            print(f" → Generated Spec ID: {self.spec_id}")
        
        # After successful spec fetch and validation
        api_info = self.api_specs.get('info', {})
        openapi_version = self.api_specs.get('openapi', '?')
        api_version = api_info.get('version', '?')
        
        # Generate spec ID and prepare paths
        self.full_spec_path = os.path.join(self.abs_cache_path, f"{self.spec_id}.json")
        os.makedirs(self.abs_cache_path, exist_ok=True)

        # Save environment data
        env_data = {
            'JCOLT_SCAN_SPEC_ID': self.spec_id,
            'JCOLT_SCAN_TARGET': APIUrl,
            'JCOLT_API_VERSION': api_version,
            'JCOLT_OPENAPI_VERSION': openapi_version,
            'JCOLT_API_TITLE': api_info.get('title', '?'),
            'JCOLT_LAST_SCAN_DATE': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'JCOLT_TOTAL_PATHS': str(len(self.api_specs['paths'])),
            'JCOLT_API_METHODS': get_methods(self.api_specs)
        }
        
        # Save to environment file
        self.save_jcolt_env(env_data)
        
        # Save spec info to Vimana's database and cache file
        spec_info = {
            'spec_id': self.spec_id,
            'spec_title': api_info.get('title', '?'),
            'fastapi_version': api_version,
            'openapi_version': openapi_version,
            'spec_host': APIUrl,
            'spec_paths': len(self.api_specs['paths']),
            'spec_methods': get_methods(self.api_specs),
            'spec_file_path': self.full_spec_path,
            'spec_date': datetime.now()
        }
        # Register in database
        VFDBOps(**spec_info).register('_SPECS_')
        jcbanner_fmt(spec_info)
        sleep(0.10)

        # Save spec file to cache
        with open(self.full_spec_path, 'w') as f:
            json.dump(self.api_specs, f, indent=4)

        if self.verbose_enabled:
            jcbanner_fmt(spec_info)
            print(f"API scan completed successfully. Spec ID: {self.spec_id}")
            sleep(0.10)

        return True

    def get_api_spec(self):
        jcbanner_fmt({})

        spec_found = VFDBOps().get_by_id('_SPECS_', 'spec_id', self.spec_id)

        if not spec_found:
            print(f' → jcolt@set_spec(): Spec {spec_found} not found!')
            print()
            print()
            sys.exit(1)
        
        spec_file = spec_found.spec_file_path
        if os.path.exists(spec_file):
            with open(spec_file, 'r') as f:
                self.api_specs = json.load(f)
                jcbanner_fmt(spec_found.__dict__)
        else:
            print(f' → jcolt@set_spec(): Spec file {spec_found.spec_id} not found!')
            print()
            sys.exit(1)
        
    def is_set_spec_type(self):
        """
        Determine and set the spec ID based on command line arguments and environment.
        Handles direct spec ID, environment fallback, and inspection modes.
        """
        self.inspect_spec = self.vmnf_handler['inspect']
        api_spec = self.vmnf_handler['apispec_enabled']
        self.spec_id = None
        
        # Handle inspection mode
        if self.inspect_spec:
            if self.inspect_spec.startswith('aS'):
                # Direct spec ID provided
                self.spec_id = self.inspect_spec
            else:
                # For path ID inspection or no argument, use environment spec
                if not self.ENV_FALLBACK_SPEC_ID:
                    print(colored("\n[!] No API specification found in environment. Please scan an API first.", 'red'))
                    print(colored("    Example: vimana run -p jcolt --scan http://api.example.com\n", 'yellow'))
                    sys.exit(1)
                self.spec_id = self.ENV_FALLBACK_SPEC_ID
        
        # Handle other cases
        elif not api_spec:
            if self.fuzzer_enabled == 'ENV_FALLBACK':
                self.fuzzer_enabled = self.ENV_FALLBACK_SPEC_ID
                self.spec_id = self.fuzzer_enabled
            elif self.fuzzer_enabled:
                self.spec_id = self.fuzzer_enabled
        else:
            self.spec_id = api_spec
        
        if self.spec_id and self.verbose_enabled:
            print(f" → Using specification ID: {self.spec_id}")
        
        return bool(self.spec_id)
    
    def set_spec(self):
        if not self.spec_id:
            print(' → jcolt@set_spec(): Error while setting spec_id.')
            return False
    
        self.get_api_spec()
        
        should_parse_specs = self.inspect_spec or self.fuzzer_enabled
        is_fuzzspec = sys.argv[-1] == self.spec_id and sys.argv[-2] == '--fuzzspec'
    
        if should_parse_specs or is_fuzzspec:
            self.spec_info = VFDBOps().get_by_id('_SPECS_', 'spec_id', self.spec_id)
            self.parse_specs()
            sys.exit(1)
        
    def highlight_json(self, data):
        json_str = json.dumps(data, indent=4)
        return highlight(json_str, JsonLexer(), TerminalFormatter())
    
    def load_env(self):
        from core._dbops_.vmnf_dbops import VFDBOps

        envs = VFDBOps().getall('_ENVS_')
        if not envs:
            print(f' → jcolt@set_env(): No environments found!')
            sys.exit(1)

        if self.debug_logging:
            logging.info("Loading from environments...")

        if not any(self.env_name in (env.env_id, env.env_name) for env in envs):
            print(f' → jcolt@set_env(): No environments found for {self.env_name}!')
            sys.exit(0.12)

        print(f' → jcolt@set_env(): Loading environment {self.env_name }...')
        sleep(1)

        env = [env for env in envs if self.env_name in (env.env_id, env.env_name)][0]

        if not env:
            print(f' → jcolt@set_env(): Environment {self.env_name} not found!')
            sys.exit(1)

        if env.env_data is None:
            print(f' → jcolt@set_env(): Environment {self.env_name} is empty!')
            sys.exit(1)

        env_config = env.env_data
        
        print(f' → jcolt@set_env(): Environment loaded successfully!')

        json_output = self.highlight_json(env_config)
        indented_lines = [f"   {line}" for line in json_output.splitlines()]
        print("\n".join(indented_lines))

    def describe_spec(self):
        self.list_paths()
        self.ops.list_opids()
        self.ops.list_schemas()
        self.ops.list_parameters()
        self.ops.list_descriptions()
        self.ops.list_response_codes()
        self.ops.list_tags()
        sys.exit(1)

    def start(self):
        """
        Main entry point for Jc0lt siddhi.
        Handles both direct specification mode and workflow mode.
        """
        # Clear screen initially
        print('\033[2J\033[1;1H' * 3)
        jcbanner()

        # Handle environment loading first if specified
        if self.load_from_env:
            self.load_env()

        # Special standalone commands that don't need spec context
        if self.list_specs:
            list_specs()
            sys.exit(0)

        elif self.flush_specs:
            try:
                s_ids = sys.argv[sys.argv.index('--flush-specs') + 1]
                f_specs = s_ids.replace(',', ' ').split() if isinstance(s_ids, str) else None
            except IndexError:
                f_specs = None
            flush_specs(f_specs, True)
            sys.exit(0)

        elif self.flush_spec:
            f_specs = self.vmnf_handler['flush_spec']
            if isinstance(f_specs, str):
                f_specs = f_specs.replace(',', ' ').split()
            flush_specs(f_specs)
            sys.exit(0)

        # Direct API scan mode - now handles both direct target and ENV_FALLBACK
        if self.api_scan_enabled:
            asyncio.run(self.check_api())
            
            # Show additional environment info when using fallback
            if self.api_scan_enabled == 'ENV_FALLBACK' and self.verbose_enabled:
                print("\nCurrent Environment Configuration:")
                print(f" → API Title: {self.jcolt_env.get('JCOLT_API_TITLE')}")
                print(f" → API Version: {self.jcolt_env.get('JCOLT_API_VERSION')}")
                print(f" → OpenAPI Version: {self.jcolt_env.get('JCOLT_OPENAPI_VERSION')}")
                print(f" → Total Paths: {self.jcolt_env.get('JCOLT_TOTAL_PATHS')}")
                print(f" → Available Methods: {self.jcolt_env.get('JCOLT_API_METHODS')}")
                print(f" → Last Scan: {self.jcolt_env.get('JCOLT_LAST_SCAN_DATE')}\n")
            
            self.list_paths()
            sys.exit(0)

        # Determine if we're in workflow mode
        self.workflow_mode = not any([
            self.vmnf_handler['apispec_enabled'],
            self.inspect_spec,
            self.fuzzer_enabled not in [False, 'ENV_FALLBACK']
        ])

        # Display appropriate banner
        if self.workflow_mode:
            self.workflow_banner = """
            ╔══════════════════════════════════════════════════════════════╗
            ║                                                              ║
            ║                   JC0LT WORKFLOW MODE                        ║
            ║                                                              ║
            ║  [*] Automated API Testing & Security Assessment Pipeline    ║
            ║  [*] Powered by Vimana Framework - @s4dhulabs                ║
            ║                                                              ║
            ╚══════════════════════════════════════════════════════════════╝
            """
            if not self.colors_disabled:
                print(colored(self.workflow_banner, 'cyan', attrs=['bold']))
            else:
                print(self.workflow_banner)
            print("\n → Loading workflow configuration...")
            sleep(0.5)

            # In workflow mode, always use ENV_FALLBACK_SPEC_ID
            if not self.ENV_FALLBACK_SPEC_ID:
                print(colored("\n[!] No API specification found in environment. Please scan an API first.", 'red'))
                print(colored("    Example: vimana run -p jcolt --scan http://api.example.com\n", 'yellow'))
                sys.exit(1)
            
            # Set the spec from environment for workflow mode
            self.vmnf_handler['apispec_enabled'] = self.ENV_FALLBACK_SPEC_ID
        else:
            jcbanner()

        # Load and validate spec configuration
        if not self.is_set_spec_type():
            print(' → jcolt@start(): No valid specification provided or found in environment')
            sys.exit(1)

        # Load the API specification
        self.set_spec()
        self.ops = jcOps(self.api_specs, self.vmnf_handler)

        # Handle inspection mode
        if self.inspect_spec:
            inspect_value = self.inspect_spec
            if inspect_value.startswith('aS') or inspect_value == 'ENV_FALLBACK':
                # Full OAS inspection
                print(colored("\n[*] Inspecting API Specification", 'cyan'))
                print(colored(f"[*] Spec ID: {self.spec_id}\n", 'cyan'))
                self.describe_spec()
            else:
                # Path ID inspection
                print(colored(f"\n[*] Inspecting Path ID: {inspect_value}", 'cyan'))
                print(colored(f"[*] In Spec ID: {self.spec_id}\n", 'cyan'))
                self.parse_specs()
            sys.exit(0)

        # Handle all spec-dependent operations
        if self.describe_mode:
            self.describe_spec()
        elif self.serialization_test:
            #print("🎷 Working on it...")
            self.run_serialization_tests()
        elif self.pydantic_test:
            self.run_pydantic_tests()
        elif self.fingerprint_enabled:
            print("🎷 Working on it...")
        elif self.list_opids:
            self.ops.list_opids()
        elif self.list_pydantic_models:
            self.ops.list_pydantic_models()
        elif self.list_field_constraints:
            self.ops.list_field_constraints()
        elif self.list_endpoint_models:
            self.ops.list_endpoint_models()
        elif self.list_security_fields:
            self.ops.list_security_fields()
        elif self.list_enums:
            self.ops.list_enums()
        elif self.list_model_relationships:
            self.ops.list_model_relationships()
        elif self.list_validation_coverage:
            self.ops.list_validation_coverage()
        elif self.list_parameters:
            self.ops.list_parameters()
        elif self.list_schemas:
            self.ops.list_schemas()
        elif self.list_response_codes:
            self.ops.list_response_codes()
        elif self.list_examples:
            self.ops.list_examples()
        elif self.list_tags:
            self.ops.list_tags()
        elif self.list_descriptions:
            self.ops.list_descriptions()
        elif self.list_response_headers:
            self.ops.list_response_headers()
        elif self.list_paths_mode:
            self.list_paths()
        elif self.schema_validate:
            validator = ValidateSchema(
                self.api_specs, self.spec_id, self.vmnf_handler
            )
            validator.run()
        else:
            # Default behavior in workflow mode - list paths
            self.list_paths()

            
            
