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


class ContentEngine(BaseEngine):
    """Engine for analyzing page content for framework fingerprints"""
    
    def analyze(self) -> None:
        """Run content analysis"""
        self._analyze_html_content()
        
    def _analyze_html_content(self) -> None:
        """Analyze HTML content for framework indicators"""
        response = self.request_manager.make_request()
        if not response or not response.text:
            return
            
        content = response.text.lower()
        
        # Look for Django indicators
        if 'csrfmiddlewaretoken' in content:
            self._add_score('Django', 5, 'Content', "CSRF middleware token found in HTML")
            
        if 'django' in content:
            self._add_score('Django', 2, 'Content', "Django reference in HTML")
            
        # Look for Flask indicators
        if 'flask' in content:
            self._add_score('Flask', 2, 'Content', "Flask reference in HTML")