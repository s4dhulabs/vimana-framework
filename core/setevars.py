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
import json
from pathlib import Path

def set_vimana_path(vimana_path):
    """
    Store Vimana installation path in a simple config file.
    This approach is more reliable than modifying shell configs.
    """
    # Use user's home directory for config
    config_dir = Path.home() / '.vimana'
    config_file = config_dir / 'config.json'
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)
    
    # Load existing config or create new one
    config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            config = {}
    
    # Update the path
    config['vimana_path'] = str(vimana_path)
    config['last_updated'] = str(Path(vimana_path).stat().st_mtime)
    
    # Save config
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Also set for current session
    os.environ['VIMANA_PATH'] = str(vimana_path)
    
    return str(vimana_path)

def get_vimana_path():
    """
    Get Vimana installation path from config file or environment.
    """
    # First try environment variable
    if 'VIMANA_PATH' in os.environ:
        return os.environ['VIMANA_PATH']
    
    # Try config file
    config_file = Path.home() / '.vimana' / 'config.json'
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('vimana_path')
        except (json.JSONDecodeError, IOError):
            pass
    
    # Fallback: try to detect from current file location
    current_file = Path(__file__).resolve()
    if 'vimana' in current_file.parts:
        # Go up until we find the vimana root
        for parent in current_file.parents:
            if (parent / 'vimana.py').exists() or (parent / 'core').exists():
                return str(parent)
    
    return None


