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

import json
import os
import math
from datetime import datetime
from typing import Dict, List, Any, Optional


class PySerialJsonExporter:
    """
    JSON exporter for PySerial serialization test results.
    Converts test results into structured JSON format for CI/CD integration.
    """
    
    def __init__(self, output_file: Optional[str] = None, spec_info: Optional[Dict] = None):
        """
        Initialize the JSON exporter.
        
        Args:
            output_file: Custom output filename, if None generates default
            spec_info: Specification metadata information
        """
        self.output_file = output_file or self._generate_default_filename()
        self.spec_info = spec_info or {}
        self.export_timestamp = datetime.now().isoformat()
        
    def _generate_default_filename(self) -> str:
        """Generate default filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"pyserial_tests_{timestamp}.json"
        
    def _sanitize_json_values(self, obj: Any) -> Any:
        """
        Recursively sanitize values to ensure JSON serialization compatibility.
        Handles NaN, Infinity, and other problematic values.
        """
        if isinstance(obj, dict):
            return {k: self._sanitize_json_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_json_values(v) for v in obj]
        elif isinstance(obj, float):
            if math.isnan(obj):
                return "NaN"
            elif math.isinf(obj):
                return "Infinity" if obj > 0 else "-Infinity"
            else:
                return obj
        else:
            return obj
            
    def _extract_host_info(self, results: Dict[str, Any]) -> str:
        """Extract host information from test results."""
        # Try to get host from spec_info first
        if self.spec_info and 'host' in self.spec_info:
            return self.spec_info['host']
            
        # Try to extract from test results
        for model_name, model_data in results.items():
            if isinstance(model_data, dict):
                fields = model_data.get('fields', {})
                if isinstance(fields, dict):
                    serialization_tests = fields.get('serialization_tests', [])
                    if isinstance(serialization_tests, list):
                        for test in serialization_tests:
                            if isinstance(test, dict):
                                details = test.get('details', {})
                                if isinstance(details, dict):
                                    request = details.get('request', {})
                                    if isinstance(request, dict):
                                        url = request.get('url', '')
                                        if url:
                                            # Extract host from URL
                                            from urllib.parse import urlparse
                                            parsed = urlparse(url)
                                            if parsed.netloc:
                                                return f"{parsed.scheme}://{parsed.netloc}"
        
        return "unknown"
        
    def _calculate_test_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive test statistics."""
        stats = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'vulnerabilities_found': 0,
            'models_tested': 0,
            'test_categories': set(),
            'error_rate': 0.0,
            'vulnerability_rate': 0.0
        }
        
        stats['models_tested'] = len(results)
        
        for model_name, model_data in results.items():
            if isinstance(model_data, dict):
                fields = model_data.get('fields', {})
                if isinstance(fields, dict):
                    serialization_tests = fields.get('serialization_tests', [])
                    if isinstance(serialization_tests, list):
                        for test in serialization_tests:
                            if isinstance(test, dict):
                                stats['total_tests'] += 1
                                
                                # Track test categories
                                if 'category' in test:
                                    stats['test_categories'].add(test['category'])
                                    
                                # Count pass/fail
                                if test.get('pass', False):
                                    stats['passed_tests'] += 1
                                else:
                                    stats['failed_tests'] += 1
                                    
                                # Count vulnerabilities
                                if 'vulnerability_details' in test:
                                    stats['vulnerabilities_found'] += 1
        
        # Calculate rates
        if stats['total_tests'] > 0:
            stats['error_rate'] = round((stats['failed_tests'] / stats['total_tests']) * 100, 1)
            stats['vulnerability_rate'] = round((stats['vulnerabilities_found'] / stats['total_tests']) * 100, 1)
            
        # Convert set to list for JSON serialization
        stats['test_categories'] = list(stats['test_categories'])
        
        return stats
        
    def _build_json_structure(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build the complete JSON structure for export."""
        host = self._extract_host_info(results)
        stats = self._calculate_test_statistics(results)
        
        json_structure = {
            "metadata": {
                "export_timestamp": self.export_timestamp,
                "framework": "Vimana Framework",
                "plugin": "PySerial",
                "plugin_version": "1.0.0",
                "test_type": "serialization_security_testing",
                "export_format": "json",
                "exporter_version": "1.0.0"
            },
            "spec_info": {
                "spec_id": self.spec_info.get('spec_id', 'unknown'),
                "spec_name": self.spec_info.get('spec_name', 'unknown'),
                "host": host,
                "framework_type": self.spec_info.get('framework_type', 'unknown'),
                "description": self.spec_info.get('description', 'Python serialization security testing')
            },
            "test_summary": {
                "total_tests": stats['total_tests'],
                "passed_tests": stats['passed_tests'],
                "failed_tests": stats['failed_tests'],
                "vulnerabilities_found": stats['vulnerabilities_found'],
                "models_tested": stats['models_tested'],
                "test_categories": stats['test_categories'],
                "error_rate_percent": stats['error_rate'],
                "vulnerability_rate_percent": stats['vulnerability_rate']
            },
            "models": []
        }
        
        # Process each model's test results
        for model_name, model_data in results.items():
            if isinstance(model_data, dict):
                model_entry = {
                    "model_name": model_name,
                    "tests": []
                }
                
                fields = model_data.get('fields', {})
                if isinstance(fields, dict):
                    serialization_tests = fields.get('serialization_tests', [])
                    if isinstance(serialization_tests, list):
                        for test in serialization_tests:
                            if isinstance(test, dict):
                                test_entry = {
                                    "test_name": test.get('name', 'unknown'),
                                    "test_type": test.get('test_type', 'serialization'),
                                    "category": test.get('category', 'unknown'),
                                    "description": test.get('description', ''),
                                    "expected_result": test.get('expected_result', ''),
                                    "actual_result": test.get('actual_result', ''),
                                    "status_code": test.get('status_code'),
                                    "pass": test.get('pass', False),
                                    "details": test.get('details', {}),
                                    "host": host
                                }
                                
                                # Add vulnerability details if present
                                if 'vulnerability_details' in test:
                                    test_entry['vulnerability_details'] = test['vulnerability_details']
                                    
                                model_entry['tests'].append(test_entry)
                
                json_structure['models'].append(model_entry)
        
        return json_structure
        
    def export_results(self, results: Dict[str, Any]) -> bool:
        """
        Export test results to JSON file.
        
        Args:
            results: Test results dictionary from PySerial
            
        Returns:
            bool: True if export successful, False otherwise
        """
        try:
            # Build the JSON structure
            json_data = self._build_json_structure(results)
            
            # Sanitize values for JSON compatibility
            json_data = self._sanitize_json_values(json_data)
            
            # Write to file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            # Print success message with summary
            host = self._extract_host_info(results)
            stats = self._calculate_test_statistics(results)
            
            print(f"\n → JSON export completed: {self.output_file}")
            print(f" → Target Host: {host}")
            print(f" → Models Tested: {stats['models_tested']}")
            print(f" → Total Tests: {stats['total_tests']}")
            print(f" → Vulnerabilities Found: {stats['vulnerabilities_found']}")
            print(f" → Error Rate: {stats['error_rate']}%")
            
            return True
            
        except Exception as e:
            print(f" → Error exporting JSON: {str(e)}")
            return False 