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

import json
import os
from typing import Dict, List, Any, Optional, Union


class JsonFormatter:
    """Formats detection results as JSON for API integration with aggregate results support"""
    
    def format(self, results: Dict[str, Any]) -> str:
        """
        Format results as a JSON string
        
        Args:
            results: Detection results dictionary
            
        Returns:
            JSON string of formatted results
        """
        # Check if these are aggregate results or single target results
        if "targets" in results and isinstance(results["targets"], list):
            # Aggregate results
            formatted = self._format_aggregate_results(results)
        else:
            # Single target results
            formatted = self._format_results(results)
        
        # Convert to JSON string with indentation
        return json.dumps(formatted, indent=2)
        
    def _format_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a formatted version of the results suitable for API consumption
        
        Args:
            results: Raw detection results
            
        Returns:
            Formatted results dictionary
        """
        # Clone the results to avoid modifying the original
        formatted = {
            "target": results.get("target_url", ""),
            "scan_time": results.get("scan_time", 0),
            "timestamp": results.get("timestamp", ""),
            "ip_info": results.get("ip_info", {}),
            "server_info": results.get("server_info", {}),
            "security": {
                "headers": results.get("security_headers", {})
            },
            "frameworks": []
        }
        
        # Format framework results
        for fw in results.get("frameworks", []):
            framework_entry = {
                "name": fw.get("name", ""),
                "confidence": fw.get("confidence", 0),
                "version": fw.get("version", "Unknown"),
                "components": fw.get("components", []),
                "vulnerabilities": fw.get("vulnerabilities", []),
                "metadata": {
                    "description": fw.get("metadata", {}).get("description", ""),
                    "website": fw.get("metadata", {}).get("website", "")
                }
            }
            
            # Add formatted evidence
            if "evidence" in results and fw["name"] in results["evidence"]:
                evidence_list = results["evidence"][fw["name"]]
                evidence_by_type = {}
                
                for evidence in evidence_list:
                    parts = evidence.split(": ", 1)
                    if len(parts) == 2:
                        evidence_type, detail = parts
                        if evidence_type not in evidence_by_type:
                            evidence_by_type[evidence_type] = []
                        evidence_by_type[evidence_type].append(detail)
                        
                framework_entry["evidence"] = evidence_by_type
                
            formatted["frameworks"].append(framework_entry)
            
        return formatted
        
    def _format_aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format aggregate results from multiple targets
        
        Args:
            results: Aggregate results dictionary
            
        Returns:
            Formatted aggregate results dictionary
        """
        # Clone the aggregate results to avoid modifying the original
        formatted = {
            "summary": {
                "target_count": len(results.get("targets", [])),
                "scan_time": results.get("scan_time", 0),
                "timestamp": results.get("timestamp", ""),
                "framework_distribution": results.get("framework_counts", {})
            },
            "targets": []
        }
        
        # Add target details
        for target in results.get("targets", []):
            target_entry = {
                "url": target.get("url", ""),
                "top_framework": target.get("top_framework", "Unknown"),
                "confidence": target.get("confidence", 0),
                "scan_time": target.get("scan_time", 0),
                "detected_frameworks": target.get("detected_frameworks", 0),
                "components": target.get("components", 0),
                "version": target.get("version", "Unknown")
            }
            
            formatted["targets"].append(target_entry)
            
        # Calculate overall statistics
        if formatted["targets"]:
            total_time = sum(target.get("scan_time", 0) for target in formatted["targets"])
            avg_time = total_time / len(formatted["targets"])
            
            formatted["summary"]["average_scan_time"] = avg_time
            formatted["summary"]["total_frameworks_detected"] = sum(target.get("detected_frameworks", 0) for target in formatted["targets"])
            formatted["summary"]["total_components_detected"] = sum(target.get("components", 0) for target in formatted["targets"])
            
        return formatted
        
    def save(self, results: Dict[str, Any], output_file: str) -> None:
        """
        Save results to a JSON file
        
        Args:
            results: Detection results dictionary
            output_file: Path to output file
        """
        # Check if these are aggregate results or single target results
        if "targets" in results and isinstance(results["targets"], list):
            formatted = self._format_aggregate_results(results)
        else:
            formatted = self._format_results(results)
            
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(formatted, f, indent=2)