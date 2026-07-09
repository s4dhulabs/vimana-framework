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

from helpers.vmnf_helpers import VimanaHelp
from res.vmnf_banners import s4dhu0nv1m4n4

require_module = [
    'args', 'run', 'info', 'guide'
]

# Command registry - maps command names to their help identifiers
vmnf_cmds = {
    'about' :  'about',
    'create':  'guide',  
    'args'  :  'args',
    'guide' :  'guide',
    'flush' :  'flush',
    'dbops' :  'dbops',
    'info'  :  'info',
    'list'  :  'list',
    'load'  :  'load',
    'run'   :  'run',
    'start' :  'start',
    'show'  :  'show',
    'help'  :  'help'
}

def get_command_help_text(command_name: str) -> str:
    """
    Get help text for a command using the new unified interface.
    
    Args:
        command_name: Name of the command to get help for
        
    Returns:
        Help text as a string
    """
    if command_name == 'about':
        return get_comprehensive_about_info()
    
    help_identifier = vmnf_cmds.get(command_name)
    if help_identifier:
        return VimanaHelp.get_command_help(help_identifier)
    
    return f"Help not available for command: {command_name}"

def get_comprehensive_about_info() -> str:
    """
    Generate comprehensive about information for Vimana Framework.
    Returns:
        Formatted about information as a string
    """
    from core._version import get_version_info, FRAMEWORK_NAME, FRAMEWORK_AUTHOR, FRAMEWORK_EMAIL, FRAMEWORK_URL
    import platform
    import sys
    import os
    from datetime import datetime

    BOX_WIDTH = 80
    def box_line(content='', width=BOX_WIDTH):
        # Pads content to fit inside box borders
        content = content[:width-4]  # truncate if too long
        return f"║ {content}{' ' * (width - 3 - len(content))}║"
    def box_title(title, width=BOX_WIDTH):
        t = f" {title} "
        return f"╠{t.center(width-2,'═')}╣"
    def box_top(width=BOX_WIDTH):
        return f"╔{'═'*(width-2)}╗"
    def box_bottom(width=BOX_WIDTH):
        return f"╚{'═'*(width-2)}╝"
    def box_empty(width=BOX_WIDTH):
        return box_line('', width)

    # Get version information
    version_info = get_version_info()
    # Get system information
    system_info = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': version_info['python_version'],
        'python_implementation': version_info['python_implementation'],
        'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'working_directory': os.getcwd()
    }
    # Framework capabilities
    capabilities = [
        "Vulnerability Detection & Exploitation",
        "Static & Dynamic Analysis", 
        "Application Crawling & Discovery",
        "Persistence & Post-Exploitation",
        "CI/CD Security Integration",
        "Plugin-Based Architecture",
        "Automated & Manual Testing",
        "Multi-Framework Support"
    ]
    # Centered VIMANA logo (ASCII art, 7 lines)
    vimana_logo = [
        r"██╗   ██╗██╗███╗   ███╗ █████╗ ███╗   ██╗ █████╗",
        r"██║   ██║██║████╗ ████║██╔══██╗████╗  ██║██╔══██╗",
        r"██║   ██║██║██╔████╔██║███████║██╔██╗ ██║███████║",
        r"╚██╗ ██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║",
        r" ╚████╔╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║",
        r"  ╚═══╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝",
        r"",
        r"                 SECURITY FRAMEWORK"
    ]
    logo_box = [box_top()] + [box_line('', BOX_WIDTH)]
    for line in vimana_logo:
        logo_box.append(box_line(line.center(BOX_WIDTH-4), BOX_WIDTH))
    logo_box.append(box_line('', BOX_WIDTH))
    logo_box.append(box_bottom())
    banner = '\n'.join(logo_box)

    # Version information section
    version_lines = [
        box_top(),
        box_title('VERSION INFORMATION'),
        box_line(f"Framework Version: {version_info['version']}", BOX_WIDTH),
        box_line(f"Version Type:     {'Development' if version_info['is_development'] else 'Release'}", BOX_WIDTH),
        box_line(f"Git Version:      {version_info['git_version'] or 'Not available'}", BOX_WIDTH),
        box_line(f"Python Version:   {version_info['python_version']}", BOX_WIDTH),
        box_line(f"Python Impl:      {version_info['python_implementation']}", BOX_WIDTH),
        box_bottom()
    ]
    version_section = '\n'.join(version_lines)

    # System information section
    system_lines = [
        box_top(),
        box_title('SYSTEM INFORMATION'),
        box_line(f"Platform:         {system_info['platform']}", BOX_WIDTH),
        box_line(f"Architecture:     {system_info['architecture']}", BOX_WIDTH),
        box_line(f"Processor:        {system_info['processor']}", BOX_WIDTH),
        box_line(f"Current Time:     {system_info['current_time']}", BOX_WIDTH),
        box_line(f"Working Dir:      {system_info['working_directory']}", BOX_WIDTH),
        box_bottom()
    ]
    system_section = '\n'.join(system_lines)

    # Framework description
    description_lines = [
        box_top(),
        box_title('FRAMEWORK OVERVIEW'),
        box_empty(),
        box_line("Vimana is a modular security framework for auditing Python web applications.", BOX_WIDTH),
        box_line("The plugin-based architecture enables security professionals to assess,", BOX_WIDTH),
        box_line("fuzz, and analyze Python projects through automated and manual techniques.", BOX_WIDTH),
        box_empty(),
        box_line("The framework provides comprehensive security testing capabilities including:", BOX_WIDTH),
        box_line("vulnerability detection, static and dynamic analysis, application crawling,", BOX_WIDTH),
        box_line("persistence analysis, and CI/CD integration.", BOX_WIDTH),
        box_empty(),
        box_bottom()
    ]
    description_section = '\n'.join(description_lines)

    # Capabilities section
    capabilities_lines = [box_top(), box_title('CORE CAPABILITIES')]
    for cap in capabilities:
        capabilities_lines.append(box_line(f"• {cap}", BOX_WIDTH))
    capabilities_lines.append(box_bottom())
    capabilities_section = '\n'.join(capabilities_lines)

    # Contact information
    contact_lines = [
        box_top(),
        box_title('CONTACT INFORMATION'),
        box_line(f"Author:           {FRAMEWORK_AUTHOR}", BOX_WIDTH),
        box_line(f"Email:            {FRAMEWORK_EMAIL}", BOX_WIDTH),
        box_line(f"Repository:       {FRAMEWORK_URL}", BOX_WIDTH),
        box_line(f"Documentation:    https://github.com/s4dhulabs/vimana-framework/docs", BOX_WIDTH),
        box_bottom()
    ]
    contact_section = '\n'.join(contact_lines)

    # Quick start section
    quick_start_lines = [
        box_top(),
        box_title('QUICK START'),
        box_empty(),
        box_line("• List available plugins:     vimana list --plugins", BOX_WIDTH),
        box_line("• Run a security scan:        vimana run <plugin> --target <url>", BOX_WIDTH),
        box_line("• Show plugin information:    vimana info --plugin <name>", BOX_WIDTH),
        box_line("• Get usage examples:         vimana guide --plugin <name>", BOX_WIDTH),
        box_line("• Start interactive mode:     vimana start", BOX_WIDTH),
        box_empty(),
        box_bottom()
    ]
    quick_start_section = '\n'.join(quick_start_lines)

    # Combine all sections
    about_info = (
        banner + '\n' +
        version_section + '\n' +
        system_section + '\n' +
        description_section + '\n' +
        capabilities_section + '\n' +
        contact_section + '\n' +
        quick_start_section
    )
    return about_info

