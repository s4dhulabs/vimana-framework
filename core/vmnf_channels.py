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
from core._dbops_.vmnf_dbops import VFDBOps
from core._dbops_.database import db
from core._dbops_.models.channels import VFChannels
from neotermcolor import colored, cprint
from tabulate import tabulate
from datetime import datetime
from res.vmnf_banners import default_naviban,sample_mode
import json
import ast
import sys
from core._dbops_.vmnf_dbops import VFDBOps
from neotermcolor import colored as cl

def _format_json_field(value, field_name, compact=False):
    """Helper function to format JSON fields with syntax highlighting"""
    if not value:
        if not compact:
            print(f'{field_name}: (empty)')
        return
    
    if isinstance(value, (dict, list)):
        formatted_str = json.dumps(value, indent=2, ensure_ascii=False)
    elif isinstance(value, str) and value.strip().startswith('{') and value.strip().endswith('}'):
        try:
            parsed_dict = ast.literal_eval(value)
            formatted_str = json.dumps(parsed_dict, indent=2, ensure_ascii=False)
        except Exception:
            formatted_str = str(value)
    else:
        formatted_str = str(value)
    
    if compact and len(formatted_str) > 100:
        formatted_str = formatted_str[:97] + "..."
    
    print(f'{field_name}:')
    try:
        from pygments import highlight
        from pygments.lexers import JsonLexer
        from pygments.formatters import TerminalFormatter
        print(highlight(formatted_str, JsonLexer(), TerminalFormatter()))
    except ImportError:
        print(formatted_str)

def list_channels(channels=None, summary=False):
    if channels is None:
        db = VFDBOps()
        channels = db.getall('_CHANNELS_')
    
    if not channels:
        print(colored('No channels found.', 'yellow'))
        return
    
    if summary:
        # Compact summary view
        print(colored(f'Found {len(channels)} channels:', 'cyan', attrs=['bold']))
        print()
        for ch in channels:
            status_color = 'red' if ch.status == 'active' else 'green'
            print(f"{colored(ch.channel_id, 'cyan')} | {colored(ch.type, 'yellow')} | {colored(ch.plugin, 'green')} | {colored(ch.status, status_color)}")
        return
    
    # Full table view
    table = []
    for ch in channels:
        table.append([
            ch.channel_id,
            ch.type,
            ch.plugin,
            ch.target_url,
            ch.endpoint,
            ch.method,
            ch.status,
            ch.created_at.strftime('%Y-%m-%d %H:%M') if ch.created_at else '',
        ])
    headers = ['ID', 'Type', 'Plugin', 'Target', 'Endpoint', 'Method', 'Status', 'Created']
    print(tabulate(table, headers=headers, tablefmt='fancy_grid'))

def show_channel(channel_id, compact=False):
    db = VFDBOps()
    ch = db.get_by_id('_CHANNELS_', 'channel_id', channel_id)
    if not ch:
        print(colored(f'Channel {channel_id} not found.', 'red'))
        return
    
    # Don't clear screen in test mode
    if not compact:
        print("\033c", end="")
        sample_mode('   channels')
        print()
        print()
    
    # Basic channel information with better formatting
    print(colored(f'Channel ID: {ch.channel_id}', 'cyan', attrs=['bold']))
    print(colored(f'Type: {ch.type}', 'yellow'))
    print(colored(f'Plugin: {ch.plugin}', 'green'))
    print(f'Target: {ch.target_url}')
    print(f'Endpoint: {ch.endpoint}')
    print(f'Method: {ch.method}')
    print(colored(f'Status: {ch.status}', 'red' if ch.status == 'active' else 'green'))
    
    if not compact:
        print(f'Created: {ch.created_at}')
        print(f'Last Verified: {ch.last_verified}')
    
    print()  # Add spacing before JSON fields
    
    # Format JSON fields using the helper function
    _format_json_field(ch.description, 'Description', compact)
    _format_json_field(ch.payload_template, 'Payload Template', compact)
    _format_json_field(ch.channel_metadata, 'Metadata', compact)

def _channel_quiet(quiet=None, handler=None) -> bool:
    """True when channel registration should stay silent (CI / orchestrator)."""
    if quiet is not None:
        return bool(quiet)
    if not handler:
        return False
    return bool(
        handler.get('ci_mode')
        or handler.get('json_output')
        or handler.get('quiet_output')
        or handler.get('no_metadata')
        or handler.get('_orchestrator')
    )


