# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-2py scanner database scanner
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import re
import datetime
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse


class DatabaseScanner:
    """
    Scanner for Web2py database exposure vulnerabilities.
    
    Detects exposed SQLite databases, backup files, and database configuration.
    """
    
    def __init__(self, http_client, config: Dict[str, Any]):
        self.http_client = http_client
        self.config = config
        self.debug_fn = config.get('debug_fn', print)
        
        # Common Web2py database file patterns
        self.database_patterns = [
            # SQLite database files
            r'storage\.sqlite',
            r'storage\.db',
            r'applications/\w+/databases/storage\.sqlite',
            r'applications/\w+/databases/storage\.db',
            r'databases/storage\.sqlite',
            r'databases/storage\.db',
            r'\.sqlite$',
            r'\.db$',
            
            # Database backup files
            r'storage\.sqlite\.backup',
            r'storage\.sqlite\.bak',
            r'storage\.sqlite\.old',
            r'storage\.sqlite\.tmp',
            r'storage\.sqlite\.save',
            r'storage\.sqlite\.copy',
            r'storage\.db\.backup',
            r'storage\.db\.bak',
            r'storage\.db\.old',
            r'storage\.db\.tmp',
            r'storage\.db\.save',
            r'storage\.db\.copy',
            
            # Database configuration files
            r'databases\.py',
            r'db\.py',
            r'config\.py',
            r'settings\.py',
            r'\.ini$',
            r'\.conf$',
            r'\.cfg$',
            
            # Web2py specific database paths
            r'applications/\w+/databases/',
            r'applications/\w+/private/',
            r'applications/\w+/uploads/',
            r'private/',
            r'uploads/',
            
            # Database dump files
            r'\.sql$',
            r'\.dump$',
            r'\.export$',
            r'backup\.sql',
            r'dump\.sql',
            r'export\.sql',
            
            # Database connection strings in content
            r'sqlite://',
            r'mysql://',
            r'postgresql://',
            r'oracle://',
            r'mssql://',
            r'database_url',
            r'db_url',
            r'connection_string',
        ]
        
        # Common database file extensions
        self.database_extensions = [
            '.sqlite', '.db', '.sql', '.dump', '.bak', '.backup', 
            '.old', '.tmp', '.save', '.copy', '.export'
        ]
        
        # Common Web2py database paths to test
        self.database_paths = [
            # Direct database files
            '/applications/welcome/databases/storage.sqlite',
            '/applications/welcome/databases/storage.db',
            '/applications/admin/databases/storage.sqlite',
            '/applications/admin/databases/storage.db',
            '/databases/storage.sqlite',
            '/databases/storage.db',
            '/storage.sqlite',
            '/storage.db',
            '/db.sqlite',
            '/db.db',
            
            # Backup files
            '/applications/welcome/databases/storage.sqlite.backup',
            '/applications/welcome/databases/storage.sqlite.bak',
            '/applications/welcome/databases/storage.sqlite.old',
            '/applications/welcome/databases/storage.sqlite.tmp',
            '/applications/welcome/databases/storage.sqlite.save',
            '/applications/welcome/databases/storage.sqlite.copy',
            '/storage.sqlite.backup',
            '/storage.sqlite.bak',
            '/storage.sqlite.old',
            '/storage.sqlite.tmp',
            '/storage.sqlite.save',
            '/storage.sqlite.copy',
            
            # Configuration files
            '/applications/welcome/databases.py',
            '/applications/welcome/db.py',
            '/applications/welcome/config.py',
            '/applications/welcome/settings.py',
            '/applications/admin/databases.py',
            '/applications/admin/db.py',
            '/applications/admin/config.py',
            '/applications/admin/settings.py',
            '/databases.py',
            '/db.py',
            '/config.py',
            '/settings.py',
            
            # Database directories
            '/applications/welcome/databases/',
            '/applications/admin/databases/',
            '/applications/welcome/private/',
            '/applications/admin/private/',
            '/applications/welcome/uploads/',
            '/applications/admin/uploads/',
            '/private/',
            '/uploads/',
            
            # Database dumps
            '/backup.sql',
            '/dump.sql',
            '/export.sql',
            '/database.sql',
            '/data.sql',
            '/backup/database.sql',
            '/backup/data.sql',
            '/dumps/database.sql',
            '/dumps/data.sql',
        ]
        
        # SQLite file magic bytes (SQLite database header)
        self.sqlite_magic = b'SQLite format 3\x00'
        
        # For reporting findings
        self.database_files = []
        self.backup_files = []
        self.config_files = []
        self.vulnerabilities = []
        self.tests_performed = []

    def _debug(self, message: str, context: str = None, emoji: str = None):
        """Debug logging function."""
        if not self.config.get("verbose", False):
            return
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[DEBUG]"
        if context:
            prefix += f"[{context}]"
        if emoji:
            prefix += f" {emoji}"
        self.debug_fn(f"{ts} {prefix} {message}")

    def _create_vuln(self, title: str, risk: str, description: str, evidence: List[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a vulnerability report."""
        return {
            "title": title,
            "risk": risk,
            "description": description,
            "evidence": evidence,
            "metadata": metadata,
            "scanner": "database_scanner"
        }

    def _is_sqlite_file(self, content: bytes) -> bool:
        """Check if content appears to be a SQLite database file."""
        if len(content) < 16:
            return False
        return content[:16] == self.sqlite_magic

    def _detect_database_patterns(self, content: str, url: str) -> List[str]:
        """Detect database-related patterns in content."""
        findings = []
        for pattern in self.database_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings.extend(matches)
        return list(set(findings))  # Remove duplicates

    async def _test_database_file(self, target_url: str, path: str) -> Dict[str, Any]:
        """Test if a database file is accessible."""
        url = urljoin(target_url, path)
        try:
            self._debug(f"Testing database file: {path}", context="database_test", emoji="🗄️")
            
            # First try HEAD request to check if file exists
            head_result = await self.http_client.head(url)
            if head_result.get("status") == 200:
                # File exists, now try to get content
                get_result = await self.http_client.get(url)
                if get_result.get("status") == 200:
                    content = get_result.get("content", "")
                    content_bytes = content.encode('utf-8', errors='ignore') if isinstance(content, str) else content
                    
                    # Check if it's a SQLite file
                    is_sqlite = self._is_sqlite_file(content_bytes)
                    
                    # Check content type
                    content_type = get_result.get("headers", {}).get("content-type", "")
                    
                    # Check file size
                    content_length = get_result.get("headers", {}).get("content-length", "0")
                    
                    return {
                        "path": path,
                        "url": url,
                        "status": get_result.get("status"),
                        "content_type": content_type,
                        "content_length": content_length,
                        "is_sqlite": is_sqlite,
                        "accessible": True,
                        "content_preview": content[:200] if content else ""
                    }
            
            return {
                "path": path,
                "url": url,
                "status": head_result.get("status", 0),
                "accessible": False
            }
            
        except Exception as e:
            self._debug(f"Error testing {path}: {e}", context="database_test", emoji="⚠️")
            return {
                "path": path,
                "url": url,
                "status": 0,
                "accessible": False,
                "error": str(e)
            }

    async def _discover_database_files(self, target_url: str) -> List[str]:
        """Discover potential database files through directory listing and common paths."""
        discovered_files = []
        
        # Test common database paths
        for path in self.database_paths:
            discovered_files.append(path)
        
        # Try to discover additional files through directory listing
        common_dirs = [
            '/applications/',
            '/applications/welcome/',
            '/applications/admin/',
            '/databases/',
            '/private/',
            '/uploads/',
            '/backup/',
            '/dumps/',
            '/data/',
        ]
        
        for directory in common_dirs:
            try:
                url = urljoin(target_url, directory)
                result = await self.http_client.get(url)
                if result.get("status") == 200:
                    content = result.get("content", "")
                    
                    # Look for database files in directory listing
                    for ext in self.database_extensions:
                        pattern = rf'href=["\']([^"\']*{re.escape(ext)})["\']'
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            if match.startswith('/'):
                                discovered_files.append(match)
                            else:
                                discovered_files.append(f"{directory.rstrip('/')}/{match}")
                    
                    # Look for database-related patterns
                    db_patterns = self._detect_database_patterns(content, url)
                    for pattern in db_patterns:
                        if pattern.startswith('/'):
                            discovered_files.append(pattern)
                        else:
                            discovered_files.append(f"{directory.rstrip('/')}/{pattern}")
                            
            except Exception as e:
                self._debug(f"Error discovering files in {directory}: {e}", context="discovery", emoji="⚠️")
                continue
        
        return list(set(discovered_files))  # Remove duplicates

    async def scan(self, target_url: str) -> Dict[str, Any]:
        """
        Scan target for database exposure vulnerabilities.
        
        Args:
            target_url: Target URL to scan
            
        Returns:
            Dictionary containing scan results and vulnerabilities
        """
        self.database_files = []
        self.backup_files = []
        self.config_files = []
        self.vulnerabilities = []
        self.tests_performed = []
        
        try:
            self._debug("Starting database scanner phase...", context="database_scanner", emoji="🗄️")
            
            # Discover potential database files
            discovered_files = await self._discover_database_files(target_url)
            self._debug(f"Discovered {len(discovered_files)} potential database files", context="discovery", emoji="🔍")
            
            # Test each discovered file
            for file_path in discovered_files:
                result = await self._test_database_file(target_url, file_path)
                self.tests_performed.append(result)
                
                if result.get("accessible", False):
                    # Categorize the file
                    if result.get("is_sqlite", False):
                        self.database_files.append(result)
                        self.vulnerabilities.append(self._create_vuln(
                            "SQLite Database Exposure",
                            "critical",
                            f"SQLite database file is directly accessible at {file_path}",
                            [f"Database file accessible at: {result['url']}", 
                             f"Content-Type: {result.get('content_type', 'Unknown')}",
                             f"File size: {result.get('content_length', 'Unknown')} bytes"],
                            {"endpoint": file_path, "cwe": "CWE-200", "file_type": "sqlite"}
                        ))
                        self._debug(f"CRITICAL: SQLite database exposed at {file_path}", context="vuln", emoji="💥")
                    
                    elif any(ext in file_path.lower() for ext in ['.backup', '.bak', '.old', '.tmp', '.save', '.copy']):
                        self.backup_files.append(result)
                        self.vulnerabilities.append(self._create_vuln(
                            "Database Backup File Exposure",
                            "high",
                            f"Database backup file is accessible at {file_path}",
                            [f"Backup file accessible at: {result['url']}", 
                             f"Content-Type: {result.get('content_type', 'Unknown')}",
                             f"File size: {result.get('content_length', 'Unknown')} bytes"],
                            {"endpoint": file_path, "cwe": "CWE-200", "file_type": "backup"}
                        ))
                        self._debug(f"HIGH: Database backup exposed at {file_path}", context="vuln", emoji="⚠️")
                    
                    elif any(ext in file_path.lower() for ext in ['.py', '.ini', '.conf', '.cfg']):
                        self.config_files.append(result)
                        self.vulnerabilities.append(self._create_vuln(
                            "Database Configuration Exposure",
                            "medium",
                            f"Database configuration file is accessible at {file_path}",
                            [f"Config file accessible at: {result['url']}", 
                             f"Content-Type: {result.get('content_type', 'Unknown')}",
                             f"File size: {result.get('content_length', 'Unknown')} bytes"],
                            {"endpoint": file_path, "cwe": "CWE-200", "file_type": "config"}
                        ))
                        self._debug(f"MEDIUM: Database config exposed at {file_path}", context="vuln", emoji="📄")
                    
                    elif any(ext in file_path.lower() for ext in ['.sql', '.dump', '.export']):
                        self.backup_files.append(result)
                        self.vulnerabilities.append(self._create_vuln(
                            "Database Dump File Exposure",
                            "high",
                            f"Database dump file is accessible at {file_path}",
                            [f"Dump file accessible at: {result['url']}", 
                             f"Content-Type: {result.get('content_type', 'Unknown')}",
                             f"File size: {result.get('content_length', 'Unknown')} bytes"],
                            {"endpoint": file_path, "cwe": "CWE-200", "file_type": "dump"}
                        ))
                        self._debug(f"HIGH: Database dump exposed at {file_path}", context="vuln", emoji="💾")
                    
                    else:
                        # Generic database file exposure
                        self.database_files.append(result)
                        self.vulnerabilities.append(self._create_vuln(
                            "Database File Exposure",
                            "medium",
                            f"Database-related file is accessible at {file_path}",
                            [f"File accessible at: {result['url']}", 
                             f"Content-Type: {result.get('content_type', 'Unknown')}",
                             f"File size: {result.get('content_length', 'Unknown')} bytes"],
                            {"endpoint": file_path, "cwe": "CWE-200", "file_type": "unknown"}
                        ))
                        self._debug(f"MEDIUM: Database file exposed at {file_path}", context="vuln", emoji="📁")
            
            # Check for database connection strings in HTML content
            try:
                main_page = await self.http_client.get(target_url)
                if main_page.get("status") == 200:
                    content = main_page.get("content", "")
                    db_patterns = self._detect_database_patterns(content, target_url)
                    
                    if db_patterns:
                        self.vulnerabilities.append(self._create_vuln(
                            "Database Connection String Disclosure",
                            "medium",
                            "Database connection strings found in HTML content",
                            db_patterns,
                            {"endpoint": "/", "cwe": "CWE-200", "disclosure_type": "connection_string"}
                        ))
                        self._debug(f"MEDIUM: Database connection strings found in HTML", context="vuln", emoji="🔗")
                        
            except Exception as e:
                self._debug(f"Error checking main page for database patterns: {e}", context="database_scanner", emoji="⚠️")
            
            self._debug(f"Database scanner completed. Found {len(self.vulnerabilities)} vulnerabilities", context="summary", emoji="📊")
            
        except Exception as e:
            self._debug(f"Database scanner error: {str(e)}", context="database_scanner", emoji="⚠️")
            self.vulnerabilities.append(self._create_vuln(
                "Database Scanner Error",
                "medium",
                f"Error during database scanning: {str(e)}",
                [f"Scanner error: {str(e)}"],
                {"error": str(e)}
            ))
        
        return {
            "vulnerabilities": self.vulnerabilities,
            "database_files": self.database_files,
            "backup_files": self.backup_files,
            "config_files": self.config_files,
            "tests_performed": self.tests_performed
        } 