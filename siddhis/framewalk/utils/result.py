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

import time
import socket
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict

# Framework metadata (descriptive only — no CVE catalogs).
# CVE correlation requires reliable version detection; do not invent
# "potential vulnerabilities" from static lists.
FRAMEWORK_METADATA = {
    'Django': {
        'description': 'High-level Python web framework',
        'website': 'https://www.djangoproject.com/',
        'versions': ['1.8.x', '1.9.x', '1.10.x', '1.11.x', '2.0.x', '2.1.x', '2.2.x', '3.0.x', '3.1.x', '3.2.x', '4.0.x', '4.1.x', '4.2.x', '5.0.x'],
    },
    'Flask': {
        'description': 'Lightweight WSGI web application framework',
        'website': 'https://flask.palletsprojects.com/',
        'versions': ['0.12.x', '1.0.x', '1.1.x', '2.0.x', '2.1.x', '2.2.x', '2.3.x', '3.0.x'],
    },
    'FastAPI': {
        'description': 'Modern, fast, web framework for building APIs',
        'website': 'https://fastapi.tiangolo.com/',
        'versions': ['0.68.x', '0.70.x', '0.78.x', '0.79.x', '0.85.x', '0.88.x', '0.89.x', '0.92.x', '0.95.x', '0.100.x'],
    },
    'Pyramid': {
        'description': 'Small, fast, down-to-earth Python web framework',
        'website': 'https://trypyramid.com/',
        'versions': ['1.9.x', '1.10.x', '2.0.x'],
    },
    'Bottle': {
        'description': 'Fast and simple micro-framework for Python web applications',
        'website': 'https://bottlepy.org/',
        'versions': ['0.12.x', '0.13.x'],
    },
}


