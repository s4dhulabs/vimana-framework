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

from .base import BaseDetector


class PyramidDetector(BaseDetector):
    """Pyramid-specific detection methods"""
    
    FRAMEWORK = "Pyramid"
    
    def detect(self) -> None:
        """Run Pyramid detection methods"""
        self._check_headers()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """Add score for Pyramid"""
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """Add version hint for Pyramid"""
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """Add component for Pyramid"""
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _check_headers(self) -> None:
        """Check for Pyramid-specific headers"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        headers = response.headers
        
        # Check for Pyramid in headers
        for name, value in headers.items():
            if 'pyramid' in value.lower():
                self._add_score(
                    10, 
                    'Header', 
                    f"{name} header contains Pyramid: {value}"
                )