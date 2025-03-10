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


class PassiveEngine(BaseEngine):
    """Engine for passive analysis without making requests"""
    
    def analyze(self) -> None:
        """Run passive analysis"""
        self._analyze_url_structure()
        
    def _analyze_url_structure(self) -> None:
        """Analyze URL structure for framework hints"""
        target_url = self.request_manager.target_url
        
        # Look for common framework patterns in URL
        if '/django/' in target_url.lower():
            self._add_score('Django', 2, 'URL', "Django reference in URL path")
            
        if '/flask/' in target_url.lower():
            self._add_score('Flask', 2, 'URL', "Flask reference in URL path")
            
        if '/fastapi/' in target_url.lower():
            self._add_score('FastAPI', 2, 'URL', "FastAPI reference in URL path")