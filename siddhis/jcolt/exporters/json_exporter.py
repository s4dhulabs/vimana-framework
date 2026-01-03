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
from datetime import datetime
from typing import Dict, List, Any, Optional


class JcoltFuzzspecJsonExporter:
    """
    JSON exporter for JColt fuzzspec results.
    Converts terminal output data into structured JSON format for CI/CD integration.
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
        return f"jcolt_fuzzspec_{timestamp}.json"
    
    def _extract_endpoint_info(self, path: str, fuzz_entries: List[Dict]) -> Dict[str, Any]:
        """
        Extract endpoint information from fuzz entries.
        
        Args:
            path: API endpoint path
            fuzz_entries: List of fuzz test entries for this endpoint
            
        Returns:
            Dictionary containing endpoint metadata
        """
        if not fuzz_entries:
            return {}
            
        # Get properties from first entry (they should be consistent)
        first_entry = fuzz_entries[0]
        properties = first_entry.get('properties', {})
        
        return {
            "path": path,
            "summary": properties.get('summary', ''),
            "operation_id": properties.get('operationId', ''),
            "tags": properties.get('tags', []),
            "method": first_entry.get('method', '').upper(),
            "total_tests": len(fuzz_entries)
        }
    
    def _format_request_data(self, fuzz_entry: Dict) -> Dict[str, Any]:
        """
        Format request data for JSON export.
        
        Args:
            fuzz_entry: Single fuzz test entry
            
        Returns:
            Formatted request data
        """
        request_data = {
            "method": fuzz_entry.get('method', '').upper(),
            "path": fuzz_entry.get('path', ''),
            "host": fuzz_entry.get('host', ''),  # Include host for test reproducibility
            "headers": {}
        }
        
        # Extract body if present and handle NaN values
        body = fuzz_entry.get('body')
        if body is not None:
            if isinstance(body, str):
                # Try to parse as JSON, otherwise keep as string
                try:
                    parsed_body = json.loads(body)
                    request_data["body"] = self._sanitize_json_values(parsed_body)
                except json.JSONDecodeError:
                    request_data["body"] = body
            else:
                request_data["body"] = self._sanitize_json_values(body)
        
        # Add any additional request metadata
        if 'spec_path' in fuzz_entry:
            request_data["spec_path"] = fuzz_entry['spec_path']
        if 'fuzz_rounds' in fuzz_entry:
            request_data["fuzz_rounds"] = fuzz_entry['fuzz_rounds']
            
        return request_data
    
    def _sanitize_json_values(self, obj: Any) -> Any:
        """
        Recursively sanitize JSON values to handle NaN, Infinity, etc.
        
        Args:
            obj: Object to sanitize
            
        Returns:
            Sanitized object safe for JSON serialization
        """
        import math
        
        if isinstance(obj, dict):
            return {key: self._sanitize_json_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_json_values(item) for item in obj]
        elif isinstance(obj, float):
            if math.isnan(obj):
                return "NaN"
            elif math.isinf(obj):
                return "Infinity" if obj > 0 else "-Infinity"
            else:
                return obj
        else:
            return obj
    
    def _format_response_data(self, fuzz_entry: Dict) -> Dict[str, Any]:
        """
        Format response data for JSON export.
        
        Args:
            fuzz_entry: Single fuzz test entry
            
        Returns:
            Formatted response data
        """
        response = fuzz_entry.get('response')
        response_text = fuzz_entry.get('response_text')
        
        if not response:
            return {"error": "No response data available"}
        
        response_data = {
            "status_code": getattr(response, 'status', None),
            "reason": getattr(response, 'reason', ''),
            "headers": {},
            "body": None
        }
        
        # Extract headers if available
        if hasattr(response, 'headers'):
            response_data["headers"] = dict(response.headers)
        
        # Format response body and sanitize values
        if response_text is not None:
            if isinstance(response_text, (dict, list)):
                response_data["body"] = self._sanitize_json_values(response_text)
            elif isinstance(response_text, str):
                # Try to parse as JSON
                try:
                    parsed_response = json.loads(response_text)
                    response_data["body"] = self._sanitize_json_values(parsed_response)
                except json.JSONDecodeError:
                    response_data["body"] = response_text
            else:
                response_data["body"] = self._sanitize_json_values(str(response_text))
        
        # Add protocol version if available
        if hasattr(response, 'version'):
            version = response.version
            response_data["http_version"] = f"{version.major}.{version.minor}"
        
        return response_data
    
    def _format_audit_data(self, fuzz_entry: Dict) -> Dict[str, Any]:
        """
        Format audit/analysis data for JSON export.
        
        Args:
            fuzz_entry: Single fuzz test entry
            
        Returns:
            Formatted audit data
        """
        audit_data = fuzz_entry.get('response_status_audit', {})
        
        formatted_audit = {
            "expected_status_codes": audit_data.get('expected_status_codes', []),
            "actual_status_code": audit_data.get('actual_status_code'),
            "status_mismatch": audit_data.get('status_mismatch', False),
            "unexpected_status": audit_data.get('unexpected_status', False)
        }
        
        # Add timing information if available
        if 'duration_ms' in fuzz_entry:
            formatted_audit["duration_ms"] = fuzz_entry['duration_ms']
        if 'timestamp' in fuzz_entry:
            formatted_audit["timestamp"] = fuzz_entry['timestamp']
            
        return formatted_audit
    
    def export_fuzz_results(self, fuzz_results: Dict[str, List[Dict]], additional_metadata: Optional[Dict] = None) -> str:
        """
        Export fuzz results to JSON format.
        
        Args:
            fuzz_results: Dictionary containing fuzz test results organized by endpoint
            additional_metadata: Additional metadata to include in export
            
        Returns:
            Path to the created JSON file
        """
        # Calculate summary statistics
        total_requests = sum(len(entries) for entries in fuzz_results.values())
        total_endpoints = len(fuzz_results)
        
        # Build metadata section
        metadata = {
            "export_timestamp": self.export_timestamp,
            "framework": "Vimana JColt",
            "export_type": "fuzzspec_results",
            "total_endpoints": total_endpoints,
            "total_requests": total_requests,
            "spec_info": self.spec_info
        }
        
        # Add additional metadata if provided
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Process endpoints
        endpoints = []
        test_id_counter = 1
        
        for path, fuzz_entries in fuzz_results.items():
            endpoint_info = self._extract_endpoint_info(path, fuzz_entries)
            
            # Process tests for this endpoint
            tests = []
            for fuzz_entry in fuzz_entries:
                test_data = {
                    "test_id": test_id_counter,
                    "request": self._format_request_data(fuzz_entry),
                    "response": self._format_response_data(fuzz_entry),
                    "audit": self._format_audit_data(fuzz_entry)
                }
                tests.append(test_data)
                test_id_counter += 1
            
            endpoint_info["tests"] = tests
            endpoints.append(endpoint_info)
        
        # Build final JSON structure
        export_data = {
            "metadata": metadata,
            "endpoints": endpoints
        }
        
        # Write to file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n → JSON export completed: {self.output_file}")
            print(f" → Total endpoints: {total_endpoints}")
            print(f" → Total requests: {total_requests}")
            
            return self.output_file
            
        except Exception as e:
            print(f"\n → Error exporting JSON: {str(e)}")
            raise
    
    def export_with_summary_stats(self, fuzz_results: Dict[str, List[Dict]], additional_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Export results and return summary statistics.
        
        Args:
            fuzz_results: Dictionary containing fuzz test results
            additional_metadata: Additional metadata to include
            
        Returns:
            Dictionary containing export summary
        """
        # Calculate detailed statistics
        stats = {
            "total_endpoints": len(fuzz_results),
            "total_requests": 0,
            "status_codes": {},
            "endpoints_with_errors": 0,
            "error_rate": 0.0
        }
        
        error_endpoints = set()
        
        for path, entries in fuzz_results.items():
            stats["total_requests"] += len(entries)
            
            for entry in entries:
                response = entry.get('response')
                if response:
                    status_code = getattr(response, 'status', 'unknown')
                    stats["status_codes"][status_code] = stats["status_codes"].get(status_code, 0) + 1
                    
                    # Track errors (4xx, 5xx)
                    if isinstance(status_code, int) and status_code >= 400:
                        error_endpoints.add(path)
        
        stats["endpoints_with_errors"] = len(error_endpoints)
        if stats["total_endpoints"] > 0:
            stats["error_rate"] = (stats["endpoints_with_errors"] / stats["total_endpoints"]) * 100
        
        # Export the file
        output_file = self.export_fuzz_results(fuzz_results, additional_metadata)
        
        # Return summary
        return {
            "output_file": output_file,
            "statistics": stats
        } 