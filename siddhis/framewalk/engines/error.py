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

import json
from typing import Dict, List, Any, Optional

from .base import BaseEngine


class ErrorEngine(BaseEngine):
    """Engine for analyzing error responses for framework fingerprints"""
    
    def analyze(self) -> None:
        """Run error analysis"""
        self._analyze_404_page()
        
    def _analyze_404_page(self) -> None:
        """Analyze 404 page for framework indicators"""
        response = self.request_manager.make_request('/this_page_should_not_exist_fRmW4lKT&st')
        if not response:
            return
            
        status_code = response.status_code
        content = response.text.lower() if response.text else ""
        
        # Django patterns
        if ('page not found' in content and ('django' in content or status_code == 404)):
            self._add_score('Django', 10, '404 Page', "Django-style 404 page")
            
        # Flask patterns
        if ('not found' in content and ('werkzeug' in content or 'flask' in content)):
            self._add_score('Flask', 10, '404 Page', "Flask/Werkzeug-style 404 page")