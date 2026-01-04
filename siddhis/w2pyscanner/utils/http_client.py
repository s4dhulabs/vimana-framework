# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-2py scanner http client
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import asyncio
import aiohttp
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse


class HTTPClient:
    """
    Async HTTP client for W2PyScanner with stealth capabilities and error handling.
    """
    
    def __init__(self, timeout: int = 10, max_retries: int = 3, 
                 user_agent: str = "W2PyScanner/1.0.0", stealth: bool = False,
                 min_delay: float = 0.5, max_delay: float = 2.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.stealth = stealth
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.session = None
        
        # Common User-Agent strings for stealth mode
        self.stealth_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]

    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _create_session(self):
        """Create aiohttp session with proper configuration."""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                "User-Agent": self._get_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        )

    def _get_user_agent(self) -> str:
        """Get User-Agent string based on stealth mode."""
        if self.stealth:
            return random.choice(self.stealth_user_agents)
        return self.user_agent

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, 
                  allow_redirects: bool = True, cookies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform GET request with retry logic and stealth delays.
        
        Args:
            url: Target URL
            headers: Additional headers
            allow_redirects: Whether to follow redirects
            cookies: Cookies to send with the request
        Returns:
            Dictionary containing response data
        """
        for attempt in range(self.max_retries):
            try:
                if self.stealth:
                    await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                if not self.session:
                    await self._create_session()
                req_headers = headers or {}
                async with self.session.get(url, headers=req_headers, allow_redirects=allow_redirects, cookies=cookies) as response:
                    return await self._process_response(response)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {"url": url, "status": 0, "error": str(e), "content": "", "headers": {}, "cookies": {}}
                await asyncio.sleep(0.5)

    async def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
                   headers: Optional[Dict[str, str]] = None, 
                   allow_redirects: bool = True, cookies: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform POST request with retry logic and stealth delays.
        
        Args:
            url: Target URL
            data: POST data
            headers: Additional headers
            allow_redirects: Whether to follow redirects
            cookies: Cookies to send with the request
        Returns:
            Dictionary containing response data
        """
        for attempt in range(self.max_retries):
            try:
                if self.stealth:
                    await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                if not self.session:
                    await self._create_session()
                req_headers = headers or {}
                async with self.session.post(url, data=data, headers=req_headers, allow_redirects=allow_redirects, cookies=cookies) as response:
                    return await self._process_response(response)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {"url": url, "status": 0, "error": str(e), "content": "", "headers": {}, "cookies": {}}
                await asyncio.sleep(0.5)

    async def head(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Perform HEAD request with retry logic and stealth delays.
        
        Args:
            url: Target URL
            headers: Additional headers
            
        Returns:
            Dictionary containing response data
        """
        return await self._request("HEAD", url, headers=headers)

    async def _request(self, method: str, url: str, data: Optional[Dict[str, Any]] = None,
                       headers: Optional[Dict[str, str]] = None, 
                       allow_redirects: bool = True) -> Dict[str, Any]:
        """
        Perform HTTP request with retry logic and stealth delays.
        
        Args:
            method: HTTP method (GET, POST, HEAD, etc.)
            url: Target URL
            data: Request data for POST requests
            headers: Additional headers
            allow_redirects: Whether to follow redirects
            
        Returns:
            Dictionary containing response data
        """
        if not self.session:
            await self._create_session()

        # Apply stealth delay if enabled
        if self.stealth:
            delay = random.uniform(self.min_delay, self.max_delay)
            await asyncio.sleep(delay)

        # Prepare headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    data=data,
                    headers=request_headers,
                    allow_redirects=allow_redirects
                ) as response:
                    return await self._process_response(response)
                    
            except asyncio.TimeoutError:
                last_exception = Exception(f"Request timeout after {self.timeout} seconds")
            except aiohttp.ClientError as e:
                last_exception = e
            except Exception as e:
                last_exception = e
            
            # If this is not the last attempt, wait before retrying
            if attempt < self.max_retries:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        
        # If all retries failed, raise the last exception
        raise last_exception or Exception("Request failed after all retries")

    async def _process_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        Process HTTP response and extract relevant information.
        
        Args:
            response: aiohttp ClientResponse object
            
        Returns:
            Dictionary containing response data
        """
        try:
            content = await response.text()
        except:
            content = ""
        
        try:
            json_data = await response.json()
        except:
            json_data = None

        return {
            "url": str(response.url),
            "status": response.status,
            "headers": dict(response.headers),
            "content": content,
            "json": json_data,
            "cookies": dict(response.cookies),
            "content_type": response.headers.get("content-type", ""),
            "content_length": response.headers.get("content-length", "0"),
            "server": response.headers.get("server", ""),
            "x_powered_by": response.headers.get("x-powered-by", ""),
            "set_cookie": response.headers.get("set-cookie", "")
        }

    async def check_url_exists(self, url: str) -> bool:
        """
        Check if a URL exists using HEAD request.
        
        Args:
            url: Target URL
            
        Returns:
            True if URL exists, False otherwise
        """
        try:
            result = await self.head(url)
            return result["status"] < 400
        except:
            return False

    async def get_redirect_chain(self, url: str) -> List[str]:
        """
        Get the redirect chain for a URL.
        
        Args:
            url: Target URL
            
        Returns:
            List of URLs in the redirect chain
        """
        try:
            result = await self.get(url, allow_redirects=False)
            redirect_chain = [url]
            
            if result["status"] in [301, 302, 303, 307, 308]:
                location = result["headers"].get("location")
                if location:
                    redirect_chain.append(location)
                    # Follow one more redirect to get the final destination
                    try:
                        final_result = await self.get(location, allow_redirects=False)
                        if final_result["status"] in [301, 302, 303, 307, 308]:
                            final_location = final_result["headers"].get("location")
                            if final_location:
                                redirect_chain.append(final_location)
                    except:
                        pass
            
            return redirect_chain
        except:
            return [url]

    def build_url(self, base_url: str, path: str) -> str:
        """
        Build a complete URL from base URL and path.
        
        Args:
            base_url: Base URL
            path: Path to append
            
        Returns:
            Complete URL
        """
        return urljoin(base_url, path)

    def is_web2py_app(self, response: Dict[str, Any]) -> bool:
        """
        Check if response indicates a Web2py application.
        
        Args:
            response: Response dictionary from _process_response
            
        Returns:
            True if Web2py indicators are found
        """
        headers = response.get("headers", {})
        content = response.get("content", "").lower()
        
        # Check for Web2py headers
        if "x-powered-by" in headers and "web2py" in headers["x-powered-by"].lower():
            return True
        
        if "server" in headers and "rocket" in headers["server"].lower():
            return True
        
        # Check for Web2py content patterns
        web2py_patterns = [
            "web2py",
            "session_id_welcome",
            "/admin/",
            "web2py.com",
            "rocket server"
        ]
        
        for pattern in web2py_patterns:
            if pattern in content:
                return True
        
        return False 