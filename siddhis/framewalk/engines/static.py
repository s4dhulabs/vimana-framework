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

from typing import Dict, List, Any, Optional

from .base import BaseEngine


class StaticResourceEngine(BaseEngine):
    """Engine for analyzing static resources for framework fingerprints"""
    
    def analyze(self) -> None:
        """Run static resource analysis"""
        self._check_common_static_paths()
        
    def _check_common_static_paths(self) -> None:
        """Check common static file paths"""
        common_paths = [
            '/static/',
            '/admin/static/',
            '/assets/',
        ]
        
        for path in common_paths:
            response = self.request_manager.make_request(path)
            if not response:
                continue
                
            if response.status_code == 200:
                # Django static files
                if path == '/static/' or path == '/admin/static/':
                    self._add_score('Django', 3, 'Static', f"Static directory found: {path}")