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

import time
import threading
import sys
from typing import List, Dict, Any, Optional

# Try to import rich for enhanced progress display
try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.panel import Panel
    from rich.console import Console
    from rich.status import Status
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class ProgressTracker:
    """Tracks and displays progress during framework detection with clean verbose output"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the progress tracker
        
        Args:
            verbose: Whether to show detailed progress
        """
        self.verbose = verbose
        self.use_rich = HAS_RICH
        self.current_operation = "Initializing"
        self.current_step = 0
        self.total_steps = 100  # Default value
        self.step_start_time = time.time()
        self.operation_start_time = time.time()
        self.operations_history = []
        self.slow_operations = []
        self.active = False
        self.thread = None
        self.paused = False
        
        # Setup rich components if available
        if self.use_rich:
            self.console = Console()
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[bold]{task.completed}/{task.total}"),
                TimeElapsedColumn(),
                console=self.console
            )
            self.task_id = None
            self.status = None  # For verbose output
        
    def set_total_steps(self, total: int) -> None:
        """
        Set the total number of steps for progress tracking
        
        Args:
            total: Total number of steps
        """
        self.total_steps = max(1, total)  # Ensure at least 1 step
        if self.use_rich and self.task_id is not None:
            self.progress.update(self.task_id, total=self.total_steps)
            
    def update_operation(self, operation: str, steps: int = 1) -> None:
        """
        Update the current operation and increment completed steps
        
        Args:
            operation: Operation description
            steps: Number of steps to add to the progress counter
        """
        # Record previous operation time
        operation_time = time.time() - self.step_start_time
        if operation_time > 3.0:  # Operations taking more than 3 seconds are considered slow
            self.slow_operations.append((self.current_operation, operation_time))
            
        # Update operation info
        prev_operation = self.current_operation
        self.operations_history.append((prev_operation, operation_time))
        self.current_operation = operation
        
        # Increment step counter
        self.current_step += steps
        if self.current_step > self.total_steps:
            self.current_step = self.total_steps
            
        self.step_start_time = time.time()
        
        # Update progress display
        if self.use_rich and self.task_id is not None:
            self.progress.update(self.task_id, 
                               description=operation, 
                               completed=self.current_step)
        
    def start(self) -> None:
        """Start progress tracking"""
        self.active = True
        self.operation_start_time = time.time()
        self.step_start_time = time.time()
        self.current_step = 0  # Reset step counter on start
        
        if self.use_rich:
            # Create a task for tracking
            self.progress.start()
            self.task_id = self.progress.add_task(
                "Starting...", 
                total=self.total_steps,
                completed=0
            )
        else:
            # Start progress display thread if not using rich
            self.thread = threading.Thread(target=self._display_progress_loop)
            self.thread.daemon = True
            self.thread.start()
            
    def stop(self) -> None:
        """Stop progress tracking"""
        self.active = False
        
        # Update to 100% completion
        if self.use_rich and self.task_id is not None:
            self.progress.update(self.task_id, completed=self.total_steps)
            self.progress.stop()
            
        # Thread will terminate itself when active=False
    
    def pause(self) -> None:
        """Temporarily pause progress display for verbose output"""
        self.paused = True
        
        if self.use_rich:
            # Rich doesn't need explicit pausing, it handles it automatically
            pass
        else:
            # Clear the current progress line
            sys.stdout.write("\033[K\n")
            sys.stdout.flush()
            
    def resume(self) -> None:
        """Resume progress display after verbose output"""
        self.paused = False
            
    def print_verbose(self, message: str) -> None:
        """
        Print a verbose message while properly handling the progress display
        
        Args:
            message: Message to print
        """
        if not self.verbose:
            return
            
        if self.use_rich:
            # Rich handles this automatically
            self.console.print(message)
        else:
            # For non-rich output, pause display, print message, and resume
            self.pause()
            print(message)
            self.resume()
            
    def _display_progress_loop(self) -> None:
        """Loop to display progress in non-rich mode"""
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        spinner_idx = 0
        
        while self.active:
            if self.total_steps > 0 and not self.paused:
                percent = min(100, int(self.current_step / self.total_steps * 100))
                elapsed = time.time() - self.operation_start_time
                
                # Create progress display
                spinner = spinner_chars[spinner_idx]
                progress_str = f"\r{spinner} {self.current_operation} - {percent}% completed ({self.current_step}/{self.total_steps}) - {elapsed:.1f}s elapsed"
                
                # Clear line and print progress
                sys.stdout.write("\033[K")  # Clear line
                sys.stdout.write(progress_str)
                sys.stdout.flush()
                
                spinner_idx = (spinner_idx + 1) % len(spinner_chars)
                
            time.sleep(0.1)
            
        # Clear line when done
        sys.stdout.write("\033[K")
        sys.stdout.flush()
        
    def get_slow_operations(self) -> List[tuple]:
        """
        Get list of slow operations
        
        Returns:
            List of (operation_name, time_taken) tuples
        """
        return self.slow_operations
        
    def get_operation_history(self) -> List[tuple]:
        """
        Get complete operation history
        
        Returns:
            List of (operation_name, time_taken) tuples
        """
        return self.operations_history