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
        
        self.engines = [
            PassiveEngine(self.request_manager, self.result_manager),
            HeaderEngine(self.request_manager, self.result_manager),
            ContentEngine(self.request_manager, self.result_manager),
            ErrorEngine(self.request_manager, self.result_manager),
            StaticResourceEngine(self.request_manager, self.result_manager)
        ]
        
    def _init_detectors(self) -> None:
        """Initialize framework detectors"""
        # Import detectors here to avoid circular imports
        from ..detectors.django import DjangoDetector
        from ..detectors.flask import FlaskDetector
        from ..detectors.fastapi import FastAPIDetector
        from ..detectors.pyramid import PyramidDetector
        from ..detectors.bottle import BottleDetector
        
        # Clear any existing detectors
        self.detectors = []
        
        # Check if we have a frameworks filter
        frameworks_filter = None
        if self.config and 'frameworks' in self.config and self.config['frameworks']:
            if isinstance(self.config['frameworks'], str):
                frameworks_filter = [fw.strip().lower() for fw in self.config['frameworks'].split(',')]
            elif isinstance(self.config['frameworks'], list):
                frameworks_filter = [fw.strip().lower() for fw in self.config['frameworks']]
        
        # Add detectors based on filter or add all
        detector_classes = {
            'django': DjangoDetector,
            'flask': FlaskDetector,
            'fastapi': FastAPIDetector,
            'pyramid': PyramidDetector,
            'bottle': BottleDetector
        }
        
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
        
        summary_only = self.config.get('summary_only', False)
        verbose_mode = self.config.get('verbose', False)
        
        if not summary_only and hasattr(self.presenter, 'print_status'):
            self.presenter.print_status(f"Starting analysis of {self.request_manager.target_url}")
        
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
            
            if verbose_mode:
                for engine in self.engines:
                    engine_name = engine.__class__.__name__
                    if not summary_only and hasattr(self.presenter, 'print_status'):
                        self.presenter.print_status(f"  Running {engine_name}")
                    engine.analyze()
                
                for detector in self.detectors:
                    detector_name = detector.__class__.__name__
                    if not summary_only and hasattr(self.presenter, 'print_status'):
                        self.presenter.print_status(f"  Running {detector_name}")
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
                        engine_name = engine.__class__.__name__
                        progress.update(engine_task, description=f"Running engine: {engine_name}")
                        engine.analyze()
                        progress.update(engine_task, advance=1)
                    
                    progress.update(engine_task, description="Running engines")
                    
                    detector_task = progress.add_task(f"Running detectors", total=len(self.detectors))
                    
                    for i, detector in enumerate(self.detectors):
                        detector_name = detector.__class__.__name__
                        framework_name = detector.FRAMEWORK if hasattr(detector, 'FRAMEWORK') else "Unknown"
                        progress.update(detector_task, description=f"Running {framework_name}Detector")
                        detector.detect()
                        progress.update(detector_task, advance=1)
                    
                    progress.update(detector_task, description="Running detectors")
        
        except ImportError:
            for i, engine in enumerate(self.engines, 1):
                engine_name = engine.__class__.__name__
                if not summary_only:
                    print(f"Running engine: {engine_name} ({i}/{len(self.engines)})")
                engine.analyze()
            
            for i, detector in enumerate(self.detectors, 1):
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