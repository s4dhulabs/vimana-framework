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
from abc import ABC, abstractmethod

from ..utils.http import RequestManager
from ..utils.result import ResultManager


class BaseEngine(ABC):
    """Base class for all detection engines"""
    
    def __init__(self, request_manager: RequestManager, result_manager: ResultManager):
        """
        Initialize the base engine
        
        Args:
            request_manager: HTTP request manager instance
            result_manager: Result manager instance
        """
        self.request_manager = request_manager
        self.result_manager = result_manager
        
    @abstractmethod
    def analyze(self) -> None:
        """
        Run analysis methods of the engine
        Must be implemented by subclasses
        """
        pass
        

    def _add_score(self, 
                framework: str, 
                points: int, 
                evidence_type: str, 
                detail: str, 
                raw_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add score and evidence for a framework detection
        
        Args:
            framework: Framework name
            points: Score points to add
            evidence_type: Type of evidence
            detail: Evidence details
            raw_data: Optional raw data
        """
        # Check if we should filter by frameworks
        frameworks_filter = None
        if hasattr(self.result_manager, 'get_frameworks_filter'):
            frameworks_filter = self.result_manager.get_frameworks_filter()
        
        # If frameworks filter is active and this framework is not in the list, skip it
        if frameworks_filter and framework.lower() not in frameworks_filter:
            return
            
        self.result_manager.add_score(framework, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                     framework: str, 
                     version: str, 
                     confidence: int, 
                     evidence: str) -> None:
        """
        Add a version detection hint
        
        Args:
            framework: Framework name
            version: Detected version
            confidence: Confidence score (0-100)
            evidence: Evidence for this version detection
        """
        # Check if we should filter by frameworks
        frameworks_filter = None
        if hasattr(self.result_manager, 'get_frameworks_filter'):
            frameworks_filter = self.result_manager.get_frameworks_filter()
        
        # If frameworks filter is active and this framework is not in the list, skip it
        if frameworks_filter and framework.lower() not in frameworks_filter:
            return
            
        self.result_manager.add_version_hint(framework, version, confidence, evidence)
    
    def _add_component(self, 
                  framework: str, 
                  component: str, 
                  evidence: str) -> None:
        """
        Add a detected component for a framework
        
        Args:
            framework: Framework name
            component: Component name
            evidence: Evidence for this component detection
        """
        # Check if we should filter by frameworks
        frameworks_filter = None
        if hasattr(self.result_manager, 'get_frameworks_filter'):
            frameworks_filter = self.result_manager.get_frameworks_filter()
        
        # If frameworks filter is active and this framework is not in the list, skip it
        if frameworks_filter and framework.lower() not in frameworks_filter:
            return
            
        self.result_manager.add_component(framework, component, evidence)