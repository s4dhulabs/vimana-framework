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

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Optional


def make_scan_id(seed: Optional[str] = None) -> str:
    """Stable-enough short scan id (replaces legacy fakeScanId)."""
    raw = (seed or '').strip() or f'{time.time_ns()}-{uuid.uuid4().hex}'
    return hashlib.sha256(raw.encode('utf-8', errors='replace')).hexdigest()[:12]


def prepare_dashboard_data(
    response,
    exception_info,
    extracted_vars,
    scan_id: Optional[str] = None,
):
    """Prepare dashboard data in the correct format"""
    
    def ensure_string(value):
        """Convert value to string if it's a list or other type"""
        if isinstance(value, list):
            return ' '.join(str(v) for v in value)
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return str(value)

    def sanitize_dict(d):
        """Recursively sanitize dictionary values"""
        if not isinstance(d, dict):
            return d
        return {
            str(k): sanitize_dict(v) if isinstance(v, dict) else ensure_string(v)
            for k, v in d.items()
        }

    def format_stack_trace(traceback_data):
        """Format traceback data into a list of standardized entries"""
        formatted_trace = []
        
        for entry in traceback_data:
            # Extract key information from each trace entry
            triggers = entry.get('MODULE_TRIGGERS', {})
            formatted_entry = {
                'file': triggers.get('Module', ''),
                'function': triggers.get('Function', ''),
                'line': triggers.get('Line trigger', ''),
                'variables': entry.get('MODULE_ARGS', {}),
                'code_snippet': entry.get('RAW_CODE_SNIPPET', [])
            }
            formatted_trace.append(formatted_entry)
            
        return formatted_trace

    # Process form fields
    form_fields = response.meta.get('form_fields', [])
    form_fields_dict = {}
    if isinstance(form_fields, list):
        for field in form_fields:
            if 'name="' in field:
                name = field.split('name="')[1].split('"')[0]
                form_fields_dict[name] = {
                    'element': field,
                    'type': 'input' if '<input' in field else 'unknown'
                }

    # Format stack trace
    stack_trace = format_stack_trace(exception_info.get('traceback', []))

    # Prepare headers
    request_headers = {
        k.decode('utf-8') if isinstance(k, bytes) else str(k): 
        v[0].decode('utf-8') if isinstance(v[0], bytes) else str(v[0])
        for k, v in response.request.headers.items()
    }
    
    response_headers = {
        k.decode('utf-8') if isinstance(k, bytes) else str(k): 
        v[0].decode('utf-8') if isinstance(v[0], bytes) else str(v[0])
        for k, v in response.headers.items()
    }

    resolved_scan_id = (
        (scan_id or '').strip()
        or str(exception_info.get('scan_id') or '').strip()
        or make_scan_id(
            f"{exception_info.get('exception_id')}-"
            f"{(exception_info.get('summary') or {}).get('Request URL', '')}"
        )
    )
    
    dashboard_data = {
        'exception_id': exception_info.get('exception_id'),
        'scan_id': resolved_scan_id,
        'exception_meta': {
            'exception_id': exception_info.get('exception_id'),
            'summary': sanitize_dict(exception_info.get('summary', {})),
            'view_trigger': exception_info.get('view_trigger', {})
        },
        'request_headers': request_headers,
        'response_headers': response_headers,
        'form_data': sanitize_dict(response.meta.get('form_data', {})),
        'form_fields': form_fields_dict,
        'extracted_vars': sanitize_dict(extracted_vars) if extracted_vars else {},
    }
    
    # Add the formatted stack trace to exception_meta
    dashboard_data['exception_meta']['traceback'] = stack_trace
    dashboard_data['exception_meta']['exception_id'] = exception_info.get('exception_id')
    dashboard_data['exception_meta']['scan_id'] = resolved_scan_id
    
    return dashboard_data

def send_to_dashboard(data: dict = None, dashboard_url: str = "http://127.0.0.1:8000", app_env: dict = None):
    """Send data to dashboard server using treq"""
    import treq
    from twisted.internet import reactor
    from twisted.internet.defer import inlineCallbacks


    if app_env:
        @inlineCallbacks
        def _send_environment():
            try:
                env_response = yield treq.post(
                    f"{dashboard_url}/environment",
                    json=app_env,
                    headers={'Content-Type': ['application/json']}
                )
                env_content = yield treq.json_content(env_response)
                print(f"Environment upload response: {env_content}")
            except Exception as e:
                print(f"Error sending environment to dashboard: {e}")
        
        # Call the environment sender
        reactor.callFromThread(_send_environment)

    # Normal exception sending logic
    @inlineCallbacks
    def _send():
        try:
            response = yield treq.post(
                f"{dashboard_url}/exception",
                json=data,
                headers={'Content-Type': ['application/json']}
            )
            content = yield treq.json_content(response)
            print(f"Dashboard response: {content}")
        except Exception as e:
            print(f"Error sending to dashboard: {e}")

    reactor.callFromThread(_send)
