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
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Try to import rich for enhanced terminal output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.tree import Tree
    from rich.text import Text
    from rich.box import Box, ROUNDED
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    
# Try to import colorama for cross-platform colored output as fallback
if not HAS_RICH:
    try:
        from colorama import init, Fore, Style
        init(autoreset=True)
        HAS_COLOR = True
    except ImportError:
        # Create dummy color classes if colorama is not available
        class DummyFore:
            def __getattr__(self, name):
                return ''
        
        class DummyStyle:
            def __getattr__(self, name):
                return ''
        
        Fore = DummyFore()
        Style = DummyStyle()
        HAS_COLOR = False

# Import shared progress tracker (optional, will be set later if available)
progress_tracker = None

# ASCII Art Logo
FRAMEWALK_LOGO = """                                 
                        ● 
                                           ╭──────╨─────────╮
                                           │            ◎   │
                                           │  ╭──────╮      │  
                                           │  │Bottle░      │ 
      ╔═══════════════════════╗            │  ╰──┬───╯      │ 
      ║ ╭────╮  FRAMEWALK  ★  ║╮           │     │          │
      ║ │ ◎─│───────────────────◎          │  ╭──┴───╮      │ 
      ║ ╰────╯                ║╯           │  │Sanic ├──────┤ 
╭─────╨─────────╮             ║            │  ╰──────╯      │   
│  ╭──────╮     │             ║            │             ╭──┴───╮
│  │Django├──┬──╯       ╭─────╯            └─────╭───────┤Web2py│
│  ╰──────╯  │     ╭────┴╮                       │       ╰──────╯  
╰─────┬──────╯     │Flask│───●──●──●─────────────╯
      │  ●         ╰──╭──╯
   ╭──┴────╮   ╭─────╯│       ╭──●           
   │FastAPI ───╯      ╰───────│ 
   ╰───────╯                  ╰──● Tornado
                                                
"""

# Framework colors (used with rich or colorama)
FRAMEWORK_COLORS = {
    'Django': 'green',
    'Flask': 'blue',
    'FastAPI': 'magenta',
    'Pyramid': 'yellow',
    'Bottle': 'cyan',
    'Tornado': 'red',
    'Sanic': 'bright_blue',
    'Falcon': 'bright_cyan',
    'Quart': 'bright_magenta',
    'Web2py': 'bright_green',
}


