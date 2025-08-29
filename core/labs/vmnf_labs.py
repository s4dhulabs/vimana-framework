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

import os
import sys
import subprocess
import time
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import requests

from neotermcolor import cprint, colored as cl
from .._dbops_.vmnf_dbops import VFDBOps
from ..vmnf_smng import VFManager


class VimanaLabManager:
    """
    Vimana Lab Management System
    
    Manages plugin labs using Docker Compose for isolated testing environments.
    Each lab is a Docker containerized environment that provides a vulnerable
    application for testing the corresponding Vimana plugin.
    """
    
    def __init__(self, **handler):
        self.handler = handler
        self.vimana_root = self._get_vimana_root()
        self.labs_root = os.path.join(self.vimana_root, "siddhis")
        self.active_labs = {}
        
        # Lab configuration
        self.required_files = [
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        # Default lab ports (can be overridden in docker-compose.yml)
        self.default_ports = {
            "w2pyscanner": 8086,
            "django_scanner": 8000,
            "flask_scanner": 5000,
            "fastapi_scanner": 8000
        }
        
        # Lab status tracking
        self.lab_status_file = os.path.join(self.vimana_root, ".vimana_labs_status.json")
        self._load_lab_status()

    def _get_vimana_root(self) -> str:
        """Get the Vimana framework root directory."""
        # Try to get from VIMANA_PATH environment variable first
        vimana_path = os.getenv("VIMANA_PATH")
        if vimana_path and os.path.exists(vimana_path):
            return vimana_path
        
        # Fallback: try to get from VIMANA_HOME/repo
        vimana_home = os.getenv("VIMANA_HOME")
        if vimana_home:
            repo_path = os.path.join(vimana_home, "repo")
            if os.path.exists(repo_path):
                return repo_path
        
        # Fallback to current working directory
        current_dir = os.getcwd()
        if os.path.exists(os.path.join(current_dir, "core", "vmnf_engine.py")):
            return current_dir
        
        # If we're in a subdirectory, try to find the root
        for root, dirs, files in os.walk(current_dir):
            if "vmnf_engine.py" in files:
                # Return the parent directory of the core directory
                return os.path.dirname(root)
        
        # Legacy fallback: try old vimana_path variable
        legacy_path = os.getenv("vimana_path")
        if legacy_path and os.path.exists(legacy_path):
            return legacy_path
        
        raise FileNotFoundError("Could not find Vimana framework root directory")

    def _load_lab_status(self) -> None:
        """Load lab status from file."""
        try:
            if os.path.exists(self.lab_status_file):
                with open(self.lab_status_file, 'r') as f:
                    self.active_labs = json.load(f)
        except Exception:
            self.active_labs = {}

    def _save_lab_status(self) -> None:
        """Save lab status to file."""
        try:
            with open(self.lab_status_file, 'w') as f:
                json.dump(self.active_labs, f, indent=2)
        except Exception as e:
            cprint(f"Warning: Could not save lab status: {e}", 'yellow')

    def _check_plugin_exists(self, plugin_name: str) -> bool:
        """Check if a plugin exists in the Vimana database."""
        try:
            # Use VFManager to check if plugin exists
            vf_manager = VFManager(module=plugin_name)
            siddhi = vf_manager.get_siddhi()
            return siddhi is not None
        except Exception:
            return False

    def _get_plugin_lab_path(self, plugin_name: str) -> str:
        """Get the lab directory path for a plugin."""
        return os.path.join(self.labs_root, plugin_name, "lab")

    def _validate_lab_structure(self, plugin_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that a plugin has a proper lab structure.
        
        Returns:
            Tuple of (is_valid, list_of_missing_files)
        """
        lab_path = self._get_plugin_lab_path(plugin_name)
        missing_files = []
        
        if not os.path.exists(lab_path):
            return False, ["lab directory"]
        
        for required_file in self.required_files:
            file_path = os.path.join(lab_path, required_file)
            if not os.path.exists(file_path):
                missing_files.append(required_file)
        
        return len(missing_files) == 0, missing_files

    def _check_docker_requirements(self) -> Tuple[bool, List[str]]:
        """
        Check if Docker and Docker Compose are available.
        
        Returns:
            Tuple of (all_available, list_of_missing_tools)
        """
        missing_tools = []
        
        # Check Docker
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                missing_tools.append("docker")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_tools.append("docker")
        
        # Check Docker Compose
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                missing_tools.append("docker-compose")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_tools.append("docker-compose")
        
        return len(missing_tools) == 0, missing_tools

    def _get_lab_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get lab configuration from docker-compose.yml."""
        lab_path = self._get_plugin_lab_path(plugin_name)
        compose_file = os.path.join(lab_path, "docker-compose.yml")
        
        try:
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            cprint(f"Warning: Could not read docker-compose.yml: {e}", 'yellow')
            return {}

    def _get_lab_port(self, plugin_name: str) -> int:
        """Get the port for a lab from its docker-compose configuration."""
        config = self._get_lab_config(plugin_name)
        
        # Try to extract port from docker-compose.yml
        try:
            services = config.get('services', {})
            for service_name, service_config in services.items():
                ports = service_config.get('ports', [])
                for port_mapping in ports:
                    if isinstance(port_mapping, str) and ':' in port_mapping:
                        host_port = port_mapping.split(':')[0]
                        return int(host_port)
        except Exception:
            pass
        
        # Fallback to default ports
        return self.default_ports.get(plugin_name, 8080)

    def _run_docker_compose(self, plugin_name: str, command: str, 
                           capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run docker-compose command for a specific lab."""
        lab_path = self._get_plugin_lab_path(plugin_name)
        
        if not os.path.exists(lab_path):
            raise FileNotFoundError(f"Lab directory not found: {lab_path}")
        
        # Change to lab directory and run command
        original_cwd = os.getcwd()
        try:
            os.chdir(lab_path)
            
            # Build the docker-compose command
            cmd = ['docker-compose'] + command.split()
            
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            else:
                result = subprocess.run(cmd, timeout=60)
            
            return result
            
        finally:
            os.chdir(original_cwd)

    def _wait_for_service(self, plugin_name: str, timeout: int = 60) -> bool:
        """Wait for lab service to be ready."""
        port = self._get_lab_port(plugin_name)
        url = f"http://localhost:{port}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:  # Any response < 500 means service is up
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(2)
        
        return False

    def _check_lab_health(self, plugin_name: str) -> bool:
        """Check if a lab is running and healthy."""
        port = self._get_lab_port(plugin_name)
        url = f"http://localhost:{port}"
        
        try:
            response = requests.get(url, timeout=10)
            return response.status_code < 500
        except requests.RequestException:
            return False

    def start_lab(self, plugin_name: str) -> bool:
        """
        Start a lab for the specified plugin.
        
        Args:
            plugin_name: Name of the plugin to start lab for
            
        Returns:
            True if lab started successfully, False otherwise
        """
        try:
            # Step 1: Validate plugin exists
            if not self._check_plugin_exists(plugin_name):
                cprint(f"❌ Plugin '{plugin_name}' not found in Vimana database", 'red')
                cprint(f"   Run 'vimana load --plugins' to load plugins", 'cyan')
                return False
            
            # Step 2: Validate lab structure
            is_valid, missing_files = self._validate_lab_structure(plugin_name)
            if not is_valid:
                cprint(f"❌ Lab structure invalid for plugin '{plugin_name}'", 'red')
                cprint(f"   Missing files: {', '.join(missing_files)}", 'yellow')
                return False
            
            # Step 3: Check Docker requirements
            docker_ok, missing_tools = self._check_docker_requirements()
            if not docker_ok:
                cprint(f"❌ Docker requirements not met", 'red')
                cprint(f"   Missing tools: {', '.join(missing_tools)}", 'yellow')
                cprint(f"   Please install Docker and Docker Compose", 'cyan')
                return False
            
            # Step 4: Check if lab is already running
            if self._check_lab_health(plugin_name):
                cprint(f"⚠️  Lab for '{plugin_name}' is already running", 'yellow')
                self._show_lab_info(plugin_name)
                return True
            
            # Step 5: Start the lab
            cprint(f"🚀 Starting lab for plugin '{plugin_name}'...", 'cyan')
            
            # Run docker-compose up
            result = self._run_docker_compose(plugin_name, "up --build -d")
            if result.returncode != 0:
                cprint(f"❌ Failed to start lab: {result.stderr}", 'red')
                return False
            
            # Step 6: Wait for service to be ready
            cprint(f"⏳ Waiting for lab service to be ready...", 'cyan')
            if not self._wait_for_service(plugin_name):
                cprint(f"❌ Lab service failed to start within timeout", 'red')
                return False
            
            # Step 7: Update status and show info
            port = self._get_lab_port(plugin_name)
            self.active_labs[plugin_name] = {
                "status": "running",
                "port": port,
                "started_at": time.time(),
                "url": f"http://localhost:{port}"
            }
            self._save_lab_status()
            
            cprint(f"✅ Lab for '{plugin_name}' started successfully!", 'green')
            self._show_lab_info(plugin_name)
            
            return True
            
        except Exception as e:
            cprint(f"❌ Error starting lab: {str(e)}", 'red')
            return False

    def stop_lab(self, plugin_name: str) -> bool:
        """
        Stop a running lab.
        
        Args:
            plugin_name: Name of the plugin to stop lab for
            
        Returns:
            True if lab stopped successfully, False otherwise
        """
        try:
            # Check if lab is running
            if not self._check_lab_health(plugin_name):
                cprint(f"⚠️  Lab for '{plugin_name}' is not running", 'yellow')
                return True
            
            cprint(f"🛑 Stopping lab for plugin '{plugin_name}'...", 'cyan')
            
            # Run docker-compose down
            result = self._run_docker_compose(plugin_name, "down")
            if result.returncode != 0:
                cprint(f"❌ Failed to stop lab: {result.stderr}", 'red')
                return False
            
            # Update status
            if plugin_name in self.active_labs:
                del self.active_labs[plugin_name]
                self._save_lab_status()
            
            cprint(f"✅ Lab for '{plugin_name}' stopped successfully!", 'green')
            return True
            
        except Exception as e:
            cprint(f"❌ Error stopping lab: {str(e)}", 'red')
            return False

    def status_lab(self, plugin_name: str) -> bool:
        """
        Check status of a lab.
        
        Args:
            plugin_name: Name of the plugin to check lab status for
            
        Returns:
            True if lab is running, False otherwise
        """
        try:
            is_running = self._check_lab_health(plugin_name)
            
            if is_running:
                cprint(f"✅ Lab for '{plugin_name}' is running", 'green')
                self._show_lab_info(plugin_name)
            else:
                cprint(f"❌ Lab for '{plugin_name}' is not running", 'red')
            
            return is_running
            
        except Exception as e:
            cprint(f"❌ Error checking lab status: {str(e)}", 'red')
            return False

    def list_labs(self) -> None:
        """List all available labs and their status."""
        try:
            # Get all plugins from database
            vf_manager = VFManager()
            plugins = vf_manager.query_siddhis()
            
            if not plugins:
                cprint("❌ No plugins found in database", 'red')
                cprint("   Run 'vimana load --plugins' to load plugins", 'cyan')
                return
            
            cprint("\n📋 Available Labs:", 'cyan')
            cprint("─" * 80)
            
            labs_found = False
            for plugin in plugins:
                plugin_name = plugin.name
                lab_path = self._get_plugin_lab_path(plugin_name)
                
                if os.path.exists(lab_path):
                    labs_found = True
                    is_valid, missing_files = self._validate_lab_structure(plugin_name)
                    is_running = self._check_lab_health(plugin_name)
                    
                    # Status indicator
                    if is_running:
                        status = cl("🟢 RUNNING", 'green')
                    elif is_valid:
                        status = cl("⚪ READY", 'white')
                    else:
                        status = cl("🔴 INVALID", 'red')
                    
                    # Plugin info
                    print(f"  {cl(plugin_name, 'cyan'):<20} {status}")
                    
                    if is_valid:
                        port = self._get_lab_port(plugin_name)
                        print(f"    📍 Port: {port}")
                        print(f"    🌐 URL: http://localhost:{port}")
                        
                        if is_running:
                            print(f"    🎯 Test Command: vimana run {plugin_name} --target-url http://localhost:{port}")
                    
                    if not is_valid:
                        print(f"    ❌ Missing: {', '.join(missing_files)}")
                    
                    print()
            
            if not labs_found:
                cprint("❌ No labs found", 'red')
                cprint("   Labs should be in siddhis/<plugin_name>/lab/ directories", 'cyan')
            
        except Exception as e:
            cprint(f"❌ Error listing labs: {str(e)}", 'red')

    def _show_lab_info(self, plugin_name: str) -> None:
        """Show detailed information about a running lab."""
        try:
            port = self._get_lab_port(plugin_name)
            url = f"http://localhost:{port}"
            
            print(f"\n🌐 Lab Information:")
            print(f"   📍 Port: {port}")
            print(f"   🌐 URL: {url}")
            print(f"   🎯 Test Command: vimana run {plugin_name} --target-url {url}")
            
            # Show lab-specific information if available
            lab_path = self._get_plugin_lab_path(plugin_name)
            readme_file = os.path.join(lab_path, "README.md")
            
            if os.path.exists(readme_file):
                print(f"   📖 Documentation: {readme_file}")
            
            # Show docker-compose services if available
            config = self._get_lab_config(plugin_name)
            services = config.get('services', {})
            if services:
                print(f"   🐳 Services: {', '.join(services.keys())}")
            
            print()
            
        except Exception as e:
            cprint(f"Warning: Could not show lab info: {e}", 'yellow')

    def cleanup_labs(self) -> None:
        """Stop all running labs and clean up."""
        try:
            if not self.active_labs:
                cprint("ℹ️  No active labs to clean up", 'cyan')
                return
            
            cprint("🧹 Cleaning up all labs...", 'cyan')
            
            for plugin_name in list(self.active_labs.keys()):
                self.stop_lab(plugin_name)
            
            # Remove status file
            if os.path.exists(self.lab_status_file):
                os.remove(self.lab_status_file)
            
            cprint("✅ All labs cleaned up successfully!", 'green')
            
        except Exception as e:
            cprint(f"❌ Error during cleanup: {str(e)}", 'red')


def handle_lab_command(handler_ns) -> None:
    """
    Main entry point for lab management commands.
    
    Args:
        handler_ns: Vimana handler namespace with lab parameters
    """
    try:
        # Initialize lab manager
        lab_manager = VimanaLabManager(**vars(handler_ns))
        
        # Get the lab name from handler
        lab_name = handler_ns.run_lab
        
        if not lab_name:
            cprint("❌ No lab specified", 'red')
            cprint("   Usage: vimana run --lab <plugin_name>", 'cyan')
            return
        
        # Handle different lab operations
        if hasattr(handler_ns, 'lab_operation'):
            operation = handler_ns.lab_operation
        else:
            operation = "start"  # Default operation
        
        if operation == "start":
            success = lab_manager.start_lab(lab_name)
        elif operation == "stop":
            success = lab_manager.stop_lab(lab_name)
        elif operation == "status":
            success = lab_manager.status_lab(lab_name)
        elif operation == "list":
            lab_manager.list_labs()
            return
        elif operation == "cleanup":
            lab_manager.cleanup_labs()
            return
        else:
            cprint(f"❌ Unknown lab operation: {operation}", 'red')
            cprint("   Available operations: start, stop, status, list, cleanup", 'cyan')
            return
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        cprint(f"❌ Lab management error: {str(e)}", 'red')
        sys.exit(1)