def register_channel(channel_data, *, quiet=None, handler=None):
    """
    Register a new exploitation channel in the Vimana database.

    quiet/handler: when CI/orchestrator quiet flags are set, suppress console output
    so JSON/SARIF stdout stays clean.

    Example usage from a plugin:
        from core.vmnf_channels import register_channel
        register_channel({
            'channel_id': 'dpo91992',
            'type': 'RCE',
            'plugin': 'pyserial',
            'target_url': 'http://localhost:8003',
            'endpoint': '/api/v1/media/attachments/decode',
            'method': 'POST',
            'payload_template': 'id && whoami && hostname',
            'description': 'Pickle RCE via custom test',
            'status': 'active',
            'metadata': {'lab': 'fastapi', 'vector': 'simple_command_execution'}
        }, handler=self.handler)
    """
    silent = _channel_quiet(quiet=quiet, handler=handler)
    data = dict(channel_data)

    # Rename metadata to channel_metadata if present
    if 'metadata' in data:
        data['channel_metadata'] = data.pop('metadata')

    db = VFDBOps(**data)
    # De-duplication: check if channel_id exists
    existing = db.get_by_id('_CHANNELS_', 'channel_id', data['channel_id'])
    if existing:
        if not silent:
            print(colored(f'Channel {data["channel_id"]} already exists. Skipping registration.', 'yellow'))
        return False
    db.register('_CHANNELS_')
    if not silent:
        print(colored(f'Channel {data["channel_id"]} registered.', 'green'))
        print(colored(f'Use: vimana show --channel {data["channel_id"]}', 'cyan'))
    return True

def flush_channel(channel_id):
    db = VFDBOps()
    result = db.flush_resource('_CHANNELS_', 'channel_id', channel_id)
    if result:
        print(colored(f'Channel {channel_id} deleted.', 'green'))
    else:
        print(colored(f'Channel {channel_id} not found.', 'red'))

def flush_all_channels():
    dbops = VFDBOps()
    result = dbops.clean_table('_CHANNELS_')
    if result:
        print(colored('All channels flushed.', 'green'))
    else:
        print(colored('Failed to flush channels.', 'red'))

def get_channels_by_type(channel_type):
    """Get all channels of a specific type (e.g., 'RCE', 'File Write')"""
    db = VFDBOps()
    channels = db.getall('_CHANNELS_')
    return [ch for ch in channels if ch.type == channel_type]

def get_channels_by_plugin(plugin_name):
    """Get all channels discovered by a specific plugin"""
    db = VFDBOps()
    channels = db.getall('_CHANNELS_')
    return [ch for ch in channels if ch.plugin == plugin_name]

def get_channels_by_target(target_url):
    """Get all channels for a specific target URL"""
    db = VFDBOps()
    channels = db.getall('_CHANNELS_')
    return [ch for ch in channels if ch.target_url == target_url]

def update_channel_status(channel_id, status='verified', metadata_update=None):
    """Update channel status and optionally metadata"""
    db = VFDBOps()
    channel = db.get_by_id('_CHANNELS_', 'channel_id', channel_id)
    if not channel:
        print(colored(f'Channel {channel_id} not found.', 'red'))
        return False
    
    channel.status = status
    channel.last_verified = datetime.utcnow()
    
    if metadata_update and channel.channel_metadata:
        channel.channel_metadata.update(metadata_update)
    
    db.session.commit()
    print(colored(f'Channel {channel_id} status updated to {status}.', 'green'))
    return True

def get_active_channels():
    """Get all active channels"""
    db = VFDBOps()
    channels = db.getall('_CHANNELS_')
    return [ch for ch in channels if ch.status == 'active'] 

def show_channels_summary():
    """Show a compact summary of all channels"""
    list_channels(summary=True) 

def run_command_in_channel(handler_ns):
    """
    Manage the logic for running a command in a channel:
    - Check channel existence
    - Show info
    - Confirm with user (unless auto)
    - Execute command using exploitation vector
    """
    channel_id = getattr(handler_ns, 'cmd_channel', None)
    if not channel_id:
        print(cl("No channel ID provided (--channel required).", "red"))
        sys.exit(1)

    db = VFDBOps()
    channel = db.get_by_id('_CHANNELS_', 'channel_id', channel_id)
    if not channel:
        print(cl(f"Channel {channel_id} not found in the database.", "red"))
        sys.exit(1)

    # Show basic info about the channel
    show_channel(channel_id, compact=True)

    # Confirm with user unless auto is enabled
    if not getattr(handler_ns, 'auto', False):
        confirm = input(f"\nDo you want to execute '{handler_ns.run_cmd}' on the target represented by channel {channel_id}? [y/N]: ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Command execution cancelled.")
            sys.exit(0)

    # Execute the command using the exploitation vector
    try:
        from core.vmnf_exploit_exec import execute_command_in_channel
        result = execute_command_in_channel(channel, handler_ns.run_cmd)
        print(result)
    except ImportError:
        print(cl("[ERROR] Exploit execution module not found.", "red"))
        sys.exit(1)
    except Exception as e:
        print(cl(f"[ERROR] Command execution failed: {e}", "red"))
        sys.exit(1)
    sys.exit(0) 