class TerminalPresenter:
    """Handles terminal output presentation with enhanced formatting and progress integration"""
    
    def __init__(self, show_evidence: bool = True, show_metadata: bool = True, verbose: bool = False):
        """
        Initialize the terminal presenter
        
        Args:
            show_evidence: Whether to show detailed evidence
            show_metadata: Whether to show framework metadata
            verbose: Whether to show verbose output
        """
        self.show_evidence = show_evidence
        self.show_metadata = show_metadata
        self.verbose = verbose
        self.progress_tracker = None  # Will be set by siddhi
        
        # Initialize rich console if available
        if HAS_RICH:
            self.console = Console()
            self.use_rich = True
        else:
            self.use_rich = False
            
    def set_progress_tracker(self, tracker):
        """Set the progress tracker for coordinated output"""
        self.progress_tracker = tracker
            
    def print_header(self) -> None:
        """Print the tool header"""
        if self.use_rich:
            # Create a panel with the logo
            self.console.print(Panel(FRAMEWALK_LOGO, style="cyan", border_style="blue"))
        else:
            # Fallback to simple colored output
            if HAS_COLOR:
                print(f"{Fore.CYAN}{FRAMEWALK_LOGO}{Style.RESET_ALL}")
            else:
                print(FRAMEWALK_LOGO)
                
    def print_status(self, message: str) -> None:
        """
        Print a status message
        
        Args:
            message: Status message to print
        """
        if not self.verbose:
            return
        
        # Use progress tracker for clean output if available    
        if self.progress_tracker:
            self.progress_tracker.print_verbose(f"[[*]] {message}")
            return
            
        if self.use_rich:
            self.console.print(f"[blue][[*]] [cyan]{message}")
        elif HAS_COLOR:
            print(f"{Fore.BLUE}[*] {Fore.CYAN}{message}{Style.RESET_ALL}")
        else:
            print(f"[*] {message}")
            
    def print_results(self, results: Dict[str, Any]) -> None:
        """
        Print formatted results to console
        
        Args:
            results: Results dictionary from the detection process
        """
        frameworks = results.get("frameworks", [])
        
        if self.use_rich:
            self._print_results_rich(results, frameworks)
        else:
            self._print_results_simple(results, frameworks)
            
    def _print_results_rich(self, results: Dict[str, Any], frameworks: List[Dict[str, Any]]) -> None:
        """Print results using enhanced rich formatting with better colors"""
        # Print header
        self.console.print("\n")
        self.console.rule("[bold cyan]Scan Results", style="cyan")
        
        # Print target info with better styling
        self.console.print(f"\n[bold]Target:[/bold] [yellow]{results['target_url']}[/yellow]")
        self.console.print(f"[bold]Scan time:[/bold] [yellow]{results['scan_time']:.2f}[/yellow] seconds")
        if 'ip_info' in results and results['ip_info']:
            ip_info = results['ip_info']
            self.console.print(f"[bold]IP:[/bold] [yellow]{ip_info.get('ip', 'Unknown')}[/yellow]")
            
        # Print server info
        if 'server_info' in results and results['server_info']:
            server_info = results['server_info']
            server_text = f"[bold]Server:[/bold] [yellow]{server_info.get('type', 'Unknown')}"
            if 'version' in server_info:
                server_text += f" {server_info['version']}"
            self.console.print(server_text)
            
        # Print security headers
        if 'security_headers' in results and results['security_headers']:
            self.console.print("\n[bold cyan]Security Headers:[/bold cyan]")
            
            security_table = Table(show_header=True, header_style="bold white on black", box=ROUNDED)
            security_table.add_column("Header")
            security_table.add_column("Status")
            
            sec_headers = results['security_headers']
            present = sec_headers.get('present', [])
            missing = sec_headers.get('missing', [])
            
            for header in present:
                security_table.add_row(header, "[green]Present[/green]")
                
            for header in missing:
                security_table.add_row(header, "[red]Missing[/red]")
                
            self.console.print(security_table)
            
        # Framework detection results
        if not frameworks:
            self.console.print("\n[bold red]No frameworks detected with confidence.[/bold red]")
            return
            
        self.console.print("\n[bold cyan]Detected Frameworks:[/bold cyan]")
        
        # Create a table for frameworks with better styling
        framework_table = Table(show_header=True, header_style="bold white on black", box=ROUNDED)
        framework_table.add_column("Framework", style="bold")
        framework_table.add_column("Confidence", style="bold")
        framework_table.add_column("Version", style="bold cyan")
        framework_table.add_column("Components", style="bold magenta")
        
        for fw in frameworks:
            # Get color from metadata
            framework = fw['name']
            color = FRAMEWORK_COLORS.get(framework, "white")
            confidence = fw['confidence']
            version = fw['version']
            
            # Format confidence bar with improved styling
            conf_bar = "█" * int(confidence / 5)  # 20 chars max
            empty_bar = "░" * (20 - int(confidence / 5))
            conf_text = f"{confidence}% [{conf_bar}{empty_bar}]"
            
            # Format components
            components = fw.get('components', [])
            components_text = ", ".join(components) if components else "None detected"
            
            framework_table.add_row(
                f"[bold {color}]{framework}[/bold {color}]",
                f"[yellow]{conf_text}[/yellow]",
                f"{version}",
                components_text
            )
            
        self.console.print(framework_table)
        
        # Show vulnerabilities if available with better styling
        for fw in frameworks:
            framework = fw['name']
            color = FRAMEWORK_COLORS.get(framework, "white")
            vulnerabilities = fw.get('vulnerabilities', [])
            
            if vulnerabilities:
                self.console.print(f"\n[bold {color}]{framework}[/bold {color}] [bold red]Potential Vulnerabilities:[/bold red]")
                
                vuln_table = Table(show_header=True, header_style="bold white on black", box=ROUNDED)
                vuln_table.add_column("CVE ID", style="bold red")
                vuln_table.add_column("Description")
                
                for vuln in vulnerabilities:
                    vuln_table.add_row(
                        vuln.get('id', 'Unknown'),
                        vuln.get('description', 'No description')
                    )
                    
                self.console.print(vuln_table)
                
        # Show evidence if requested with improved styling
        if self.show_evidence and 'evidence' in results:
            self.console.print("\n[bold cyan]Detection Evidence:[/bold cyan]")
            
            # Create a tree for evidence
            evidence_tree = Tree("[bold]Evidence by Framework[/bold]")
            
            for framework, evidence_list in results['evidence'].items():
                if framework in [fw['name'] for fw in frameworks]:
                    # Get color from metadata
                    color = FRAMEWORK_COLORS.get(framework, "white")
                    framework_node = evidence_tree.add(f"[bold {color}]{framework}[/bold {color}]")
                    
                    # Group evidence by type
                    evidence_by_type = defaultdict(list)
                    for evidence in evidence_list:
                        parts = evidence.split(": ", 1)
                        if len(parts) == 2:
                            evidence_type, detail = parts
                            evidence_by_type[evidence_type].append(detail)
                    
                    # Add evidence by type with better styling
                    for evidence_type, details in evidence_by_type.items():
                        type_node = framework_node.add(f"[yellow]{evidence_type}[/yellow]")
                        for detail in details:
                            type_node.add(detail)
                            
            self.console.print(evidence_tree)
            
        # Add recommendations with enhanced styling
        if frameworks:
            top_framework = frameworks[0]['name']
            color = FRAMEWORK_COLORS.get(top_framework, "white")
            
            self.console.print("\n[bold cyan]Recommendations:[/bold cyan]")
            
            # Add styled recommendations
            self.console.print(f"• Primary target appears to be: [bold {color}]{top_framework}[/bold {color}]")
            
            if frameworks[0]['confidence'] > 80:
                self.console.print("• [green]High confidence detection - proceed with framework-specific testing[/green]")
                
                # Suggest framework-specific plugins
                if top_framework == "Django":
                    self.console.print("• [yellow]Try these tools:[/yellow] [white]djunch, dmt, jungle[/white]")
                elif top_framework == "Flask":
                    self.console.print("• [yellow]Try these tools:[/yellow] [white]flame, atlatl[/white]")
                    
            else:
                self.console.print("• [yellow]Medium/low confidence detection - use manual verification techniques[/yellow]")
                self.console.print("• [white]Consider deeper analysis with more invasive techniques[/white]")
                


    def _print_results_simple(self, results: Dict[str, Any], frameworks: List[Dict[str, Any]]) -> None:
        """Print results using simple formatting with colorama if available"""
        # Print header
        print("\n" + "="*70)
        if HAS_COLOR:
            print(f"{Fore.CYAN}Results for {Fore.YELLOW}{results['target_url']}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Scan completed in {Fore.YELLOW}{results['scan_time']:.2f}{Fore.CYAN} seconds{Style.RESET_ALL}")
        else:
            print(f"Results for {results['target_url']}")
            print(f"Scan completed in {results['scan_time']:.2f} seconds")
        print("="*70)
        
        # Framework detection results
        if not frameworks:
            if HAS_COLOR:
                print(f"\n{Fore.RED}No frameworks detected with confidence.{Style.RESET_ALL}")
            else:
                print("\nNo frameworks detected with confidence.")
            return
            
        if HAS_COLOR:
            print(f"\n{Fore.WHITE}{Style.BRIGHT}Detected frameworks (ordered by confidence):{Style.RESET_ALL}\n")
        else:
            print("\nDetected frameworks (ordered by confidence):\n")
            
        for fw in frameworks:
            framework = fw['name']
            confidence = fw['confidence']
            score = fw['score']
            version = fw['version']
            
            # Get color from metadata if available
            color = Fore.WHITE if not HAS_COLOR else getattr(Fore, FRAMEWORK_COLORS.get(framework, "WHITE").upper())
            
            # Print the framework with a confidence bar
            conf_bar = "█" * int(confidence / 5)  # 20 chars max
            
            if HAS_COLOR:
                print(f"  {color}{Style.BRIGHT}{framework}{Style.RESET_ALL} {Fore.YELLOW}v{version}{Style.RESET_ALL}")
                print(f"  {color}Confidence: {confidence}% {Style.DIM}[{conf_bar}]{Style.RESET_ALL} (score: {score})")
            else:
                print(f"  {framework} v{version}")
                print(f"  Confidence: {confidence}% [{conf_bar}] (score: {score})")
                
            # Show components
            components = fw.get('components', [])
            if components:
                if HAS_COLOR:
                    print(f"  {Fore.CYAN}Components: {', '.join(components)}{Style.RESET_ALL}")
                else:
                    print(f"  Components: {', '.join(components)}")
                    
            # Show metadata if available and requested
            if self.show_metadata and 'metadata' in fw and fw['metadata']:
                meta = fw['metadata']
                if HAS_COLOR:
                    print(f"  {Fore.WHITE}{Style.DIM}{meta.get('description', '')}{Style.RESET_ALL}")
                    print(f"  {Fore.BLUE}{Style.DIM}{meta.get('website', '')}{Style.RESET_ALL}")
                else:
                    print(f"  {meta.get('description', '')}")
                    print(f"  {meta.get('website', '')}")
                    
                # Show CVEs if available
                vulnerabilities = fw.get('vulnerabilities', [])
                if vulnerabilities:
                    if HAS_COLOR:
                        print(f"\n  {Fore.RED}{Style.BRIGHT}Potential vulnerabilities:{Style.RESET_ALL}")
                    else:
                        print("\n  Potential vulnerabilities:")
                        
                    for vuln in vulnerabilities[:3]:  # Show top 3 CVEs
                        if HAS_COLOR:
                            print(f"  - {Fore.RED}{vuln.get('id', 'Unknown')}{Style.RESET_ALL}: {vuln.get('description', '')}")
                        else:
                            print(f"  - {vuln.get('id', 'Unknown')}: {vuln.get('description', '')}")
                            
            print("")  # Empty line between frameworks
            
        # Show evidence if requested
        if self.show_evidence and 'evidence' in results:
            if HAS_COLOR:
                print(f"\n{Fore.WHITE}{Style.BRIGHT}Evidence:{Style.RESET_ALL}")
            else:
                print("\nEvidence:")
                
            for framework, evidence_list in results['evidence'].items():
                if framework in [fw['name'] for fw in frameworks]:
                    # Get color from metadata if available
                    color = Fore.WHITE if not HAS_COLOR else getattr(Fore, FRAMEWORK_COLORS.get(framework, "WHITE").upper())
                    
                    if HAS_COLOR:
                        print(f"\n  {color}{Style.BRIGHT}{framework}:{Style.RESET_ALL}")
                    else:
                        print(f"\n  {framework}:")
                        
                    # Group evidence by type
                    evidence_by_type = defaultdict(list)
                    for evidence in evidence_list:
                        parts = evidence.split(": ", 1)
                        if len(parts) == 2:
                            evidence_type, detail = parts
                            evidence_by_type[evidence_type].append(detail)
                    
                    # Print evidence grouped by type
                    for evidence_type, details in evidence_by_type.items():
                        if HAS_COLOR:
                            print(f"    {Fore.YELLOW}{evidence_type}:{Style.RESET_ALL}")
                        else:
                            print(f"    {evidence_type}:")
                            
                        for detail in details:
                            print(f"      - {detail}")
                            
        # Recommendations
        if frameworks:
            top_framework = frameworks[0]['name']
            
            if HAS_COLOR:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}Recommendations:{Style.RESET_ALL}")
                color = getattr(Fore, FRAMEWORK_COLORS.get(top_framework, "WHITE").upper())
                print(f"  • {Fore.WHITE}Primary target appears to be: {color}{top_framework}{Style.RESET_ALL}")
            else:
                print("\nRecommendations:")
                print(f"  • Primary target appears to be: {top_framework}")
                
            if frameworks[0]['confidence'] > 80:
                if HAS_COLOR:
                    print(f"  • {Fore.GREEN}High confidence detection - proceed with framework-specific testing{Style.RESET_ALL}")
                else:
                    print(f"  • High confidence detection - proceed with framework-specific testing")
                    
                # Suggest framework-specific plugins
                if top_framework == "Django":
                    if HAS_COLOR:
                        print(f"  • {Fore.YELLOW}Try these tools: {Fore.WHITE}djunch, dmt, jungle{Style.RESET_ALL}")
                    else:
                        print(f"  • Try these tools: djunch, dmt, jungle")
                elif top_framework == "Flask":
                    if HAS_COLOR:
                        print(f"  • {Fore.YELLOW}Try these tools: {Fore.WHITE}flame, atlatl{Style.RESET_ALL}")
                    else:
                        print(f"  • Try these tools: flame, atlatl")
            else:
                if HAS_COLOR:
                    print(f"  • {Fore.YELLOW}Medium/low confidence detection - use manual verification techniques{Style.RESET_ALL}")
                    print(f"  • {Fore.WHITE}Consider deeper analysis with more invasive techniques{Style.RESET_ALL}")
                else:
                    print(f"  • Medium/low confidence detection - use manual verification techniques")
                    print(f"  • Consider deeper analysis with more invasive techniques")


    def print_aggregate_results(self, aggregate_results: Dict[str, Any]) -> None:
        """
        Print aggregate results for multiple targets
        
        Args:
            aggregate_results: Dictionary with aggregate results
        """
        if self.use_rich:
            self._print_aggregate_results_rich(aggregate_results)
        else:
            self._print_aggregate_results_simple(aggregate_results)
            
    def _print_aggregate_results_rich(self, aggregate_results: Dict[str, Any]) -> None:
        """Print aggregate results using rich formatting with improved colors"""
        # Print header with better styling
        self.console.print("\n")
        self.console.rule("[bold cyan]Aggregate Scan Results[/bold cyan]", style="cyan")
        
        # Print summary with better color styling
        target_count = len(aggregate_results.get('targets', []))
        total_time = aggregate_results.get('scan_time', 0)
        timestamp = aggregate_results.get('timestamp', '')
        
        self.console.print(f"\n[cyan]Scanned Targets:[/cyan] [yellow]{target_count}[/yellow]")
        self.console.print(f"[cyan]Total Scan Time:[/cyan] [yellow]{total_time:.2f}[/yellow] seconds")
        self.console.print(f"[cyan]Timestamp:[/cyan] [yellow]{timestamp}[/yellow]")
        
        # Add a section header for framework distribution
        self.console.print("\n[bold cyan]Framework Distribution:[/bold cyan]")
        
        try:
            # Import ROUNDED here to avoid issues
            from rich.box import ROUNDED
            
            # Create a framework distribution table with better styling
            fw_table = Table(show_header=True, header_style="bold white on black", box=ROUNDED)
            fw_table.add_column("Framework", style="bold")
            fw_table.add_column("Count", style="bold cyan")
            fw_table.add_column("Percentage", style="bold yellow")
            fw_table.add_column("Distribution", style="bold")
            
            framework_counts = aggregate_results.get('framework_counts', {})
            
            for fw_name, count in sorted(framework_counts.items(), key=lambda x: x[1], reverse=True):
                # Get color from metadata
                color = FRAMEWORK_COLORS.get(fw_name, "white")
                percentage = (count / target_count) * 100 if target_count > 0 else 0
                
                # Create a distribution bar with the framework's color
                bar_width = 20
                bar_filled = int((count / target_count) * bar_width) if target_count > 0 else 0
                distribution = "█" * bar_filled + "░" * (bar_width - bar_filled)
                
                fw_table.add_row(
                    f"[bold {color}]{fw_name}[/bold {color}]",
                    f"{count}",
                    f"{percentage:.1f}%",
                    f"[{color}]{distribution}[/{color}]"
                )
                
            self.console.print(fw_table)
            
            # Add a section header for target details
            self.console.print("\n[bold cyan]Target Details:[/bold cyan]")
            
            # Create a target details table with better styling
            target_table = Table(show_header=True, header_style="bold white on black", box=ROUNDED)
            target_table.add_column("Target URL", style="bold")
            target_table.add_column("Top Framework", style="bold")
            target_table.add_column("Confidence", style="bold")
            target_table.add_column("Scan Time", style="bold cyan")
            target_table.add_column("Frameworks", style="bold green")
            target_table.add_column("Components", style="bold magenta")
            
            for target in aggregate_results.get('targets', []):
                # Get color for the framework
                fw_name = target.get('top_framework', 'Unknown')
                color = FRAMEWORK_COLORS.get(fw_name, "white")
                confidence = target.get('confidence', 0)
                
                # Format confidence bar with yellow for better visibility
                conf_bar = "█" * int(confidence / 5)  # 20 chars max
                empty_bar = "░" * (20 - int(confidence / 5))
                conf_text = f"{confidence}% [{conf_bar}{empty_bar}]"
                
                target_table.add_row(
                    target.get('url', 'Unknown'),
                    f"[bold {color}]{fw_name}[/bold {color}]",
                    f"[yellow]{conf_text}[/yellow]",
                    f"{target.get('scan_time', 0):.2f}s",
                    str(target.get('detected_frameworks', 0)),
                    str(target.get('components', 0))
                )
                
            self.console.print(target_table)
            
        except Exception as e:
            # Fallback if rich tables fail
            self.console.print(f"[red]Error displaying tables: {str(e)}[/red]")
            self.console.print("\n[bold cyan]Framework Distribution:[/bold cyan]")
            
            framework_counts = aggregate_results.get('framework_counts', {})
            for fw_name, count in sorted(framework_counts.items(), key=lambda x: x[1], reverse=True):
                color = FRAMEWORK_COLORS.get(fw_name, "white")
                percentage = (count / target_count) * 100 if target_count > 0 else 0
                self.console.print(f"• [bold {color}]{fw_name}[/bold {color}]: {count} ([yellow]{percentage:.1f}%[/yellow])")
            
            self.console.print("\n[bold cyan]Target Details:[/bold cyan]")
            for target in aggregate_results.get('targets', []):
                fw_name = target.get('top_framework', 'Unknown')
                color = FRAMEWORK_COLORS.get(fw_name, "white")
                self.console.print(f"• [bold]{target.get('url', 'Unknown')}[/bold]: [bold {color}]{fw_name}[/bold {color}] ([yellow]{target.get('confidence', 0)}%[/yellow])")
        
        # Add recommendations with better styling
        self.console.print("\n[bold cyan]Recommendations:[/bold cyan]")
        
        # Identify most common framework
        framework_counts = aggregate_results.get('framework_counts', {})
        most_common_fw = max(framework_counts.items(), key=lambda x: x[1])[0] if framework_counts else "Unknown"
        color = FRAMEWORK_COLORS.get(most_common_fw, "white")
        
        # Add styled recommendations
        self.console.print(f"• Most common framework detected: [bold {color}]{most_common_fw}[/bold {color}]")
        
        if target_count > 10:
            self.console.print(f"• [green]Large-scale scan - consider using automated tools for deeper analysis[/green]")
            
        if len(framework_counts) > 3:
            self.console.print(f"• [yellow]Diverse framework usage detected - consider targeting specific framework families[/yellow]")
            
    def connect_vimana_vte(self, vimana_vte):
        """Connect the Vimana VTE for progress tracking"""
        #self.vimana_vte = vimana_vte

    def _print_aggregate_results_simple(self, aggregate_results: Dict[str, Any]) -> None:
        """Print aggregate results using simple formatting"""
        # Print header
        print("\n" + "="*70)
        if HAS_COLOR:
            print(f"{Fore.CYAN}Aggregate Scan Results{Style.RESET_ALL}")
        else:
            print("Aggregate Scan Results")
        print("="*70)
        
        # Print summary
        target_count = len(aggregate_results.get('targets', []))
        total_time = aggregate_results.get('scan_time', 0)
        timestamp = aggregate_results.get('timestamp', '')
        
        if HAS_COLOR:
            print(f"{Fore.WHITE}{Style.BRIGHT}Scanned Targets:{Style.RESET_ALL} {Fore.YELLOW}{target_count}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{Style.BRIGHT}Total Scan Time:{Style.RESET_ALL} {Fore.YELLOW}{total_time:.2f}{Fore.CYAN} seconds{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{Style.BRIGHT}Timestamp:{Style.RESET_ALL} {Fore.YELLOW}{timestamp}{Style.RESET_ALL}")
        else:
            print(f"Scanned Targets: {target_count}")
            print(f"Total Scan Time: {total_time:.2f} seconds")
            print(f"Timestamp: {timestamp}")
            
        # Print framework distribution
        print("\nFramework Distribution:")
        
        framework_counts = aggregate_results.get('framework_counts', {})
        total_frameworks = sum(framework_counts.values())
        
        for fw_name, count in sorted(framework_counts.items(), key=lambda x: x[1], reverse=True):
            # Get color for the framework
            color = Fore.WHITE if not HAS_COLOR else getattr(Fore, FRAMEWORK_COLORS.get(fw_name, "WHITE").upper())
            percentage = (count / target_count) * 100 if target_count > 0 else 0
            
            # Create a distribution bar
            bar_width = 20
            bar_filled = int((count / target_count) * bar_width) if target_count > 0 else 0
            distribution = "█" * bar_filled + "░" * (bar_width - bar_filled)
            
            if HAS_COLOR:
                print(f"  {color}{Style.BRIGHT}{fw_name}{Style.RESET_ALL}: {count} ({percentage:.1f}%) {color}{distribution}{Style.RESET_ALL}")
            else:
                print(f"  {fw_name}: {count} ({percentage:.1f}%) {distribution}")
                
        # Print target details
        print("\nTarget Details:")
        
        # Calculate column widths
        url_width = max(len(target.get('url', '')) for target in aggregate_results.get('targets', []))
        url_width = min(60, max(10, url_width))  # Limit width between 10-60 chars
        
        # Print header
        header_format = f"  {'Target URL':<{url_width}} | {'Framework':<15} | {'Confidence':<20} | {'Time':<8} | {'FWs':<3} | {'Comps':<5}"
        print(header_format)
        print(f"  {'-' * url_width}-+-{'-' * 15}-+-{'-' * 20}-+-{'-' * 8}-+-{'-' * 3}-+-{'-' * 5}")
        
        for target in aggregate_results.get('targets', []):
            # Get color for the framework
            fw_name = target.get('top_framework', 'Unknown')
            color = Fore.WHITE if not HAS_COLOR else getattr(Fore, FRAMEWORK_COLORS.get(fw_name, "WHITE").upper())
            confidence = target.get('confidence', 0)
            
            # Format confidence bar
            conf_bar = "█" * int(confidence / 5)  # 20 chars max
            conf_text = f"{confidence}% [{conf_bar}]"
            
            # Truncate URL if needed
            url = target.get('url', 'Unknown')
            if len(url) > url_width:
                url = url[:url_width-3] + "..."
                
            # Format line
            line = f"  {url:<{url_width}} | {fw_name:<15} | {conf_text:<20} | {target.get('scan_time', 0):.2f}s | {target.get('detected_frameworks', 0):<3} | {target.get('components', 0):<5}"
            
            if HAS_COLOR:
                # Apply color to framework name
                parts = line.split("|")
                parts[1] = f" {color}{fw_name:<15}{Style.RESET_ALL} "
                line = "|".join(parts)
                
            print(line)
            
        # Add recommendations
        if HAS_COLOR:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}Recommendations:{Style.RESET_ALL}")
        else:
            print("\nRecommendations:")
            
        # Identify most common framework
        most_common_fw = max(framework_counts.items(), key=lambda x: x[1])[0] if framework_counts else "Unknown"
        color = Fore.WHITE if not HAS_COLOR else getattr(Fore, FRAMEWORK_COLORS.get(most_common_fw, "WHITE").upper())
        
        if HAS_COLOR:
            print(f"  • Most common framework detected: {color}{Style.BRIGHT}{most_common_fw}{Style.RESET_ALL}")
        else:
            print(f"  • Most common framework detected: {most_common_fw}")
            
        if target_count > 10:
            if HAS_COLOR:
                print(f"  • {Fore.GREEN}Large-scale scan - consider using automated tools for deeper analysis{Style.RESET_ALL}")
            else:
                print(f"  • Large-scale scan - consider using automated tools for deeper analysis")
                
        if len(framework_counts) > 3:
            if HAS_COLOR:
                print(f"  • {Fore.YELLOW}Diverse framework usage detected - consider targeting specific framework families{Style.RESET_ALL}")
            else:
                print(f"  • Diverse framework usage detected - consider targeting specific framework families")
