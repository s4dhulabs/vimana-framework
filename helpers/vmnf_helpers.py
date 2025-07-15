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
from res.colors import *
from random import choice
from res.vmnf_banners import s4dhu0nv1m4n4,vmn05,default_naviban,sample_mode
from neotermcolor import colored, cprint
from core.load_settings import _version_


class VimanaHelp:
    ''' '''
    def __init__(self):
        """
        Vimana Framework {0}
        
        Usage: vimana <command> [options]

        Commands:
            about   Framework information and version
            create  Create new resources (env, vars, creds)
            flush   Remove recorded resources
            guide   Show plugin usage examples and arguments
            help    Display comprehensive help for all commands
            info    Show detailed plugin information
            list    List available resources
            load    Load recorded sessions
            run     Execute plugins, cases, or workflows
            show    Display detailed resource information
            start   Start interactive mode

        Run 'vimana <command> --help' for command-specific help.
        """
        
    def overview(self):
        ovw = {
            'about' : "Framework information and version",
            'create': "Create new resources (env, vars, creds)",
            'flush' : "Remove recorded resources", 
            'dbops' : "Database operations and maintenance",
            'guide' : "Show plugin usage examples and arguments",
            'help'  : "Display comprehensive help for all commands",
            'info'  : "Show detailed plugin information",
            'list'  : "List available resources",
            'load'  : "Load recorded sessions",
            'run'   : "Execute plugins, cases, or workflows",
            'show'  : "Display detailed resource information",
            'start' : "Start interactive mode",
        }
        
        cmd_color = 77  
        separator_color = 79 
        
        for cmd, desc in ovw.items():
            print("{:>25} {} {}".format(
                colored(cmd, cmd_color),
                colored('•', separator_color, attrs=['bold']), 
                colored(desc, None)
            ))
        print('\n')

    def proxy(self):
        '''
        [proxy] 

        --set-proxy         Enable the default proxy for all requests: SOCKS5://127.0.0.1:9050
        --proxy             Configure the proxy specified by the ip:port string 
        --proxy-type        Specify the proxy protocol to be used: SOCKS4, SOCKS5, HTTP (required --proxy option)
        '''

    def about(self):
        s4dhu0nv1m4n4()

    def help(self):
        '''
        [ help ]

        Display comprehensive help for all Vimana Framework commands.

        Usage: vimana help
               vimana --help

        This command provides detailed information about all available
        commands, their usage patterns, and examples. It's equivalent
        to running the full help system.

        Examples:
        vimana help              # Display full help
        vimana --help            # Alternative syntax
        vimana help <command>    # Get help for specific command

        The help system includes:
        - Command overview and descriptions
        - Usage examples and syntax
        - Argument explanations
        - Best practices and tips
        '''

    def set_scope(self):
        '''
    [ target settings ]

    Options to define target scope for security testing:

    Single target:
        --target             Single target IP/URL
        --target-url         Single target IP/URL (alternative)

    Multiple targets:
        --target-list        Comma-separated list of targets
        --file               File containing list of targets (one per line)
        --ip-range           Range of target IPs (e.g., 192.168.1.1-192.168.1.254)
        --cidr-range         CIDR range of targets (e.g., 192.168.1.0/24)
       
    [ port settings ]

    Options to define port scope for testing:

        --port               Single port number
        --port-list          Comma-separated list of ports
        --port-range         Range of ports (e.g., 8000-8010)
        --ignore-state       Skip target reachability verification
        '''

    def save_case(self):
        '''

    [ save_case ]
      
    Save current command as a reusable test case.

    Usage: vimana run <plugin> [options] --save-case <case_name>

    Benefits:
    - Reuse complex command configurations
    - Share test scenarios with team members
    - Maintain testing consistency
    - Avoid command line history pollution

    Examples:

    Save a basic test case:
    vimana run dmt \\
        --target-url http://target.com:8000 \\
        --save-case django_basic_test

    Save a comprehensive test case:
    vimana run dmt \\
        --target-list target1.com,target2.com \\
        --port-list 8000,8001,8002 \\
        --debug \\
        --threads 10 \\
        --save-case multi_target_audit

    Save and execute immediately:
    vimana run dmt \\
        --target-url http://target.com:8000 \\
        --save-case quick_test \\
        --exec-case

    Case execution:
    vimana run <case_name>          # Execute saved case
    vimana run --case <case_name>   # Alternative syntax
        '''

    def abduct(self):
        '''

    [ abduct ]

    Execute analysis from a YAML configuration file.

    Usage: vimana run --abduct <config_file.yaml>

    This option allows you to perform complex analyses using predefined
    configurations stored in YAML files. Useful for:
    - Standardized testing procedures
    - Complex multi-step workflows
    - Reproducible security assessments
    - Team collaboration scenarios

    Example:
    vimana run --abduct my_workflow.yaml

    Configuration files should follow the Vimana workflow format.
        '''
    
    def general_options(self):
        '''
    [ general settings ]

    Global options for controlling plugin behavior:

    Output control:
        --debug              Enable debug mode with detailed output
        --verbose            Enable verbose mode (incremental levels)
        --auto               Auto-confirm prompts and continue on errors

    Execution control:
        --threads            Number of concurrent threads (default: 3)
        --timeout            HTTP request timeout in seconds (default: 5)
        --wait               Delay between requests in seconds
        --pause-steps        Pause between test steps for manual review

    Behavior control:
        --random             Enable random mode for supported tasks
        --exit-on-trigger    Stop execution on first finding
        --disable-external   Disable external lookups (CVE, etc.)
        --disable-cache      Disable caching mechanisms
        '''

    def fuzzer_args(self):
        '''

    [ fuzzer arguments ]

    Options specific to fuzzing and testing tools:

    URL configuration:
        --urlconf            Path to URL configuration file (urls.py)
        --patterns           File containing custom URL patterns
        --view-name          Filter testing scope by specific view name

    Testing scope:
        --methods            HTTP methods to test (GET, POST, PUT, etc.)
        --fuzzspecs          Custom fuzzing specifications file
        --custom-variations  Custom test variations file

    Advanced options:
        --set-parameter      Set specific parameter for testing
        --set-param          Alternative syntax for parameter setting
        --form-input-target  Target specific form inputs
        '''

    def args(self):
        '''
    [ args ]

    Show detailed plugin arguments and options.

    Usage: vimana args --module <plugin_name>
           vimana args --plugin <plugin_name>
           vimana args --siddhi <plugin_name>

    This command displays all available arguments, options, and their
    descriptions for a specific plugin. Useful for understanding
    plugin capabilities and required parameters.

    Examples:
    vimana args --module dmt
    vimana args --plugin jcolt
    vimana args --siddhi pyserial

    Note: --module, --plugin, and --siddhi are interchangeable.
        '''

    def guide(self):
        '''

    [ guide ]

    Show plugin usage examples and documentation.

    Usage: vimana guide --plugin <plugin_name> [options]
    
    Options:
    --args, -a      Show plugin arguments and options
    --examples, -e  Show usage examples
    --labs, -l      Show lab setup instructions

    Examples:

    Show complete plugin guide:
    vimana guide --plugin dmt
    vimana guide -p dmt

    Show plugin arguments:
    vimana guide --plugin dmt --args
    vimana guide -p dmt -a

    Show usage examples:
    vimana guide --plugin dmt --examples
    vimana guide -p dmt -e

    Show lab setup:
    vimana guide --plugin dmt --labs
    vimana guide -p dmt -l

        '''

    def start(self): 
        '''
    [ start ]
    
    Start Vimana in interactive mode.

    Usage: vimana start

    Interactive mode provides a step-by-step interface for:
    - Configuring plugin parameters
    - Setting target scope
    - Defining execution options
    - Running security assessments

    This mode is ideal for:
    - Learning plugin capabilities
    - Complex multi-step configurations
    - Guided security testing workflows
    - Interactive exploration of targets

    All required and optional parameters are configured
    interactively before execution begins.
        '''
        
    def info(self): 
        '''
    [ info ]
    
    Show detailed information about a plugin.

    Usage: vimana info --siddhi <plugin_name>
           vimana info --module <plugin_name>
           vimana info --plugin <plugin_name>

    Displays comprehensive plugin information including:
        
        * Description and capabilities
        * Author and version information
        * Testing type (DAST/SAST)
        * Category and framework support
        * Associated CWE identifiers
        * Security tags and classifications
        * Composition and dependencies

    Examples:
    
    vimana info --siddhi dmt
    vimana info --module jcolt
    vimana info --plugin pyserial

    Note: --siddhi, --module, and --plugin are interchangeable.
        '''
    
    def show(self):
        '''
    [ show ]
    
    Show detailed information about Vimana resources.

    Usage: vimana show <resource_type> <identifier> [options]

    Available resources:
    --channel <id>           Show exploitation channel details
    --session <id>           Show analysis session details
    --case <name>            Show test case configuration

    Channel display options:
    --compact	            Show channel details in compact format

    Examples:
        
    Show channel details:
    vimana show --channel abc12345
    vimana show --channel abc12345 --compact

    Show session information:
    vimana show --session 2720b71be1

    Show case configuration:
    vimana show --case django_audit_case

    Compact mode provides:
    - No screen clearing
    - Truncated JSON fields
    - Essential information only
    - Better for terminal integration
        '''
    
    def flush(self): 
        '''
    [ flush ]
    
    Remove recorded resources from the database.

    Usage: vimana flush <resource_type> [identifier]

    Available resources:
    --sessions               Remove all analysis sessions
    --session <id>           Remove specific session by ID
    --cases                  Remove all test cases
    --case <name>            Remove specific case by name
    --channels               Remove all exploitation channels
    --channel <id>           Remove specific channel by ID
    --scans                  Remove all scan results

    Examples:
        
    Remove specific resources:
    vimana flush --session 2720b71be1
    vimana flush --case django_audit_case
    vimana flush --channel abc12345

    Remove all resources of a type:
    vimana flush --sessions
    vimana flush --cases
    vimana flush --channels

    Warning: These operations are irreversible.
    Use with caution, especially when removing all resources.
        '''
   
    def load(self):
        ''' 
    [ load ]

    Load recorded resources and plugins.
    
    Usage: vimana load <resource_type> [identifier]

    Available resources:
    --plugins                 Load all available plugins (initial setup)
    --session <id>            Load specific analysis session by ID
    --case <name>             Load specific test case by name

    Examples:
    
    Load plugins during initial setup:
    vimana load --plugins 
    
    Load specific session:
    vimana load --session 4a0a5a8c99
    
    Load specific case:
    vimana load --case django_audit_case

    Loading sessions provides access to:
    - Previous analysis results
    - Discovered vulnerabilities
    - Configuration settings
    - Execution history

    Loading cases provides access to:
    - Saved test configurations
    - Target definitions
    - Plugin parameters
    - Execution options
        '''

    def list(self):
        '''
    [list]
   
    List available resources in the Vimana Framework.

    Usage: vimana list <resource_type> [filters]

    Available resources:
    --plugins	    List all available security testing plugins
    --sessions	    List all recorded analysis sessions
    --cases	    List all saved test cases
    --scans	    List all completed security scans
    --channels	    List all exploitation channels
    --payloads	    List available attack payloads

    Plugin filtering options:

    --framework	    Filter by target framework:
		    ‣  Django
		    ‣  Flask
		    ‣  FastAPI
		    ‣  Python
		    ‣  Generic
		    ‣  All

    --category	    Filter by plugin category:
		    ‣  Audit
		    ‣  Discovery
		    ‣  Exploit
		    ‣  Fingerprint
		    ‣  Framework
		    ‣  Fuzzer
		    ‣  Persistence
		    ‣  Parser
		    ‣  Tracker

    --type	    Filter by testing methodology:
		    ‣  DAST (Dynamic Application Security Testing)
		    ‣  SAST (Static Application Security Testing)

    Display options:
    -ft,--fancy-table       Use fancy grid table format

    Examples:

    List all DAST plugins for Django:
    vimana list --plugins --type DAST --framework Django

    List all fuzzer plugins:
    vimana list --plugins --category Fuzzer

    List all audit plugins:
    vimana list --plugins --category Audit

    Channel management:

    --summary	            Show channels in compact summary format
    --channel-type	    Filter by vulnerability type (RCE, File Write, etc.)
    --channel-plugin	    Filter by discovering plugin
    --channel-target	    Filter by target URL
    --channel-status	    Filter by status (active, verified, etc.)

    Examples:

    List all channels in summary format:
    vimana list --channels --summary

    List RCE channels from pyserial:
    vimana list --channels --channel-type RCE --channel-plugin pyserial
        '''
    
    def run(self):
        '''
    [ run ]
    
    Execute plugins, cases, commands or workflows.
    
    Usage: vimana run <plugin_name> [options]
           vimana run --case <case_name>
           vimana run <workflow_name>
           vimana run --cmd <command> --channel <channel_id>

    Examples:

    > Plugins
    Run viewscan against a target project's directory (SAST: Scan Django Views):
    vimana run viewscan --project-dir mydjangop_project

    Run jcolt plugin against a target API (DAST: Scan a FastAPI application):
    vimana run jcolt --scan-api http://myfastapitarget.com

    Run a plugin with basic options (DAST: Django Audit):
    vimana run dmt --target-url http://target.com:8000

    Run with advanced options:
    vimana run dmt \\
        --target-url http://target.com:8000 \\
        --disable-external \\
        --exit-on-trigger \\
        --debug \\
        --auto

    > Commands
    Run ID command in the target channel 882fceec 
    vimana run --cmd 'id' --channel 882fceec

    > Cases
    vimana run !               # Execute last case
    vimana run --case djapp8   # Execute specific case
    vimana run djapp8          # Execute case by name
    vimana run @cf12           # Execute case by ID

    Note: --plugin, --siddhi, and --module are interchangeable.
    Use `vimana guide --plugin <name> --args` for detailed options.
        '''

    def basic_help(self):
        #vmn05()
        os.system('clear')
        sample_mode('')
        self.overview()

    def dbops(self):
        '''
        [ dbops ]

        Database operations and maintenance.

        Usage: vimana dbops [options]

        Options:
            --reset           Reset and clean the Vimana Framework database (dangerous!)
            --list            List all tables and their columns/types in the database
            --integrity-check Run a database integrity check (SQLite supported)

        Examples:

        vimana dbops --reset            # Clean and reset the database
        vimana dbops --list             # Show all tables and their structure
        vimana dbops --integrity-check  # Run a database integrity check

        This command is intended for advanced users and administrators.
        More options will be added in future versions.
        '''

    @staticmethod
    def full_help():
        print("\033c", end="") 
        print(VimanaHelp().__doc__.format(_version_))
        help_instance = VimanaHelp()
        help_instance.overview()
        print(    
            #help_instance.overview.__doc__,
            help_instance.start.__doc__,
            help_instance.list.__doc__,
            help_instance.run.__doc__,
            help_instance.info.__doc__,
            help_instance.show.__doc__,
            help_instance.set_scope.__doc__,
            help_instance.general_options.__doc__
        )
    
    @staticmethod
    def get_command_help(command_name: str) -> str:
        """
        Get help text for a specific command.
        
        Args:
            command_name: Name of the command to get help for
            
        Returns:
            Help text as a string
        """
        help_methods = {
            'start': VimanaHelp._get_start_help,
            'list': VimanaHelp._get_list_help,
            'run': VimanaHelp._get_run_help,
            'info': VimanaHelp._get_info_help,
            'show': VimanaHelp._get_show_help,
            'flush': VimanaHelp._get_flush_help,
            'dbops': VimanaHelp._get_dbops_help,
            'load': VimanaHelp._get_load_help,
            'guide': VimanaHelp._get_guide_help,
            'help': VimanaHelp._get_help_help,
            'args': VimanaHelp._get_args_help,
            'about': VimanaHelp._get_about_help,
            'set_scope': VimanaHelp._get_scope_help,
            'general_options': VimanaHelp._get_general_options_help,
            'save_case': VimanaHelp._get_save_case_help,
            'abduct': VimanaHelp._get_abduct_help,
            'fuzzer_args': VimanaHelp._get_fuzzer_args_help,
        }
        
        if command_name == 'help':
            return VimanaHelp._get_full_help()
        
        method = help_methods.get(command_name)
        return method() if method else f"Help not available for command: {command_name}"
    
    @staticmethod
    def _get_full_help() -> str:
        """Get complete help text as a string"""
        return f"""{VimanaHelp().__doc__.format(_version_)}

{VimanaHelp._get_overview()}

{VimanaHelp._get_start_help()}
{VimanaHelp._get_list_help()}
{VimanaHelp._get_run_help()}
{VimanaHelp._get_info_help()}
{VimanaHelp._get_show_help()}
{VimanaHelp._get_scope_help()}
{VimanaHelp._get_general_options_help()}"""
    
    @staticmethod
    def _get_overview() -> str:
        """Get command overview as a string"""
        return """
Command Overview:
  about  - Framework information and version
  create - Create new resources (env, vars, creds)
  flush  - Remove recorded resources
  dbops  - Database operations and maintenance
  guide  - Show plugin usage examples and arguments
  help   - Display comprehensive help for all commands
  info   - Show detailed plugin information
  list   - List available resources
  load   - Load recorded sessions
  run    - Execute plugins, cases, or workflows
  show   - Display detailed resource information
  start  - Start interactive mode
"""
    
    @staticmethod
    def _get_about_help() -> str:
        """Get about help text"""
        return """
[ about ]

Display comprehensive framework information including version details,
capabilities, and system information. Use 'vimana about' to view
complete framework overview and current installation details.
"""

    @staticmethod
    def _get_help_help() -> str:
        """Get help help text"""
        return """
[ help ]

Display comprehensive help for all Vimana Framework commands.

Usage: vimana help
       vimana --help

This command provides detailed information about all available
commands, their usage patterns, and examples. It's equivalent
to running the full help system.

Examples:
vimana help              # Display full help
vimana --help            # Alternative syntax
vimana help <command>    # Get help for specific command

The help system includes:
- Command overview and descriptions
- Usage examples and syntax
- Argument explanations
- Best practices and tips
"""
    
    @staticmethod
    def _get_start_help() -> str:
        """Get start command help text"""
        return VimanaHelp().start.__doc__
    
    @staticmethod
    def _get_list_help() -> str:
        """Get list command help text"""
        return VimanaHelp().list.__doc__
    
    @staticmethod
    def _get_run_help() -> str:
        """Get run command help text"""
        return VimanaHelp().run.__doc__
    
    @staticmethod
    def _get_info_help() -> str:
        """Get info command help text"""
        return VimanaHelp().info.__doc__
    
    @staticmethod
    def _get_show_help() -> str:
        """Get show command help text"""
        return VimanaHelp().show.__doc__
    
    @staticmethod
    def _get_flush_help() -> str:
        """Get flush command help text"""
        return VimanaHelp().flush.__doc__
    
    @staticmethod
    def _get_load_help() -> str:
        """Get load command help text"""
        return VimanaHelp().load.__doc__
    
    @staticmethod
    def _get_guide_help() -> str:
        """Get guide command help text"""
        return VimanaHelp().guide.__doc__
    
    @staticmethod
    def _get_args_help() -> str:
        """Get args command help text"""
        return VimanaHelp().args.__doc__
    
    @staticmethod
    def _get_scope_help() -> str:
        """Get scope settings help text"""
        return VimanaHelp().set_scope.__doc__
    
    @staticmethod
    def _get_general_options_help() -> str:
        """Get general options help text"""
        return VimanaHelp().general_options.__doc__
    
    @staticmethod
    def _get_save_case_help() -> str:
        """Get save_case help text"""
        return VimanaHelp().save_case.__doc__
    
    @staticmethod
    def _get_abduct_help() -> str:
        """Get abduct help text"""
        return VimanaHelp().abduct.__doc__
    
    @staticmethod
    def _get_fuzzer_args_help() -> str:
        """Get fuzzer arguments help text"""
        return VimanaHelp().fuzzer_args.__doc__

    @staticmethod
    def _get_dbops_help() -> str:
        """Get dbops help text"""
        return """
    [ dbops ]

    Database operations and maintenance.

    Usage: vimana dbops [options]

    Options:
        --reset           Reset and clean the Vimana Framework database (dangerous!)
        --list            List all tables and their columns/types in the database
        --integrity-check Run a database integrity check (SQLite supported)

    Examples:
    vimana dbops --reset            # Clean and reset the database
    vimana dbops --list             # Show all tables and their structure
    vimana dbops --integrity-check  # Run a database integrity check

    This command is intended for advanced users and administrators.
    More options will be added in future versions.
"""
        