class vfasserts:
    def __init__(self, **_vfh_):
        self._vfh_ = _vfh_

    def tactical_mode(self):
        return False if (
            not self._vfh_['session_mode'] \
            and not self._vfh_['request_data_set'] \
            and not self._vfh_['apispec_enabled'] \
            and not self._vfh_['inspect'] \
            and not self._vfh_['listener_mode'] \
            and not self._vfh_['auth_mode'] \
            and not self._vfh_['target_url'] \
            and not self._vfh_['rule_scan'] \
            and not self._vfh_['framework_search_version'] \
            and not self._vfh_['list_specs'] \
            and not self._vfh_['flush_specs'] \
            and not self._vfh_['flush_spec'] \
            and not self._vfh_['fuzzerspec_enabled'] \
            and not self._vfh_['create_env'] \
            and not self._vfh_['load_from_env'] \
            and not self._vfh_['api_scan_enabled'] \
            and not self._vfh_['ws_audit_enabled'] \
            and not self._vfh_['stream_audit_enabled'] \
            and not self._vfh_['stream_path'] \
            and not self._vfh_['openapi_spec_file'] \
            and not self._vfh_['openapi_spec_url'] \
        ) else True

    def default_guide_mode(self):
        return True if (
            not self._vfh_['guide_examples'] \
            and not self._vfh_['guide_args'] \
            and not self._vfh_['guide_labs']
        ) else False

    def is_target_set(self):
        return True if (
            self._vfh_['single_target'] \
            or self._vfh_['file_scope'] \
            or self._vfh_['ip_range'] \
            or self._vfh_['cidr_range'] \
            or self._vfh_['list_target'] 
        ) else False

    def version_search(self):
        return True if (
            self._vfh_['django_version'] \
            or self._vfh_['flask_version'] \
            or self._vfh_['tornado_version'] \
            or self._vfh_['web2py_version']
        ) else False

    def exec_enabled(self):
        return True if (
            self._vfh_['save_case'] \
            and self._vfh_['exec_case'] 
            ) else False
    
    def vfr_run(self):
        return True if (
            self._vfh_['module_run'] \
            or self._vfh_['plugin_run'] \
            or self._vfh_['siddhi_run'] 
        ) else False
    
    def plugin_payload_set(self):
        return True if (
            self._vfh_['module_run']) \
            and (self._vfh_['flask_pinstealer'] \
            or self._vfh_['flask_consolehook'] \
            or self._vfh_['connect_back'] 
        ) else False

    '''
    ** to support future changes

    def get_run_option(self):
        return [v for k,v in self._vfh_.items() \
                if k in ['G','J', 'L']][0]
    '''
