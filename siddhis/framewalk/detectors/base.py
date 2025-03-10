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

from typing import Dict, List, Any, Optional, Set
from abc import ABC, abstractmethod

from ..utils.http import RequestManager
from ..utils.result import ResultManager


class BaseDetector(ABC):
    """Base class for all framework-specific detectors"""
    
    def __init__(self, request_manager: RequestManager, result_manager: ResultManager):
        """
        Initialize the detector
        
        Args:
            request_manager: HTTP request manager instance
            result_manager: Result manager instance
        """
        self.request_manager = request_manager
        self.result_manager = result_manager
        
    @abstractmethod
    def detect(self) -> None:
        """
        Run detection methods
        Must be implemented by subclasses
        """
        pass
        
    def detect_version(self) -> None:
        """
        Attempt to detect framework version
        Can be overridden by subclasses with framework-specific implementation
        """
        pass
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add score and evidence for this framework
        
        Args:
            points: Score points to add
            evidence_type: Type of evidence
            detail: Evidence details
            raw_data: Optional raw data
        """
        # Each detector should implement this to use the framework name
        raise NotImplementedError("Subclasses must implement _add_score()")
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """
        Add a version detection hint for this framework
        
        Args:
            version: Detected version
            confidence: Confidence score (0-100)
            evidence: Evidence for this version detection
        """
        # Each detector should implement this to use the framework name
        raise NotImplementedError("Subclasses must implement _add_version_hint()")
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """
        Add a detected component for this framework
        
        Args:
            component: Component name
            evidence: Evidence for this component detection
        """
        # Each detector should implement this to use the framework name
        raise NotImplementedError("Subclasses must implement _add_component()")
        
    def _analyze_response(self, 
                         response: Any, 
                         path: str) -> None:
        """
        Analyze a response for framework-specific patterns
        
        Args:
            response: Response object
            path: Path that was requested
        """
        # Each detector should implement this for framework-specific analysis
        pass