class ResultManager:
    """Handles the collection, scoring and organization of detection results"""
    
    def __init__(self, target_url: str):
        """
        Initialize the result manager
        
        Args:
            target_url: URL of the target being analyzed
        """
        self.target_url = target_url
        self.framework_scores = defaultdict(int)
        self.evidence = defaultdict(list)
        self.raw_data = {}  # Store raw data for later analysis
        self.detection_start_time = time.time()
        self.detection_end_time = None
        self.version_hints = defaultdict(list)
        self.components = defaultdict(set)  # Track detected components
        self.server_info = {}  # Server information
        self.security_headers = {"present": [], "missing": []}
        self.ip_info = self._get_ip_info()
        self.frameworks_filter = None  # Add this line
        
    def set_frameworks_filter(self, frameworks_filter: List[str]) -> None:
        """
        Set the frameworks filter
        
        Args:
            frameworks_filter: List of framework names to filter by
        """
        self.frameworks_filter = [fw.lower() for fw in frameworks_filter] if frameworks_filter else None
        
    def get_frameworks_filter(self) -> Optional[List[str]]:
        """
        Get the current frameworks filter
        
        Returns:
            List of framework names to filter by, or None if no filter is active
        """
        return self.frameworks_filter
    
    def _get_ip_info(self) -> Dict[str, Any]:
        """Get IP information for the target"""
        try:
            # Extract hostname from URL
            if self.target_url.startswith(('http://', 'https://')):
                hostname = self.target_url.split('//')[1].split('/')[0]
                # Remove port if present
                if ':' in hostname:
                    hostname = hostname.split(':')[0]
            else:
                hostname = self.target_url.split('/')[0]
                
            ip = socket.gethostbyname(hostname)
            return {"hostname": hostname, "ip": ip}
        except Exception:
            return {}
            
    def add_evidence(self, 
                     framework: str, 
                     evidence_type: str, 
                     detail: str, 
                     raw_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add detection evidence with optional raw data preservation
        
        Args:
            framework: Framework name
            evidence_type: Type of evidence (e.g., 'Header', 'Content')
            detail: Evidence details
            raw_data: Optional raw data for deeper analysis
        """
        evidence_entry = f"{evidence_type}: {detail}"
        if evidence_entry not in self.evidence[framework]:  # Avoid duplicates
            self.evidence[framework].append(evidence_entry)
            
        if raw_data:
            if framework not in self.raw_data:
                self.raw_data[framework] = []
            self.raw_data[framework].append({
                "type": evidence_type,
                "detail": detail,
                "data": raw_data
            })
            
    def add_score(self, 
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
        self.framework_scores[framework] += points
        self.add_evidence(framework, evidence_type, detail, raw_data)
        
    def add_version_hint(self, 
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
        self.version_hints[framework].append({
            "version": version,
            "confidence": confidence,
            "evidence": evidence
        })
        
    def add_component(self, 
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
        self.components[framework].add(component)
        self.add_evidence(framework, "Component", f"{component} ({evidence})")
        
    def add_server_info(self, 
                        server_type: str, 
                        version: Optional[str] = None) -> None:
        """
        Add server information
        
        Args:
            server_type: Type of server
            version: Server version if available
        """
        self.server_info["type"] = server_type
        if version:
            self.server_info["version"] = version
            
    def add_security_header(self, 
                            header: str, 
                            present: bool = True, 
                            value: Optional[str] = None) -> None:
        """
        Add security header information
        
        Args:
            header: Header name
            present: Whether the header is present
            value: Header value if available
        """
        if present:
            self.security_headers["present"].append(header)
            if value:
                # Store the value for deeper analysis
                if "values" not in self.security_headers:
                    self.security_headers["values"] = {}
                self.security_headers["values"][header] = value
        else:
            if header not in self.security_headers["missing"]:
                self.security_headers["missing"].append(header)
                
    def mark_complete(self) -> None:
        """Mark the detection as complete and record the end time"""
        self.detection_end_time = time.time()
        
    def get_detection_time(self) -> float:
        """
        Get the total detection time in seconds
        
        Returns:
            Detection time in seconds
        """
        if self.detection_end_time:
            return self.detection_end_time - self.detection_start_time
        return time.time() - self.detection_start_time
        
    def get_most_likely_version(self, framework: str) -> str:
        """
        Determine the most likely version based on hints
        
        Args:
            framework: Framework name
            
        Returns:
            Most likely version string
        """
        if not self.version_hints[framework]:
            return "Unknown"
            
        # Group by version and sum confidence scores
        version_scores = defaultdict(int)
        for hint in self.version_hints[framework]:
            version_scores[hint["version"]] += hint["confidence"]
            
        # Find the version with highest confidence
        if version_scores:
            return max(version_scores.items(), key=lambda x: x[1])[0]
        return "Unknown"
        
    def get_results(self, min_confidence: int = 0) -> Dict[str, Any]:
        """
        Compile and return detection results
        
        Args:
            min_confidence: Minimum confidence threshold for including frameworks (0-100)
            
        Returns:
            Dictionary with comprehensive detection results
        """
        # Sort frameworks by score
        sorted_frameworks = sorted(
            self.framework_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        results = {
            "target_url": self.target_url,
            "scan_time": self.get_detection_time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "ip_info": self.ip_info,
            "server_info": self.server_info,
            "security_headers": self.security_headers,
            "frameworks": [],
            "evidence": dict(self.evidence),
            "version_hints": dict(self.version_hints)
        }
        
        # Only include frameworks with a score above the minimum confidence
        for framework, score in sorted_frameworks:
            if score > 0:
                # Cap confidence at 100%
                confidence = min(score, 100)
                
                # Skip frameworks below the minimum confidence threshold
                if confidence < min_confidence:
                    continue
                    
                # Get version info if available
                version = self.get_most_likely_version(framework)
                
                # Get components
                components = list(self.components.get(framework, set()))
                
                # Only real CVE hits from VulnerabilityEngine/Prana (when version is known).
                # Do not inject static framework CVE lists — that is not detection.
                vulnerability_data = getattr(self, 'vulnerability_data', {}).get(framework, [])
                component_vulnerability_data = getattr(self, 'component_vulnerability_data', {}).get(framework, {})
                
                all_vulnerabilities = list(vulnerability_data)
                for component_vulns in component_vulnerability_data.values():
                    all_vulnerabilities.extend(component_vulns)
                
                results["frameworks"].append({
                    "name": framework,
                    "confidence": confidence,
                    "score": score,
                    "version": version,
                    "components": components,
                    "vulnerabilities": all_vulnerabilities,
                    "metadata": FRAMEWORK_METADATA.get(framework, {})
                })
        
        return results
        
    def _get_relevant_cves(self,
                           framework: str,
                           version: str) -> List[Dict[str, str]]:
        """
        Reserved for future version-aware CVE lookup.

        Returns an empty list: hardcoded CVE catalogs were removed because
        framewalk does not yet resolve precise framework versions reliably.
        """
        return []