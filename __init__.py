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
Vimana Framework - Advanced Security Testing Framework

A comprehensive security testing framework for Python web applications
with support for Django, Flask, FastAPI, and other frameworks.
"""

# Import version information
from core._version import (
    __version__,
    __version_info_tuple__,
    _version_,
    VERSION,
    FRAMEWORK_NAME,
    FRAMEWORK_AUTHOR,
    FRAMEWORK_EMAIL,
    FRAMEWORK_URL,
    FRAMEWORK_DESCRIPTION,
    get_version_info,
    print_version_info,
    get_version,
    get_legacy_version,
    is_version_compatible,
    get_plugin_version_info,
)

# Framework metadata
__title__ = FRAMEWORK_NAME
__author__ = FRAMEWORK_AUTHOR
__email__ = FRAMEWORK_EMAIL
__url__ = FRAMEWORK_URL
__description__ = FRAMEWORK_DESCRIPTION
__license__ = "MIT"

# Make version information easily accessible
version = __version__
version_info = __version_info_tuple__

# Export commonly used items
__all__ = [
    '__version__',
    '__version_info_tuple__',
    '_version_',  # Legacy compatibility
    'VERSION',
    'version',
    'version_info',
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
    '__title__',
    '__author__',
    '__email__',
    '__url__',
    '__description__',
    '__license__',
]
