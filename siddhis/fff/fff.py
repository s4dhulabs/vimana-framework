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


import asyncio
import aiohttp
import json
import time
import statistics
import sys
import math
import os
from concurrent.futures import ThreadPoolExecutor
import threading
import psutil
import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import argparse
from tqdm import tqdm
from colorama import Fore, Style, init
import struct
import decimal
from core._dbops_.vmnf_dbops import VFDBOps  
from .engines.fff_test_engine import FastAPIExhaustionTester, FloatingPointVectors


class siddhi:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.debug_logging = self.vmnf_handler.get('debug_logging')
        self.verbose_logging = self.vmnf_handler.get('verbose_logging') 
        self.verbose_enabled = self.vmnf_handler.get('verbose')
        init(autoreset=True)
        
    def start(self):

        target_url = None
        # If fuzzspec is enabled, run spec-driven tests and return immediately
        if self.vmnf_handler.get('fuzzerspec_enabled'):
            try:
                db_ops = VFDBOps()
                spec_id = self.vmnf_handler.get('fuzzerspec_enabled') if self.vmnf_handler.get('fuzzerspec_enabled') != 'ENV_FALLBACK' else None
                if not spec_id:
                    with open(os.path.expanduser('~/.jcolt_env'), 'r') as f:
                        env_data = dict(line.strip().split('=') for line in f if '=' in line)
                    spec_id = env_data.get('JCOLT_SCAN_SPEC_ID')
                if not spec_id:
                    print(Fore.RED + "[-] No spec ID provided and no last scan spec found in ~/.jcolt_env")
                    sys.exit(1)
                spec_found = db_ops.get_by_id('_SPECS_', 'spec_id', spec_id)
                if not spec_found:
                    print(Fore.RED + f"[-] Spec {spec_id} not found in database")
                    sys.exit(1)
                # Always load the OpenAPI spec from the file
                if hasattr(spec_found, 'spec_file_path') and spec_found.spec_file_path:
                    try:
                        with open(spec_found.spec_file_path, 'r') as f:
                            spec = json.load(f)
                    except Exception as e:
                        print(Fore.RED + f"[-] Could not load OpenAPI spec from file: {e}")
                        sys.exit(1)
                else:
                    print(Fore.RED + f"[-] No spec_file_path found in spec object.")
                    sys.exit(1)

                target_url = getattr(spec_found, 'target_url', None) or getattr(spec_found, 'spec_host', None)

                if not target_url or not spec:
                    print(Fore.RED + "[-] No target URL or spec found in spec object")
                    sys.exit(1)
                print(Fore.CYAN + f"[*] Using target from spec {spec_id}: {target_url}")
            except Exception as e:
                print(Fore.RED + f"[-] Error loading spec: {str(e)}")
                sys.exit(1)
            
            if self.vmnf_handler.get('verbose'):
                print(Fore.CYAN + "[FFF] Starting spec-driven tests...")
            
            vectors = FloatingPointVectors(self.vmnf_handler)
            results, analysis = vectors.run_spec_tests(
                spec,
                target_url,
                test_type=self.vmnf_handler.get('test_type'),
                filter_by_method=self.vmnf_handler.get('filter_by_method'),
                filter_by_tag=self.vmnf_handler.get('filter_by_tag'),
                filter_by_opid=self.vmnf_handler.get('filter_by_opid'),
                endpoint=self.vmnf_handler.get('endpoint'),
                verbose=self.vmnf_handler.get('verbose')
            )
            if self.vmnf_handler.get('debug'):
                print()
                print(Fore.CYAN + f"[FFF] Finished run_spec_tests. Results: {len(results)}")
                print()
            
            if analysis:
                FastAPIExhaustionTester(target_url).print_analysis(analysis)
            else:
                print(Fore.YELLOW + "[FFF] No analysis results to print.")
            if self.vmnf_handler.get('output'):
                output_data = {
                    'analysis': analysis,
                    'results': [
                        {
                            'status_code': r.status_code,
                            'response_time': r.response_time,
                            'test_vector': r.test_vector,
                            'payload_type': r.payload_type,
                            'error_type': r.error_type,
                            'error_message': r.error_message
                        }
                        for r in results
                    ]
                }
                with open(self.vmnf_handler.get('output'), 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"\n💾 Results saved to {self.vmnf_handler.get('output')}")
            return
        else:
            target_url = self.vmnf_handler.get('target_url')
        
        if not target_url:
            sys.exit(1)
        
        tester = FastAPIExhaustionTester(target_url, self.vmnf_handler.get('endpoint'))
        
        if self.vmnf_handler.get('check_debug'):
            print(f"🎯 Target: {tester.target_url}{tester.endpoint}")
            debug_result = tester.check_debug_mode(self.vmnf_handler.get('verbose'))
            
            if self.vmnf_handler.get('output'):
                with open(self.vmnf_handler.get('output'), 'w') as f:
                    json.dump(debug_result, f, indent=2)
                print(f"\n💾 Debug check results saved to {self.vmnf_handler.get('output')}")
            
            sys.exit(0)
        
        test_type = self.vmnf_handler.get('test_type')
        print(f"🎯 Target: {tester.target_url}{tester.endpoint}")
        print(f"🧪 Test Type: {test_type}")
        
        results = []
        analysis = {}        

        if test_type == "single":
            payload = tester.create_nan_payload()
            result = tester.single_request_test(payload, test_vector="basic_nan", payload_type="single_test")
            print(f"[+] Single request result: Status {result.status_code}, Time: {result.response_time:.2f}s")
            if result.error_type:
                print(f"[+] Error type: {result.error_type}")
                print(f"[+] Error message: {result.error_message}")
            
            results = [result]
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "concurrent":
            results = tester.concurrent_test(
                self.vmnf_handler.get('requests'), 
                self.vmnf_handler.get('payload_size'), 
                self.vmnf_handler.get('max_workers')
            )
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "progressive":
            results_dict = tester.progressive_size_test(1, 20, 2)
            results = list(results_dict.values())
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "sustained":
            results = tester.sustained_attack_test(self.vmnf_handler.get('duration'), 0.5)
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "ieee754":
            results = tester.ieee_754_test_suite()
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "precision":
            results = tester.precision_attack_suite()
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "mathematical":
            results = tester.mathematical_edge_case_suite()
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "confusion":
            results = tester.type_confusion_suite()
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        elif test_type == "comprehensive":
            results = tester.comprehensive_float_test_suite()
            analysis = tester.analyze_results(results)
            tester.print_analysis(analysis)
        
        if self.vmnf_handler.get('output'):
            output_data = {
                'analysis': analysis,
                'results': [
                    {
                        'status_code': r.status_code,
                        'response_time': r.response_time,
                        'test_vector': r.test_vector,
                        'payload_type': r.payload_type,
                        'error_type': r.error_type,
                        'error_message': r.error_message
                    }
                    for r in results
                ]
            }
            
            with open(self.vmnf_handler.get('output'), 'w') as f:
                json.dump(output_data, f, indent=2)
            print(f"\n💾 Results saved to {self.vmnf_handler.get('output')}")

