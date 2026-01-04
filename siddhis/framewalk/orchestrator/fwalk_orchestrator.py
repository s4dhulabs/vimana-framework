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
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import hashlib

from ..utils.http import RequestManager
from ..utils.result import ResultManager
from ..presentation.terminal import TerminalPresenter
from ..presentation.json import JsonFormatter
from ..utils.progress import ProgressTracker


class framewalkOrchestrator:
    """
    Main FRAMEWALK handler class that orchestrates the framework detection process
        this was previously named as vixtriOr :D
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the orchestrator
        
        Args:
            **kwargs: Optional keyword arguments for configuration from Vimana
        """
        self.request_manager = None
        self.result_manager = None
        self.detectors = []
        self.engines = []
        self.presenter = None
        self.json_formatter = None
        self.progress_tracker = None  # Will be initialized in configure
        
        self.config = kwargs  # Store Vimana handler parameters
        self.aggregate_results = {
            "targets": [],
            "framework_counts": {},
            "scan_time": 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # test2: Initialize immediately with the provided configuration
        if kwargs:
            self.configure(kwargs)


        issue_type = 'dast/output'
        plugin_scope = f'python/{issue_type}'
        self.cache_dir = f".vimana/cache/{plugin_scope}"
        self.abs_cache_path = os.path.join(os.path.expanduser("~"), self.cache_dir)

        self.scan_time = datetime.now()
        scan_pattern = f"{self.scan_time}{self.config}"
        sha256 = hashlib.sha256()
        sha256.update(scan_pattern.encode())
        self.scan_hash = sha256.hexdigest()
        self.scan_id = self.scan_hash[:10]
        self.app_name = None
        
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the handler with the provided configuration
        
        Args:
            config: Configuration dictionary with settings for detection
        """
        # Update configuration
        if not config and self.config:
            config = self.config
        elif self.config:
            self.config.update(config)
            config = self.config
            
        # Vim4na Framewørk Project
        target_url = config.get('target_url')
        if not target_url:
            target_url = config.get('target_dir')
        if not target_url:
            target_url = config.get('single_target')
        
        if not target_url:
            return
            
        self.presenter = TerminalPresenter(
            show_evidence=not config.get('no_evidence', False),
            show_metadata=not config.get('no_metadata', False),
            verbose=config.get('verbose', False)
        )
        
        self.json_formatter = JsonFormatter()
        
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
            
            class DetailedProgress(Progress):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.verbose = config.get('verbose', False)
                    self.total_steps = 100  # Default value
                    self.task_id = None
                    
                def print_verbose(self, message: str) -> None:
                    """Print a verbose message if verbose mode is enabled"""
                    if self.verbose:
                        print(message)
                
                def set_total_steps(self, total: int) -> None:
                    """Set total steps for the task"""
                    self.total_steps = total
                    
                def update_operation(self, description: str, advance: int = 0) -> None:
                    """Update the operation description and advance the progress"""
                    if self.task_id is not None:
                        self.update(self.task_id, description=description, advance=advance)
                    else:
                        self.task_id = self.add_task(description, total=self.total_steps)
            
            self.progress_tracker = DetailedProgress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}"),
                BarColumn(complete_style="magenta"),
                TextColumn("[progress.percentage]{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                refresh_per_second=4
            )
            
            self.progress_tracker.verbose = config.get('verbose', False)
            self.progress_tracker.total_steps = 100  # Default value
            
        except ImportError:
            class MinimalProgressTracker:
                def __init__(self):
                    self.tasks = {}
                    self.verbose = config.get('verbose', False)
                    self.total_steps = 100  # Default value
                    
                def add_task(self, description, total=100):
                    task_id = description
                    self.tasks[task_id] = {"completed": 0, "total": total}
                    if self.verbose:
                        print(f": {description} " + "━" * 30 + " 0/{total}")
                    return task_id
                    
                def update(self, task_id, advance=1, completed=None, description=None):
                    if task_id in self.tasks:
                        if completed is not None:
                            self.tasks[task_id]["completed"] = completed
                        else:
                            self.tasks[task_id]["completed"] += advance
                        
                        if description:
                            task_id = description
                        
                        if self.verbose:
                            task = self.tasks[task_id]
                            print(f": {task_id} " + "━" * 30 + f" {task['completed']}/{task['total']}")
                            
                def print_verbose(self, message):
                    if self.verbose:
                        print(message)
                
                def set_total_steps(self, total: int) -> None:
                    self.total_steps = total
                    
                def update_operation(self, description: str, advance: int = 0) -> None:
                    if hasattr(self, 'task_id'):
                        self.update(self.task_id, advance=advance, description=description)
                    else:
                        self.task_id = description
                        self.add_task(description, total=self.total_steps)
                        
                def __enter__(self):
                    return self
                    
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            self.progress_tracker = MinimalProgressTracker()
            
        # Connect the progress tracker to the presenter
        if hasattr(self.presenter, 'set_progress_tracker'):
            self.presenter.set_progress_tracker(self.progress_tracker)
        
        # Initialize request manager
        self.request_manager = RequestManager(
            target_url=target_url,
            timeout=config.get('timeout', 10),
            delay_range=(config.get('min_delay', 0.5), config.get('max_delay', 2.0)),
            max_retries=config.get('max_retries', 3),
            stealth_mode=config.get('stealth', False),
            user_agent=config.get('user_agent')
        )
        
        # Get frameworks filter (if any)
        frameworks_filter = None
        if 'frameworks' in config and config['frameworks']:
            if isinstance(config['frameworks'], str):
                frameworks_filter = [fw.strip().lower() for fw in config['frameworks'].split(',')]
            elif isinstance(config['frameworks'], list):
                frameworks_filter = [fw.strip().lower() for fw in config['frameworks']]
            
            # Set a higher default minimum confidence when filtering by framework
            if 'min_confidence' not in config or config['min_confidence'] == 0:
                config['min_confidence'] = 30  # Default to 30% when filtering
        
        # Initialize result manager
        self.result_manager = ResultManager(target_url)
        if frameworks_filter:
            self.result_manager.set_frameworks_filter(frameworks_filter)
        
        # Initialize engines
        self._init_engines()

        # Initialize detectors
        self._init_detectors()
        
    def _init_engines(self) -> None:
        """Initialize detection engines"""
        # Import engines here to avoid circular imports
        from ..engines.passive import PassiveEngine
        from ..engines.header import HeaderEngine
        from ..engines.content import ContentEngine
        from ..engines.error import ErrorEngine
        from ..engines.static import StaticResourceEngine
        from ..engines.vulnerability import VulnerabilityEngine
        
        self.engines = [
            PassiveEngine(self.request_manager, self.result_manager),
            HeaderEngine(self.request_manager, self.result_manager),
            ContentEngine(self.request_manager, self.result_manager),
            ErrorEngine(self.request_manager, self.result_manager),
            StaticResourceEngine(self.request_manager, self.result_manager),
            VulnerabilityEngine(self.request_manager, self.result_manager)
        ]
        
    def _init_detectors(self) -> None:
        """Initialize framework detectors"""

        # Import detectors here to avoid circular imports
        from ..detectors.django import DjangoDetector
        from ..detectors.flask import FlaskDetector
        from ..detectors.fastapi import FastAPIDetector
        from ..detectors.pyramid import PyramidDetector
        from ..detectors.bottle import BottleDetector
        from ..detectors.web2py import Web2pyDetector
        from ..detectors.sanic import SanicDetector
        from ..detectors.tornado import TornadoDetector
        from ..detectors.starlette import StarletteDetector
        from ..detectors.cherrypy import CherryPyDetector

        
        # Add detectors based on filter or add all
        detector_classes = {
            'django': DjangoDetector,
            'flask': FlaskDetector,
            'fastapi': FastAPIDetector,
            'pyramid': PyramidDetector,
            'bottle': BottleDetector,
            'web2py': Web2pyDetector,
            'sanic': SanicDetector,
            'tornado': TornadoDetector,
            'starlette': StarletteDetector,
            'cherrypy': CherryPyDetector
        }

        frameworks_filter = self.config.get('frameworks')
        if frameworks_filter:
            frameworks_filter = [fw.strip().lower() for fw in frameworks_filter.split(',')]
        else:
            frameworks_filter = None
        
        for framework_name, detector_class in detector_classes.items():
            # If we have a filter and this framework is not in it, skip
            if frameworks_filter and framework_name not in frameworks_filter:
                continue
                
            # Print verbose message if verbose mode is enabled
            if self.progress_tracker and hasattr(self.progress_tracker, 'print_verbose'):
                self.progress_tracker.print_verbose(f"[[*]] Adding detector for {framework_name}")
                
            # Add the detector
            self.detectors.append(detector_class(self.request_manager, self.result_manager))

    def _reset_for_target(self, target_url: str) -> None:
        """
        Reset the detector for a new target
        
        Args:
            target_url: New target URL
        """
        if not target_url:
            raise ValueError("Target URL cannot be None")
            
        # Get frameworkss filter (if any)
        frameworks_filter = None
        if 'frameworks' in self.config and self.config['frameworks']:
            if isinstance(self.config['frameworks'], str):
                frameworks_filter = [fw.strip().lower() for fw in self.config['frameworks'].split(',')]
            elif isinstance(self.config['frameworks'], list):
                frameworks_filter = [fw.strip().lower() for fw in self.config['frameworks']]
            
        # Initialize new request manager
        self.request_manager = RequestManager(
            target_url=target_url,
            timeout=self.config.get('timeout', 10),
            delay_range=(self.config.get('min_delay', 0.5), self.config.get('max_delay', 2.0)),
            max_retries=self.config.get('max_retries', 3),
            stealth_mode=self.config.get('stealth', False),
            user_agent=self.config.get('user_agent')
        )
        
        # Initialize new result manager with frameworks filter,
        self.result_manager = ResultManager(target_url)
        if frameworks_filter:
            self.result_manager.set_frameworks_filter(frameworks_filter)
        
        # Re-initialize engines with the new managers
        for engine in self.engines:
            engine.request_manager = self.request_manager
            engine.result_manager = self.result_manager
            
        # Re-initialize detectors with the new managers
        for detector in self.detectors:
            detector.request_manager = self.request_manager
            detector.result_manager = self.result_manager
        
    def run(self, args=None) -> Dict[str, Any]:
        """
        Main entry point for framework detection
        
        Args:
            args: Not used in Vimana integration, kept for backward compatibility
        
        Returns:
            Dictionary with detection results
        """
        if not self.request_manager or not self.result_manager:
            if self.config:
                target_url = self.config.get('target_url')
                if not target_url:
                    target_url = self.config.get('target_dir')
                if not target_url:
                    target_url = self.config.get('single_target')
                
                if target_url:
                    self.configure(self.config)
                else:
                    raise ValueError("FRAMEWALK has not been configured with a valid target.")
            else:
                raise ValueError("FRAMEWALK has not been configured.")
                
        start_time = time.time()
        
        # Calculate global timeout: (timeout + retry_delay) * max_retries * estimated_requests
        # Estimated requests: 6 engines + 9 detectors = ~15 components, each making ~2-3 requests
        estimated_requests = 45  # Conservative estimate
        timeout_per_request = self.config.get('timeout', 10)
        max_retries = self.config.get('max_retries', 3)
        retry_delay = min(0.5, timeout_per_request / 2)
        
        # Global timeout: (timeout + retry_delay) * (max_retries + 1) * estimated_requests
        global_timeout = (timeout_per_request + retry_delay) * (max_retries + 1) * estimated_requests
        
        # Add a reasonable cap to prevent extremely long scans
        global_timeout = min(global_timeout, 300)  # Max 5 minutes
        
        summary_only = self.config.get('summary_only', False)
        verbose_mode = self.config.get('verbose', False)
        
        if not summary_only and hasattr(self.presenter, 'print_status'):
            self.presenter.print_status(f"Starting analysis of {self.request_manager.target_url}")
            if verbose_mode:
                self.presenter.print_status(f"Global timeout set to {global_timeout:.1f} seconds")
        
        # Early connectivity check
        if not summary_only and hasattr(self.presenter, 'print_status'):
            self.presenter.print_status("  Performing connectivity check...")
        
        connectivity_response = self.request_manager.make_request()
        if not connectivity_response:
            if not summary_only and hasattr(self.presenter, 'print_status'):
                self.presenter.print_status("  Target is unreachable, stopping scan")
            
            # Return early with minimal results
            elapsed = time.time() - start_time
            results = {
                'target_url': self.request_manager.target_url,
                'scan_time': elapsed,
                'frameworks': [],
                'security_headers': [],
                'server_info': {},
                'error': 'Target is unreachable'
            }
            
            # Register the scan in the database
            self._record_scan(results, elapsed)
            
            if not summary_only:
                self.presenter.print_results(results)
            
            return results
        
        if not summary_only and hasattr(self.presenter, 'print_status'):
            self.presenter.print_status("  Target is reachable, proceeding with analysis...")
        
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
            
            if verbose_mode:
                for engine in self.engines:
                    engine_name = engine.__class__.__name__
                    if not summary_only and hasattr(self.presenter, 'print_status'):
                        self.presenter.print_status(f"  Running {engine_name}")
                    
                    # Check global timeout before each engine
                    if time.time() - start_time > global_timeout:
                        if not summary_only and hasattr(self.presenter, 'print_status'):
                            self.presenter.print_status(f"  Global timeout reached, stopping scan")
                        break
                        
                    engine.analyze()
                
                for detector in self.detectors:
                    detector_name = detector.__class__.__name__
                    if not summary_only and hasattr(self.presenter, 'print_status'):
                        self.presenter.print_status(f"  Running {detector_name}")
                    
                    # Check global timeout before each detector
                    if time.time() - start_time > global_timeout:
                        if not summary_only and hasattr(self.presenter, 'print_status'):
                            self.presenter.print_status(f"  Global timeout reached, stopping scan")
                        break
                        
                    detector.detect()
            else:
                progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[cyan]{task.description}"),
                    BarColumn(complete_style="green"),
                    TextColumn("[progress.percentage]{task.completed}/{task.total}"),
                    TimeElapsedColumn(),
                    refresh_per_second=4
                )
                
                with progress:
                    engine_task = progress.add_task(f"Running engines", total=len(self.engines))
                    
                    for i, engine in enumerate(self.engines):
                        # Check global timeout
                        if time.time() - start_time > global_timeout:
                            progress.update(engine_task, description="Global timeout reached")
                            break
                            
                        engine_name = engine.__class__.__name__
                        progress.update(engine_task, description=f"Running engine: {engine_name}")
                        engine.analyze()
                        progress.update(engine_task, advance=1)
                    
                    progress.update(engine_task, description="Running engines")
                    
                    detector_task = progress.add_task(f"Running detectors", total=len(self.detectors))
                    
                    for i, detector in enumerate(self.detectors):
                        # Check global timeout
                        if time.time() - start_time > global_timeout:
                            progress.update(detector_task, description="Global timeout reached")
                            break
                            
                        detector_name = detector.__class__.__name__
                        framework_name = detector.FRAMEWORK if hasattr(detector, 'FRAMEWORK') else "Unknown"
                        progress.update(detector_task, description=f"Running {framework_name}Detector")
                        detector.detect()
                        progress.update(detector_task, advance=1)
                    
                    progress.update(detector_task, description="Running detectors")
        
        except ImportError:
            for i, engine in enumerate(self.engines, 1):
                # Check global timeout
                if time.time() - start_time > global_timeout:
                    if not summary_only:
                        print("Global timeout reached, stopping scan")
                    break
                    
                engine_name = engine.__class__.__name__
                if not summary_only:
                    print(f"Running engine: {engine_name} ({i}/{len(self.engines)})")
                engine.analyze()
            
            for i, detector in enumerate(self.detectors, 1):
                # Check global timeout
                if time.time() - start_time > global_timeout:
                    if not summary_only:
                        print("Global timeout reached, stopping scan")
                    break
                    
                print(detector)
                detector_name = detector.__class__.__name__
                framework_name = detector.FRAMEWORK if hasattr(detector, 'FRAMEWORK') else "Unknown"
                if not summary_only:
                    print(f"Running detector: {framework_name} ({i}/{len(self.detectors)})")
                detector.detect()

        self.result_manager.mark_complete()
        
        # Get the final results using the minimum confidence threshold
        elapsed = time.time() - start_time
        min_confidence = self.config.get('min_confidence', 0)
        results = self.result_manager.get_results(min_confidence)
        results['scan_time'] = elapsed
        
        # Register the scan in the database
        self._record_scan(results, elapsed)
        
        if not summary_only:
            self.presenter.print_results(results)
        
        if self.config and self.config.get('output'):
            self.save_results(self.config['output'])
        
        return results
        
    def get_json_results(self) -> str:
        """
        Get the results in JSON format
        
        Returns:
            JSON string of detection results
        """
        min_confidence = self.config.get('min_confidence', 0)
        results = self.result_manager.get_results(min_confidence)
        return self.json_formatter.format(results)
        
    def save_results(self, output_file: str, format: str = "json") -> None:
        """
        Save results to a file
        
        Args:
            output_file: Path to output file
            format: Output format (currently only 'json' is supported)
        """
        if format.lower() != "json":
            raise ValueError(f"Unsupported output format: {format}")
            
        min_confidence = self.config.get('min_confidence', 0)
        results = self.result_manager.get_results(min_confidence)
        self.json_formatter.save(results, output_file)
        
        # Use the presenter instead of progress_tracker for verbose output
        if self.presenter and self.config.get('verbose', False) and hasattr(self.presenter, 'print_status'):
            self.presenter.print_status(f"Results saved to {output_file}")
    
    def _record_scan(self, results: Dict[str, Any], elapsed_time: float) -> None:
        """
        Record the scan in the database
        
        Args:
            results: Scan results
            elapsed_time: Time taken for the scan
        """
        try:
            import jsonpickle
            import yaml
            import os
            from datetime import datetime
            from core._dbops_.vmnf_dbops import VFDBOps
            import uuid

            scan_file = f'{self.scan_id}.yaml'
            scan_output_path = f"{self.abs_cache_path}/{self.scan_id}"
            scan_output_file = f"{scan_output_path}/{scan_file}"
            scan_template = VFDBOps(**self.config).get_model_dict("_SCANS_")
            
            # Prepare scan scope
            scope = {
                'urls': [self.request_manager.target_url],
                'frameworks_filter': self.config.get('frameworks'),
                'min_confidence': self.config.get('min_confidence', 0)
            }
            
            # Get detected frameworks info
            detected_frameworks = results.get('frameworks', [])
            top_framework = "Unknown"
            top_framework_version = "Unknown"
            total_frameworks = len(detected_frameworks)
            total_components = 0
            
            if detected_frameworks:
                # Get the framework with highest confidence
                top_framework_data = max(detected_frameworks, key=lambda x: x.get('confidence', 0))
                top_framework = top_framework_data.get('name', 'Unknown')
                top_framework_version = top_framework_data.get('version', 'Unknown')
                
                # Count total components
                for fw in detected_frameworks:
                    total_components += len(fw.get('components', []))
            
            # Check if scan has findings (frameworks detected)
            has_issues = total_frameworks > 0
            
            # Get scan template
            scan_template = VFDBOps(**self.config).get_model_dict("_SCANS_")
            
            # Update scan template with framewalk-specific data
            scan_template.update({
                'scan_id': self.scan_id,
                'scan_type': 'DAST',
                'scan_date': self.scan_time,
                'scan_hash': self.scan_hash,
                'scan_target': self.request_manager.target_url,
                'scan_target_full_path': 'N.A',
                'scan_cache_dir': scan_output_path,  # Framewalk doesn't use cache files like d4m8
                'scan_output_file': scan_output_file,
                'project_framework': top_framework,
                'project_framework_version': top_framework_version,
                'project_framework_total_cves': 0,  # Framewalk doesn't check CVEs
                'project_total_requirements': 'N.A',
                'project_total_view_modules': 'N.A',
                'scan_scope': jsonpickle.encode(scope),
                'scan_plugin': 'framewalk',
                'vmnf_handler': jsonpickle.encode(self.config),
                'has_issues': has_issues
            })
            
            # Register the scan
            VFDBOps(**scan_template).register('_SCANS_')
            
            # Log scan registration if verbose
            if self.config.get('verbose', False) and self.presenter and hasattr(self.presenter, 'print_status'):
                self.presenter.print_status(f"Scan registered in database with ID: {self.scan_id}")
                
        except Exception as e:
            # Don't fail the scan if database registration fails
            if self.config.get('verbose', False):
                print(f"Warning: Failed to register scan in database: {str(e)}", file=sys.stderr)