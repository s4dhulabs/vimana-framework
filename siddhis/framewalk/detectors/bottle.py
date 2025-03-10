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
#from .base import BaseDetector


class BottleDetector(BaseDetector):
    """Bottle-specific detection methods"""
    
    FRAMEWORK = "Bottle"
    
    def detect(self) -> None:
        """Run Bottle detection methods"""
        self._check_headers()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """Add score for Bottle"""
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """Add version hint for Bottle"""
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """Add component for Bottle"""
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _check_headers(self) -> None:
        """Check for Bottle-specific headers"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        # Check for Bottle in headers
        headers = response.headers
        for name, value in headers.items():
            if 'bottle' in value.lower():
                self._add_score(
                    10, 
                    'Header', 
                    f"{name} header contains Bottle: {value}"
                )
                
        # Check for bottle in response content
        if response.text and 'bottle' in response.text.lower():
            self._add_score(
                2,
                'Content',
                "Bottle reference in HTML"
            )