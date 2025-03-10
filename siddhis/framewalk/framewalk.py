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

import sys
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .utils.http import RequestManager
from .utils.result import ResultManager
from .presentation.terminal import TerminalPresenter
from .presentation.json import JsonFormatter
from .orchestrator.fwalk_orchestrator import framewalkOrchestrator


class siddhi:
    """
    Main FRAMEWALK handler class that orchestrates the framework detection process
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the siddhi handler
        
        Args:
            **kwargs: Optional keyword arguments for configuration from Vimana
        """
        self.detector = framewalkOrchestrator(**kwargs)
        self.presenter = TerminalPresenter()
        self.vmnf_handler = kwargs  
        self.config = kwargs.copy()  
        self.aggregate_results = {
            "targets": [],
            "framework_counts": {},
            "scan_time": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_frameworks_detected": 0,
            "total_components_detected": 0
        }
        
    def start(self, args=None) -> Dict[str, Any]:
        """
        Main entry point for framework detection - called by Vimana
        
        Args:
            args: Not used in Vimana integration, kept for backward compatibility
        
        Returns:
            Dictionary with detection results
        """
        try:
            # Multi Targets
            file_path = self.vmnf_handler.get('file_scope')
            summary_only = self.vmnf_handler.get('summary_only', False)
            
            if summary_only:
                self.presenter.print_header()
            
            start_time = time.time()
            
            if file_path:
                with open(file_path, 'r') as f:
                    targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                for idx, target in enumerate(targets):
                    if summary_only:
                        print(f"Scanning target: {target}")
                    else:
                        if idx > 0:
                            print("\n" + "─" * 80 + "\n")
                            
                        print(f"\n[Target {idx+1}/{len(targets)}] Scanning: {target}")

                        if idx == 0:
                            self.presenter.print_header()
                    
                    target_config = self.vmnf_handler.copy()
                    target_config['target_url'] = target
                    
                    # Configure detector with current target config
                    self.detector.configure(target_config)
                    
                    # Run the scan``
                    results = self.detector.run()
                    
                    # Add to aggregate results, we have a bug here, I'll fix it soon
                    if results and "frameworks" in results:
                        self._update_aggregate_results(results, target)
                
                # scan time
                self.aggregate_results["scan_time"] = time.time() - start_time
                
                if not summary_only:
                    print("\n" + "─" * 80 + "\n")
                
                self.presenter._print_aggregate_results_rich(self.aggregate_results)
                
                return self.aggregate_results
                
            else:
                target_url = self.vmnf_handler.get('target_url')
                if not target_url:
                    target_url = self.vmnf_handler.get('target_dir')
                if not target_url:
                    target_url = self.vmnf_handler.get('single_target')
                
                if not target_url:
                    raise ValueError("No target specified. Use --target-url, --target, or --file")
                
                self.detector.config['target_url'] = target_url
                
                self.presenter.print_header()
                result = self.detector.run()
                return result
                
        except KeyboardInterrupt:
            print("\nScan interrupted by user", file=sys.stderr)
            return {"error": "Scan interrupted by user"}
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)

            if self.vmnf_handler.get('verbose'):
                import traceback
                traceback.print_exc()
            return {"error": str(e)}
    
    def _update_aggregate_results(self, results: Dict[str, Any], target: str) -> None:
        """
        Update aggregate results with the current scan results
        
        Args:
            results: Results from the current scan
            target: Original target URL
        """
        top_framework = None
        top_confidence = 0
        framework_count = 0
        component_count = 0
        
        for fw in results.get("frameworks", []):
            framework_name = fw.get("name", "Unknown")
            if framework_name not in self.aggregate_results["framework_counts"]:
                self.aggregate_results["framework_counts"][framework_name] = 0
            self.aggregate_results["framework_counts"][framework_name] += 1
            
            confidence = fw.get("confidence", 0)
            if confidence > top_confidence:
                top_confidence = confidence
                top_framework = framework_name
                
            framework_count += 1
            component_count += len(fw.get("components", []))
        
        self.aggregate_results["targets"].append({
            "url": results.get("target_url", target),
            "top_framework": top_framework,
            "confidence": top_confidence,
            "scan_time": results.get("scan_time", 0),
            "detected_frameworks": framework_count,
            "components": component_count,
            "version": results.get("frameworks", [{}])[0].get("version", "Unknown") if results.get("frameworks") else "Unknown"
        })
        
        self.aggregate_results["total_frameworks_detected"] += framework_count
        self.aggregate_results["total_components_detected"] += component_count


if __name__ == "__main__":
    detector = siddhi()
    detector.start()