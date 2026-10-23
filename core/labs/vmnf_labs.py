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
        
        # Multi-service lab configurations (structural — ports still overridable via compose)
        self.multi_service_labs = {
            "framewalk": {
                "web2py-app": {"framework": "Web2py", "port": 8081},
                "sanic-app": {"framework": "Sanic", "port": 8082},
                "tornado-app": {"framework": "Tornado", "port": 8083},
                "starlette-app": {"framework": "Starlette", "port": 8084},
                "cherrypy-app": {"framework": "CherryPy", "port": 8085}
            }
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
    
    def _create_targets_file(self, plugin_name: str) -> str:
        """Create targets.txt file with lab addresses and set VIMANA_LAB_TARGETS."""
        try:
            lab_path = self._get_plugin_lab_path(plugin_name)
            targets_file = os.path.join(lab_path, "targets.txt")
            
            # Get all lab URLs
            services = self._get_lab_services(plugin_name)
            urls = [f"http://localhost:{service['port']}" for service in services.values()]
            
            # Write targets to file (overwrite each time)
            with open(targets_file, 'w') as f:
                for url in urls:
                    f.write(f"{url}\n")
            
            # Set environment variable for current process
            os.environ["VIMANA_LAB_TARGETS"] = targets_file
            
            # Also create an environment file that can be sourced
            env_file = os.path.join(lab_path, ".env")
            with open(env_file, 'w') as f:
                f.write(f"export VIMANA_LAB_TARGETS={targets_file}\n")
            
            return targets_file
            
        except Exception as e:
            cprint(f"Warning: Could not create targets file: {e}", 'yellow')
            return ""

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

        if not os.path.isfile(compose_file):
            # Plugins without a lab — quiet (Control API polls status for every plugin)
            return {}

        try:
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)
            return config or {}
        except Exception as e:
            cprint(f"Warning: Could not read docker-compose.yml: {e}", 'yellow')
            return {}

    def _is_multi_service_lab(self, plugin_name: str) -> bool:
        """Check if this is a multi-service lab."""
        return plugin_name in self.multi_service_labs
    
    def _get_lab_services(self, plugin_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all services for a lab with their configurations."""
        if plugin_name in self.multi_service_labs:
            return self.multi_service_labs[plugin_name]
        
        # For single-service labs, create a single service entry
        port = self._get_lab_port(plugin_name)
        return {
            f"{plugin_name}-service": {
                "framework": plugin_name.capitalize(),
                "port": port
            }
        }
    
    def _get_lab_ports(self, plugin_name: str) -> List[int]:
        """Get all ports for a lab."""
        if plugin_name in self.multi_service_labs:
            return [service["port"] for service in self.multi_service_labs[plugin_name].values()]
        else:
            return [self._get_lab_port(plugin_name)]
    
    def _get_plugin_lab_meta(self, plugin_name: str) -> Dict[str, Any]:
        """Lab metadata from composition.lab / vfset.lab (via capabilities registry)."""
        try:
            from core.capabilities import get_lab_meta
            return get_lab_meta(plugin_name) or {}
        except Exception:
            return {}

    def _format_run_hint(self, plugin_name: str, url: str) -> str:
        """Example run command from composition.lab.run_hint (or a generic fallback)."""
        lab = self._get_plugin_lab_meta(plugin_name)
        hint = lab.get('run_hint') if isinstance(lab, dict) else None
        if not hint:
            hint = "vimana run {plugin} --target-url {url}"
        return str(hint).format(plugin=plugin_name, url=url, port=urlparse(url).port or '')

    def _shared_flag_map(self) -> Dict[str, tuple]:
        """CLI flag → (handler_dest, action) for common shared args used in run_hints."""
        return {
            '--target-url': ('target_url', 'store'),
            '--endpoint-url': ('endpoint_url', 'store'),
            '--endpoint': ('endpoint', 'store'),
            '--file': ('file_scope', 'store'),
            '--json': ('json_output', 'store_true'),
            '--no-channels': ('no_channels', 'store_true'),
            '--ci-mode': ('ci_mode', 'store_true'),
            '--auto': ('auto', 'store_true'),
            '--debug': ('debug', 'store_true'),
            '--verbose': ('verbose', 'store_true'),
            '--scan-api': ('api_scan_enabled', 'store'),
            '--api-scan': ('api_scan_enabled', 'store'),
            '--spec-url': ('openapi_spec_url', 'store'),
            '--spec-file': ('openapi_spec_file', 'store'),
        }

    def _specialty_flag_map(self, plugin_name: str) -> Dict[str, tuple]:
        """CLI flag → (dest, action) from composition.specialty_args."""
        mapping: Dict[str, tuple] = {}
        try:
            from core.capabilities import get_capability
            cap = get_capability(plugin_name) or {}
        except Exception:
            return mapping
        specialty = cap.get('specialty_args') or {}
        for flag in specialty.get('flags') or []:
            dest = flag.get('dest')
            if not dest:
                continue
            action = flag.get('action', 'store')
            for name in flag.get('flags') or []:
                mapping[str(name)] = (dest, action)
        return mapping

    def parse_run_hint_args(self, plugin_name: str, url: str) -> Dict[str, Any]:
        """
        Materialize composition.lab.run_hint into a handler kwargs dict.

        Example hint:
            vimana run boundr --target-url http://localhost:18102 --upload-audit --json --no-channels
        """
        import shlex

        hint = self._format_run_hint(plugin_name, url)
        tokens = shlex.split(hint)
        # Drop leading: vimana run [plugin]
        while tokens and tokens[0] in ('vimana', 'vf', 'run'):
            tokens.pop(0)
        if tokens and tokens[0] == plugin_name:
            tokens.pop(0)

        flag_map = {}
        flag_map.update(self._shared_flag_map())
        flag_map.update(self._specialty_flag_map(plugin_name))

        args: Dict[str, Any] = {
            'target_url': url,
            'json_output': True,
            'no_channels': True,
            'ci_mode': False,
        }

        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in flag_map:
                dest, action = flag_map[tok]
                if action == 'store_true':
                    args[dest] = True
                    i += 1
                elif action == 'store_false':
                    args[dest] = False
                    i += 1
                else:
                    if i + 1 >= len(tokens) or tokens[i + 1].startswith('-'):
                        # nargs='?' style — presence alone
                        args[dest] = True
                        i += 1
                    else:
                        args[dest] = tokens[i + 1]
                        i += 2
            else:
                # Unknown flag: skip flag and optional value
                if tok.startswith('-') and i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                    i += 2
                else:
                    i += 1

        # Always prefer live lab URL for target_url
        args['target_url'] = url
        return args

    def test_lab_plugin(self, plugin_name: str) -> bool:
        """
        Run the plugin against its lab using composition.lab.run_hint.

        Assumes the lab is already up (or start_lab just succeeded).
        """
        try:
            if not self._check_lab_health(plugin_name):
                cprint(f"❌ Lab for '{plugin_name}' is not healthy — cannot --test", 'red')
                return False

            port = self._get_lab_port(plugin_name)
            url = f"http://localhost:{port}"
            hint = self._format_run_hint(plugin_name, url)
            args = self.parse_run_hint_args(plugin_name, url)

            cprint(f"\n🧪 Lab test — running plugin against lab", 'cyan')
            cprint(f"   Hint: {hint}", 'white')
            cprint(f"   URL:  {url}\n", 'white')

            # Prefer leaf orchestrator path (same as Control API) when available
            try:
                from core.api.control.services import run_plugin as control_run_plugin
                record = control_run_plugin(plugin_name, args)
                if record and record.status == 'succeeded':
                    report = record.report or {}
                    summary = report.get('summary') if isinstance(report, dict) else None
                    cprint(f"✅ Lab test finished for '{plugin_name}'", 'green')
                    if summary:
                        cprint(f"   Summary: {summary}", 'cyan')
                    return True
                err = (record.error if record else None) or 'unknown error'
                cprint(f"❌ Lab test failed: {err}", 'red')
                return False
            except Exception:
                # Fallback: classic VFManager.run_siddhi
                from core.vmnf_smng import VFManager

                run_handler = dict(self.handler or {})
                run_handler.update(args)
                run_handler['module_run'] = plugin_name
                run_handler['module'] = plugin_name
                run_handler['plugin_name'] = plugin_name
                run_handler['run_lab'] = False
                run_handler['lab_test'] = False
                run_handler['lab_operation'] = False
                VFManager(**run_handler).run_siddhi()
                cprint(f"✅ Lab test finished for '{plugin_name}'", 'green')
                return True

        except Exception as e:
            cprint(f"❌ Lab test error: {str(e)}", 'red')
            return False

    def _get_lab_port(self, plugin_name: str) -> int:
        """Primary lab port: docker-compose ports → composition.lab.port → error."""
        # For multi-service labs, return the first service port
        if plugin_name in self.multi_service_labs:
            first_service = list(self.multi_service_labs[plugin_name].values())[0]
            return first_service["port"]

        config = self._get_lab_config(plugin_name)

        # Prefer host port from docker-compose.yml
        try:
            services = config.get('services', {})
            for service_name, service_config in services.items():
                ports = service_config.get('ports', [])
                for port_mapping in ports:
                    if isinstance(port_mapping, str) and ':' in port_mapping:
                        host_port = port_mapping.split(':')[0]
                        return int(host_port)
                    if isinstance(port_mapping, dict) and 'published' in port_mapping:
                        return int(port_mapping['published'])
        except Exception:
            pass

        lab = self._get_plugin_lab_meta(plugin_name)
        if lab.get('port') not in (None, False, ''):
            try:
                return int(lab['port'])
            except (TypeError, ValueError):
                pass

        raise ValueError(
            f"No lab port configured for '{plugin_name}'. "
            f"Set ports: in siddhis/{plugin_name}/lab/docker-compose.yml "
            f"or composition.lab.port in siddhis/{plugin_name}/{plugin_name}.yaml"
        )

    def _port_conflicts(self, ports: List[int]) -> List[Tuple[int, str]]:
        """Return (port, hint) for host ports that already accept connections."""
        import socket

        conflicts: List[Tuple[int, str]] = []
        for port in ports:
            if port is None:
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.35)
                    if sock.connect_ex(('127.0.0.1', int(port))) != 0:
                        continue
            except OSError:
                continue
            hint = f'127.0.0.1:{port} already accepting connections'
            try:
                # Best-effort: name the Docker publisher when present.
                ps = subprocess.run(
                    ['docker', 'ps', '--format', '{{.Names}}\t{{.Ports}}'],
                    capture_output=True, text=True, timeout=5,
                )
                if ps.returncode == 0:
                    needle = f':{port}->'
                    for line in (ps.stdout or '').splitlines():
                        if needle in line or f':{port}-' in line:
                            name = line.split('\t', 1)[0].strip()
                            if name:
                                hint = f'port {port} published by Docker container {name}'
                                break
            except Exception:
                pass
            conflicts.append((int(port), hint))
        return conflicts

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
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            else:
                # Stream progress to the terminal AND keep a copy so callers
                # can surface a real error (compose often writes failures to
                # stdout; without capture, CompletedProcess.stderr is None).
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                chunks: List[str] = []
                assert proc.stdout is not None
                for line in proc.stdout:
                    chunks.append(line)
                    try:
                        sys.stdout.write(line)
                        sys.stdout.flush()
                    except Exception:
                        pass
                returncode = proc.wait(timeout=300)
                combined = ''.join(chunks)
                result = subprocess.CompletedProcess(
                    args=cmd,
                    returncode=returncode,
                    stdout=combined,
                    stderr=combined,
                )
            
            return result
            
        finally:
            os.chdir(original_cwd)

    def _wait_for_service(self, plugin_name: str, timeout: int = 60) -> bool:
        """Wait for lab service(s) to be ready."""
        ports = self._get_lab_ports(plugin_name)
        
        start_time = time.time()
        services_ready = 0
        
        while time.time() - start_time < timeout:
            services_ready = 0
            
            for port in ports:
                url = f"http://localhost:{port}"
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code < 500:  # Any response < 500 means service is up
                        services_ready += 1
                except requests.RequestException:
                    pass
            
            # For multi-service labs, at least 70% of services should be ready
            required_services = max(1, int(len(ports) * 0.7))
            if services_ready >= required_services:
                return True
            
            time.sleep(2)
        
        return services_ready > 0  # At least one service is ready

    def _check_lab_health(self, plugin_name: str) -> bool:
        """Check if a lab is running and healthy."""
        ports = self._get_lab_ports(plugin_name)
        healthy_services = 0
        
        for port in ports:
            url = f"http://localhost:{port}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:
                    healthy_services += 1
            except requests.RequestException:
                pass
        
        # For multi-service labs, at least 70% should be healthy
        if len(ports) > 1:
            required_healthy = max(1, int(len(ports) * 0.7))
            return healthy_services >= required_healthy
        else:
            return healthy_services > 0

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

            # Step 4b: Fail fast on host port collisions (common with other labs)
            conflicts = self._port_conflicts(self._get_lab_ports(plugin_name))
            if conflicts:
                cprint(f"❌ Cannot start lab '{plugin_name}': host port(s) already in use", 'red')
                for port, hint in conflicts:
                    cprint(f"   • {hint}", 'yellow')
                cprint(
                    "   Stop the conflicting container/lab, or remap ports in the lab compose file.",
                    'cyan',
                )
                return False
            
            # Step 5: Start the lab
            cprint(f"🚀 Starting lab for plugin '{plugin_name}'...", 'cyan')
            
            # Run docker-compose up
            result = self._run_docker_compose(plugin_name, "up --build -d")
            if result.returncode != 0:
                err = (result.stderr or result.stdout or '').strip()
                if not err:
                    err = f'docker-compose exited with code {result.returncode}'
                # Prefer the last non-empty line (usually the bind/port error).
                last = next(
                    (ln.strip() for ln in reversed(err.splitlines()) if ln.strip()),
                    err,
                )
                cprint(f"❌ Failed to start lab: {last}", 'red')
                return False
            
            # Step 6: Wait for service to be ready
            cprint(f"⏳ Waiting for lab service to be ready...", 'cyan')
            if not self._wait_for_service(plugin_name):
                cprint(f"❌ Lab service failed to start within timeout", 'red')
                return False
            
            # Step 7: Create targets file and set environment variable
            targets_file = self._create_targets_file(plugin_name)
            
            # Step 8: Update status and show info
            port = self._get_lab_port(plugin_name)
            self.active_labs[plugin_name] = {
                "status": "running",
                "port": port,
                "started_at": time.time(),
                "url": f"http://localhost:{port}",
                "targets_file": targets_file
            }
            self._save_lab_status()
            
            cprint(f"✅ Lab for '{plugin_name}' started successfully!", 'green')
            if targets_file:
                cprint(f"📝 Targets file created: {targets_file}", 'cyan')
                cprint(f"🔧 To set VIMANA_LAB_TARGETS, run:", 'cyan')
                cprint(f"   export VIMANA_LAB_TARGETS={targets_file}", 'yellow')
                cprint(f"   # or source the .env file:", 'cyan')
                cprint(f"   source {os.path.join(self._get_plugin_lab_path(plugin_name), '.env')}", 'yellow')
            
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
                # Still clear stale status entry if present
                if plugin_name in self.active_labs:
                    del self.active_labs[plugin_name]
                    self._save_lab_status()
                return True
            
            cprint(f"🛑 Stopping lab for plugin '{plugin_name}'...", 'cyan')
            
            # Run docker-compose down (capture stderr for diagnostics)
            result = self._run_docker_compose(plugin_name, "down", capture_output=True)
            if result.returncode != 0:
                err = (result.stderr or result.stdout or '').strip() or f'exit {result.returncode}'
                cprint(f"❌ Failed to stop lab: {err}", 'red')
                return False
            
            # Update status
            if plugin_name in self.active_labs:
                # Clean up targets file and .env file if they exist
                if "targets_file" in self.active_labs[plugin_name]:
                    targets_file = self.active_labs[plugin_name]["targets_file"]
                    if targets_file and os.path.exists(targets_file):
                        try:
                            os.remove(targets_file)
                            cprint(f"🗑️  Targets file removed: {targets_file}", 'cyan')
                        except Exception as e:
                            cprint(f"Warning: Could not remove targets file: {e}", 'yellow')
                    
                    # Also remove .env file
                    lab_path = self._get_plugin_lab_path(plugin_name)
                    env_file = os.path.join(lab_path, ".env")
                    if os.path.exists(env_file):
                        try:
                            os.remove(env_file)
                            cprint(f"🗑️  Environment file removed: {env_file}", 'cyan')
                        except Exception as e:
                            cprint(f"Warning: Could not remove environment file: {e}", 'yellow')
                
                del self.active_labs[plugin_name]
                self._save_lab_status()
            else:
                # Lab was running in Docker but not tracked in status file — still OK
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
                        if self._is_multi_service_lab(plugin_name):
                            # Multi-service lab info
                            services = self._get_lab_services(plugin_name)
                            print(f"    🧪 Type: Multi-Service Lab ({len(services)} frameworks)")
                            for service_name, service_info in services.items():
                                framework = service_info["framework"]
                                port = service_info["port"]
                                print(f"    📍 {framework}: http://localhost:{port}")
                            
                            if is_running:
                                print(f"    🎯 Test All: vimana run {plugin_name} --file $VIMANA_LAB_TARGETS")
                                all_urls = [f"http://localhost:{service['port']}" for service in services.values()]
                                for u in all_urls[:2]:
                                    print(f"    🎯 Example: {self._format_run_hint(plugin_name, u)}")
                        else:
                            # Single-service lab info
                            try:
                                port = self._get_lab_port(plugin_name)
                            except ValueError as exc:
                                print(f"    ⚠️  {exc}")
                                print()
                                continue
                            print(f"    📍 Port: {port}")
                            print(f"    🌐 URL: http://localhost:{port}")
                            
                            if is_running:
                                print(f"    🎯 Test Command: {self._format_run_hint(plugin_name, f'http://localhost:{port}')}")
                    
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
            if self._is_multi_service_lab(plugin_name):
                self._show_multi_service_lab_info(plugin_name)
            else:
                self._show_single_service_lab_info(plugin_name)
            
        except Exception as e:
            cprint(f"Warning: Could not show lab info: {e}", 'yellow')
    
    def _show_single_service_lab_info(self, plugin_name: str) -> None:
        """Show information for single-service labs."""
        port = self._get_lab_port(plugin_name)
        url = f"http://localhost:{port}"
        
        print(f"\n🌐 Lab Information:")
        print(f"   📍 Port: {port}")
        print(f"   🌐 URL: {url}")
        print(f"   🎯 Test Command: {self._format_run_hint(plugin_name, url)}")

        lab_path = self._get_plugin_lab_path(plugin_name)
        if os.path.exists(os.path.join(lab_path, "docker-compose.yml")):
            print(f"   📡 OpenAPI:       {url}/openapi.json")
        
        # Show targets file info if it exists
        if plugin_name in self.active_labs and "targets_file" in self.active_labs[plugin_name]:
            targets_file = self.active_labs[plugin_name]["targets_file"]
            if targets_file and os.path.exists(targets_file):
                print(f"   📝 Targets File: {targets_file}")
                print(f"   🔧 VIMANA_LAB_TARGETS: {os.environ.get('VIMANA_LAB_TARGETS', 'Not set')}")
                print(f"   💡 To set in shell: export VIMANA_LAB_TARGETS={targets_file}")
        
        # Show lab-specific information if available
        readme_file = os.path.join(lab_path, "README.md")
        
        if os.path.exists(readme_file):
            print(f"   📖 Documentation: {readme_file}")
        
        # Show docker-compose services if available
        config = self._get_lab_config(plugin_name)
        services = config.get('services', {})
        if services:
            print(f"   🐳 Services: {', '.join(services.keys())}")
        
        print()
    
    def _show_multi_service_lab_info(self, plugin_name: str) -> None:
        """Show information for multi-service labs."""
        services = self._get_lab_services(plugin_name)
        
        print(f"\n🌐 Multi-Service Lab Information:")
        print(f"   🧪 Lab Type: {plugin_name.capitalize()} Framework Testing Lab")
        print(f"   📦 Services: {len(services)} framework containers")
        print()
        
        print("🌐 Available Endpoints:")
        for service_name, service_info in services.items():
            framework = service_info["framework"]
            port = service_info["port"]
            url = f"http://localhost:{port}"
            
            # Check if service is healthy
            try:
                response = requests.get(url, timeout=3)
                status = "🟢 RUNNING" if response.status_code < 500 else "🟡 ISSUES"
            except requests.RequestException:
                status = "🔴 DOWN"
            
            print(f"   {framework:<12} {url:<25} {status}")
        
        print()
        print("🧪 Test Individual Frameworks:")
        for service_name, service_info in services.items():
            framework = service_info["framework"]
            port = service_info["port"]
            url = f"http://localhost:{port}"
            print(f"   {self._format_run_hint(plugin_name, url)}")
        
        print()
        print("🔗 Test All Frameworks at Once:")
        print(f"   vimana run {plugin_name} --file $VIMANA_LAB_TARGETS")
        print(f"   vimana run {plugin_name} --file {os.environ.get('VIMANA_LAB_TARGETS', 'targets.txt')}")
        all_urls = [f"http://localhost:{service['port']}" for service in services.values()]
        if all_urls:
            print(f"   {self._format_run_hint(plugin_name, all_urls[0])}")
        
        print()
        print("🔧 Environment Setup:")
        current_env = os.environ.get('VIMANA_LAB_TARGETS', 'Not set')
        print(f"   VIMANA_LAB_TARGETS: {current_env}")
        targets_file = None
        if plugin_name in self.active_labs:
            targets_file = self.active_labs[plugin_name].get('targets_file')
        if not targets_file:
            targets_file = os.path.join(self._get_plugin_lab_path(plugin_name), 'targets.txt')
        if current_env != 'Not set':
            print(f"   To use in shell: export VIMANA_LAB_TARGETS={current_env}")
        else:
            print(f"   To set: export VIMANA_LAB_TARGETS={targets_file}")
        
        print()
        print("🛑 Lab Control:")
        print(f"   Start+Test: vimana run --lab {plugin_name} --test")
        print(f"   Stop Lab:   vimana run --lab {plugin_name} --stop")
        print(f"   Lab Status: vimana run --lab {plugin_name} --lab-operation status")
        print(f"   Cleanup:    vimana run --lab {plugin_name} --lab-operation cleanup")
        
        # Show lab-specific information if available
        lab_path = self._get_plugin_lab_path(plugin_name)
        readme_file = os.path.join(lab_path, "README.md")
        
        if os.path.exists(readme_file):
            print(f"   📖 Documentation: {readme_file}")
        
        print()

    def _discover_running_labs(self) -> List[str]:
        """Find labs that respond on their ports (Docker truth), not only status file."""
        running: List[str] = []
        if not os.path.isdir(self.labs_root):
            return running
        for entry in os.scandir(self.labs_root):
            if not entry.is_dir() or entry.name.startswith('_'):
                continue
            lab_dir = os.path.join(entry.path, 'lab')
            if not os.path.isdir(lab_dir):
                continue
            try:
                if self._check_lab_health(entry.name):
                    running.append(entry.name)
            except Exception:
                continue
        return sorted(running)

    def cleanup_labs(self) -> None:
        """Stop all running labs and clean up (Docker health + status file)."""
        try:
            discovered = self._discover_running_labs()
            tracked = list(self.active_labs.keys())
            names = sorted(set(discovered) | set(tracked))

            if not names:
                cprint("ℹ️  No active labs to clean up", 'cyan')
                return

            cprint("🧹 Cleaning up labs...", 'cyan')
            if discovered:
                cprint(f"   Detected running: {', '.join(discovered)}", 'white')
            if tracked and set(tracked) - set(discovered):
                stale = sorted(set(tracked) - set(discovered))
                cprint(f"   Stale status entries: {', '.join(stale)}", 'yellow')

            for plugin_name in names:
                self.stop_lab(plugin_name)

            self.active_labs = {}
            if os.path.exists(self.lab_status_file):
                try:
                    os.remove(self.lab_status_file)
                except Exception as e:
                    cprint(f"Warning: Could not remove status file: {e}", 'yellow')

            cprint("✅ All labs cleaned up successfully!", 'green')

        except Exception as e:
            cprint(f"❌ Error during cleanup: {str(e)}", 'red')


def _resolve_lab_operation(handler_ns) -> str:
    """
    Resolve lab operation from flags / positional token.

    Supports:
      vimana run --lab X --lab-operation stop
      vimana run --lab X --stop
      vimana run --lab X stop          # positional (common mistake → now works)
      vimana run --lab-operation cleanup   # no --lab required
      vimana run --cleanup-labs
      vimana run --lab-operation list
    """
    ops = {'start', 'stop', 'status', 'list', 'cleanup'}

    if getattr(handler_ns, 'cleanup_labs', False):
        return 'cleanup'

    if getattr(handler_ns, 'lab_stop', False):
        return 'stop'

    positional = getattr(handler_ns, 'plugin_name', None)
    if positional and str(positional).lower() in ops:
        return str(positional).lower()

    leftovers = getattr(handler_ns, 'args', None) or []
    if isinstance(leftovers, (list, tuple)):
        for tok in leftovers:
            if str(tok).lower() in ops:
                return str(tok).lower()

    if getattr(handler_ns, 'lab_operation', None):
        return str(handler_ns.lab_operation)

    return 'start'


def handle_lab_command(handler_ns) -> None:
    """
    Main entry point for lab management commands.
    
    Args:
        handler_ns: Vimana handler namespace with lab parameters
    """
    try:
        lab_manager = VimanaLabManager(**vars(handler_ns))
        lab_name = getattr(handler_ns, 'run_lab', None) or None
        operation = _resolve_lab_operation(handler_ns)

        # Global ops do not require --lab
        if operation in ('cleanup', 'list'):
            if operation == 'list':
                lab_manager.list_labs()
            else:
                lab_manager.cleanup_labs()
            return

        if not lab_name:
            cprint("❌ No lab specified", 'red')
            cprint("   Usage: vimana run --lab <plugin_name>", 'cyan')
            cprint("   Stop:  vimana run --lab <plugin_name> --stop", 'cyan')
            cprint("   Test:  vimana run --lab <plugin_name> --test", 'cyan')
            cprint("   All:   vimana run --cleanup-labs", 'cyan')
            cprint("   List:  vimana run --lab-operation list", 'cyan')
            return

        want_test = bool(getattr(handler_ns, 'lab_test', False))
        if want_test and operation not in ('start',):
            cprint("❌ --test only applies with lab start (default operation)", 'red')
            cprint("   Usage: vimana run --lab <plugin_name> --test", 'cyan')
            sys.exit(1)
        
        if operation == "start":
            success = lab_manager.start_lab(lab_name)
        elif operation == "stop":
            success = lab_manager.stop_lab(lab_name)
        elif operation == "status":
            success = lab_manager.status_lab(lab_name)
        else:
            cprint(f"❌ Unknown lab operation: {operation}", 'red')
            cprint("   Available operations: start, stop, status, list, cleanup", 'cyan')
            cprint("   Tip: vimana run --lab <plugin> --stop", 'cyan')
            cprint("   Tip: vimana run --cleanup-labs", 'cyan')
            return
        
        if not success:
            sys.exit(1)

        if want_test and operation == "start":
            if not lab_manager.test_lab_plugin(lab_name):
                sys.exit(1)
            
    except Exception as e:
        cprint(f"❌ Lab management error: {str(e)}", 'red')
        sys.exit(1)

