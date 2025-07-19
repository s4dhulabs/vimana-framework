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
import random
import requests
from typing import Dict, Any, Optional, Tuple, Union
from urllib.parse import urljoin
from requests.exceptions import RequestException, Timeout

# Common User-Agents for request diversification
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Edge/117.0.2045.47',
]


class RequestManager:
    """Manages HTTP requests with stealth and reliability features"""
    
    def __init__(self, 
                 target_url: str, 
                 timeout: int = 10, 
                 delay_range: Tuple[float, float] = (0.5, 2.0), 
                 max_retries: int = 3, 
                 stealth_mode: bool = False,
                 user_agent: Optional[str] = None):
        """
        Initialize the request manager
        
        Args:
            target_url: Base URL of the target
            timeout: Request timeout in seconds
            delay_range: Tuple of (min_delay, max_delay) between requests
            max_retries: Maximum number of request retries
            stealth_mode: Enable stealth mode for less detectable scanning
            user_agent: Custom User-Agent string (if None, a random one is selected)
        """
        self.target_url = target_url.rstrip('/')
        self.timeout = timeout
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.stealth_mode = stealth_mode
        self.custom_user_agent = user_agent
        
        self.session = requests.Session()
        self.last_request_time = 0
        self.responses_cache = {}  # Cache responses to avoid duplicate requests
        
        # Set initial User-Agent
        self._rotate_user_agent()
        
    def _rotate_user_agent(self) -> None:
        """Randomly select a user agent to reduce fingerprinting"""
        if self.custom_user_agent:
            self.session.headers.update({'User-Agent': self.custom_user_agent})
        else:
            self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        
    def _add_request_delay(self) -> None:
        """Add a randomized delay between requests to avoid detection"""
        if self.stealth_mode:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            
            # If the last request was too recent, add a delay
            min_delay, max_delay = self.delay_range
            if elapsed < min_delay:
                sleep_time = random.uniform(min_delay, max_delay)
                time.sleep(sleep_time)
                
            self.last_request_time = time.time()
            
    def _get_cache_key(self, 
                       path: str, 
                       method: str, 
                       data: Optional[Dict[str, Any]] = None, 
                       headers: Optional[Dict[str, str]] = None) -> str:
        """
        Generate a cache key for a request
        
        Args:
            path: Request path
            method: HTTP method
            data: Request data
            headers: Request headers
            
        Returns:
            Cache key string
        """
        headers_str = str(sorted(headers.items())) if headers else ""
        data_str = str(sorted(data.items())) if data else ""
        return f"{method}:{path}:{data_str}:{headers_str}"
        
    def make_request(self, 
                     path: str = "", 
                     method: str = "GET", 
                     data: Optional[Dict[str, Any]] = None, 
                     headers: Optional[Dict[str, str]] = None, 
                     allow_redirects: bool = True, 
                     retry_count: int = 0,
                     cache: bool = True) -> Optional[requests.Response]:
        """
        Make an HTTP request with stealth and retry capabilities
        
        Args:
            path: Request path (relative to target URL)
            method: HTTP method
            data: Request data
            headers: Request headers
            allow_redirects: Whether to follow redirects
            retry_count: Current retry count (used internally)
            cache: Whether to use response caching
            
        Returns:
            Response object or None if request failed
        """
        url = urljoin(self.target_url, path)
        
        # Check cache if enabled
        if cache:
            cache_key = self._get_cache_key(path, method, data, headers)
            if cache_key in self.responses_cache:
                return self.responses_cache[cache_key]
        
        # Apply stealth techniques
        if self.stealth_mode:
            self._add_request_delay()
            if random.random() < 0.3:  # 30% chance to rotate user agent
                self._rotate_user_agent()
        
        try:
            response = self.session.request(
                method, 
                url, 
                data=data, 
                headers=headers, 
                timeout=self.timeout,
                allow_redirects=allow_redirects
            )
            
            # Cache the response if caching is enabled
            if cache:
                self.responses_cache[cache_key] = response
                
            return response
            
        except (Timeout, RequestException) as e:
            # Implement retry logic with shorter backoff
            if retry_count < self.max_retries:
                # Use a shorter backoff: min(0.5 seconds, timeout/2)
                backoff_time = min(0.5, self.timeout / 2)
                time.sleep(backoff_time)
                return self.make_request(
                    path, method, data, headers, allow_redirects, retry_count + 1, cache
                )
            return None
            
    def clear_cache(self) -> None:
        """Clear the response cache"""
        self.responses_cache = {}