# -*- coding: utf-8 -*-
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

"""
Vimana Framework Version Management

This module provides centralized version management for the Vimana Framework.
All version-related information should be imported from here to ensure consistency.

Version Format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality additions
- PATCH: Backwards-compatible bug fixes
- PRERELEASE: alpha, beta, rc (release candidate)
- BUILD: Build metadata (optional)

Examples:
- 1.0.0 (stable release)
- 1.0.0-alpha.1 (alpha release)
- 1.0.0-beta.2 (beta release)
- 1.0.0-rc.1 (release candidate)
- 1.0.0+build.123 (with build metadata)
"""

import os
import sys
from typing import NamedTuple, Optional

# Core version information - UPDATE THIS FOR NEW RELEASES
__version_info__ = (0, 8, 0)  # (major, minor, patch)
__prerelease__ = None
__prerelease_num__ = None
__build__ = None  # Build metadata (optional)

class VersionInfo(NamedTuple):
    """Version information tuple"""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    prerelease_num: Optional[int] = None
    build: Optional[str] = None

def _get_version_string() -> str:
    """Generate version string from components"""
    major, minor, patch = __version_info__
    version = f"{major}.{minor}.{patch}"
    
    if __prerelease__ and __prerelease_num__:
        version += f"-{__prerelease__}.{__prerelease_num__}"
    elif __prerelease__:
        version += f"-{__prerelease__}"
    
    if __build__:
        version += f"+{__build__}"
    
    return version

def _get_legacy_version() -> str:
    """Get version in legacy format (v1.0) for backward compatibility"""
    major, minor, _ = __version_info__
    return f"v{major}.{minor}"

def _get_short_version() -> str:
    """Get short version (1.0.0) without prerelease/build info"""
    major, minor, patch = __version_info__
    return f"{major}.{minor}.{patch}"

def _get_git_version() -> Optional[str]:
    """Attempt to get git version information"""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'describe', '--tags', '--dirty', '--always'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return None

def _is_development_version() -> bool:
    """Check if this is a development version"""
    return __prerelease__ is not None or _get_git_version() is not None

# Public API - Static version for build tools
__version__ = "0.8.0"  # Updated by version manager
__version_info_tuple__ = VersionInfo(
    major=__version_info__[0],
    minor=__version_info__[1], 
    patch=__version_info__[2],
    prerelease=__prerelease__,
    prerelease_num=__prerelease_num__,
    build=__build__
)

# Legacy compatibility
_version_ = _get_legacy_version()  # For backward compatibility with existing code
VERSION = __version__
version = __version__

# Additional version formats
SHORT_VERSION = _get_short_version()
LEGACY_VERSION = _get_legacy_version()
GIT_VERSION = _get_git_version()

# Framework metadata
FRAMEWORK_NAME = "Vimana Framework"
FRAMEWORK_AUTHOR = "s4dhu"
FRAMEWORK_EMAIL = "s4dhul4bs@protonmail.ch"
FRAMEWORK_URL = "https://github.com/s4dhulabs/vimana-framework"
FRAMEWORK_DESCRIPTION = "Advanced Security Testing Framework"

def get_version_info() -> dict:
    """Get comprehensive version information"""
    return {
        'version': __version__,
        'version_info': __version_info_tuple__,
        'short_version': SHORT_VERSION,
        'legacy_version': LEGACY_VERSION,
        'git_version': GIT_VERSION,
        'is_development': _is_development_version(),
        'framework_name': FRAMEWORK_NAME,
        'author': FRAMEWORK_AUTHOR,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'python_implementation': sys.implementation.name,
    }

def print_version_info() -> None:
    """Print detailed version information"""
    info = get_version_info()
    print(f"{info['framework_name']} {info['version']}")
    print(f"Python {info['python_version']} ({info['python_implementation']})")
    if info['git_version']:
        print(f"Git: {info['git_version']}")
    if info['is_development']:
        print("Development version")

# For compatibility with existing imports
def get_version() -> str:
    """Get the current version string"""
    return __version__

def get_legacy_version() -> str:
    """Get version in legacy format for backward compatibility"""
    return _version_

# Version checking utilities
def is_version_compatible(required_version: str) -> bool:
    """Check if current version is compatible with required version"""
    try:
        from packaging import version as pkg_version
        return pkg_version.parse(__version__) >= pkg_version.parse(required_version)
    except ImportError:
        # Fallback to simple string comparison if packaging not available
        return __version__ >= required_version

def get_plugin_version_info(plugin_name: str, plugin_version: str = "1.0.0") -> dict:
    """Get version information for a plugin"""
    return {
        'plugin_name': plugin_name,
        'plugin_version': plugin_version,
        'framework_version': __version__,
        'compatible': True,  # Add compatibility logic as needed
        'framework_name': FRAMEWORK_NAME
    }

# Make commonly used variables available at module level
__all__ = [
    '__version__',
    '__version_info_tuple__',
    '_version_',  # Legacy compatibility
    'VERSION',
    'version',
    'SHORT_VERSION',
    'LEGACY_VERSION',
    'GIT_VERSION',
    'FRAMEWORK_NAME',
    'FRAMEWORK_AUTHOR',
    'FRAMEWORK_EMAIL',
    'FRAMEWORK_URL',
    'FRAMEWORK_DESCRIPTION',
    'get_version_info',
    'print_version_info',
    'get_version',
    'get_legacy_version',
    'is_version_compatible',
    'get_plugin_version_info',
] 