# -*- coding: utf-8 -*-
"""
Robust mock fixtures for Exception Monitor demos / tests.

Produces multiple mocked Django-style applications with varied
exception types, severities, security findings, stack traces, and
environments — enough for FuzzingDashboard filters + reassembly UI.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from core.api.dashboard_utils import make_scan_id


# ---------------------------------------------------------------------------
# Application catalogue
# ---------------------------------------------------------------------------

MOCK_APPS: List[Dict[str, Any]] = [
    {
        'name': 'shop',
        'base_url': 'https://shop.lab.vimana.local',
        'django_version': '4.2.11',
        'plugin': 'djunch',
        'views': [
            ('catalog/views.py', 'ProductDetailView', '/products/<int:pk>/', 88),
            ('orders/views.py', 'CheckoutView', '/checkout/', 142),
            ('cart/views.py', 'AddToCartView', '/cart/add/', 55),
        ],
    },
    {
        'name': 'blog',
        'base_url': 'https://blog.lab.vimana.local',
        'django_version': '3.2.25',
        'plugin': 'd4m8',
        'views': [
            ('posts/views.py', 'PostDetail', '/posts/<slug>/', 64),
            ('comments/views.py', 'CreateComment', '/comments/new/', 37),
        ],
    },
    {
        'name': 'intranet',
        'base_url': 'https://intranet.lab.vimana.local',
        'django_version': '4.1.13',
        'plugin': 'djunch',
        'views': [
            ('hr/views.py', 'EmployeeProfile', '/hr/employees/<uuid:id>/', 210),
            ('authz/views.py', 'RoleGate', '/admin/roles/', 91),
            ('files/views.py', 'DocumentDownload', '/files/<path:name>', 48),
        ],
    },
    {
        'name': 'payments',
        'base_url': 'https://pay.lab.vimana.local',
        'django_version': '4.2.11',
        'plugin': 'd4m8',
        'views': [
            ('billing/views.py', 'ChargeCard', '/v1/charges/', 119),
            ('webhooks/views.py', 'StripeHook', '/hooks/stripe/', 73),
        ],
    },
    {
        'name': 'cms',
        'base_url': 'https://cms.lab.vimana.local',
        'django_version': '5.0.3',
        'plugin': 'djunch',
        'views': [
            ('pages/views.py', 'PageRender', '/p/<slug>/', 33),
            ('media/views.py', 'UploadMedia', '/media/upload/', 101),
        ],
    },
]


_EXCEPTION_BLUEPRINTS: List[Dict[str, Any]] = [
    {
        'type': 'SuspiciousOperation',
        'category': 'Security',
        'value': 'Invalid HTTP_HOST header',
        'severity_hint': 'critical',
        'method': 'GET',
        'security': {
            'issue_type': 'host_header_injection',
            'confidence': 0.92,
            'description': 'Host header accepted without allowlist',
            'recommendation': 'Set ALLOWED_HOSTS explicitly; reject unknown Host',
            'related_cwe': 'CWE-644',
        },
    },
    {
        'type': 'PermissionDenied',
        'category': 'Auth',
        'value': 'User lacks permission to access employee record',
        'severity_hint': 'high',
        'method': 'GET',
        'security': {
            'issue_type': 'broken_access_control',
            'confidence': 0.81,
            'description': 'Object-level authorization missing on employee profile',
            'recommendation': 'Enforce ownership / RBAC checks before queryset',
            'related_cwe': 'CWE-639',
        },
    },
    {
        'type': 'DoesNotExist',
        'category': 'ORM',
        'value': 'Product matching query does not exist',
        'severity_hint': 'medium',
        'method': 'GET',
        'security': None,
    },
    {
        'type': 'FieldError',
        'category': 'ORM',
        'value': "Cannot resolve keyword 'is_staffx' into field",
        'severity_hint': 'low',
        'method': 'POST',
        'security': None,
    },
    {
        'type': 'MultiValueDictKeyError',
        'category': 'Request',
        'value': "'csrfmiddlewaretoken'",
        'severity_hint': 'medium',
        'method': 'POST',
        'security': {
            'issue_type': 'csrf_bypass_probe',
            'confidence': 0.55,
            'description': 'Missing CSRF token on state-changing endpoint',
            'recommendation': 'Ensure CSRF middleware + template tokens',
            'related_cwe': 'CWE-352',
        },
    },
    {
        'type': 'TypeError',
        'category': 'Runtime',
        'value': "int() argument must be a string, a bytes-like object or a number, not 'NoneType'",
        'severity_hint': 'low',
        'method': 'GET',
        'security': None,
    },
    {
        'type': 'DisallowedHost',
        'category': 'Security',
        'value': "Invalid HTTP_HOST header: 'evil.example'",
        'severity_hint': 'critical',
        'method': 'GET',
        'security': {
            'issue_type': 'disallowed_host',
            'confidence': 0.95,
            'description': 'DEBUG traceback leaked for DisallowedHost',
            'recommendation': 'Disable DEBUG in production; customize 400 handler',
            'related_cwe': 'CWE-209',
        },
    },
    {
        'type': 'ValidationError',
        'category': 'Forms',
        'value': "['Enter a valid email address.']",
        'severity_hint': 'low',
        'method': 'POST',
        'security': None,
    },
]


def _utc(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)).isoformat()


def _code_snippet(view_fn: str, line: int) -> List[str]:
    return [
        f'def {view_fn}(request, *args, **kwargs):',
        '    ctx = {}',
        f'    # trigger near line {line}',
        '    obj = Model.objects.get(pk=kwargs.get("pk"))',
        '    return render(request, "detail.html", {"obj": obj})',
    ]


def _stack_frames(app: str, module: str, fn: str, line: int) -> List[Dict[str, Any]]:
    fullpath = f'/opt/apps/{app}/{module}'
    return [
        {
            'file': f'/usr/local/lib/python3.11/site-packages/django/core/handlers/base.py',
            'function': '_get_response',
            'line': f'174   response = wrapped_callback(request, *callback_args, **callback_kwargs)',
            'variables': {'request': '<WSGIRequest>'},
            'code_snippet': [
                'def _get_response(self, request):',
                '    response = wrapped_callback(...)',
            ],
        },
        {
            'file': fullpath,
            'function': fn,
            'line': f'{line}   obj = Model.objects.get(pk=kwargs.get("pk"))',
            'variables': {
                'request': '<WSGIRequest>',
                'kwargs': "{'pk': None}",
                'user': f'<User: mock@{app}>',
            },
            'code_snippet': _code_snippet(fn, line),
        },
    ]


def _security_issue(blueprint: Optional[Dict[str, Any]], evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not blueprint:
        return []
    return [{
        'issue_type': blueprint['issue_type'],
        'confidence': blueprint['confidence'],
        'description': blueprint['description'],
        'evidence': evidence,
        'recommendation': blueprint['recommendation'],
        'related_cwe': blueprint.get('related_cwe'),
    }]


def build_environment(app: Dict[str, Any]) -> Dict[str, Any]:
    name = app['name']
    return {
        'DJANGO_SETTINGS_MODULE': f'{name}.settings',
        'ROOT_URLCONF': f'{name}.urls',
        'DEBUG': 'True',
        'SECRET_KEY': f'mock-secret-{name}-not-for-prod',
        'ALLOWED_HOSTS': f"{name}.lab.vimana.local,localhost",
        'DATABASES': "{'default': {'ENGINE': 'django.db.backends.sqlite3'}}",
        'INSTALLED_APPS': f"['django.contrib.admin', '{name}.apps.Config']",
        'MIDDLEWARE': "['django.middleware.security.SecurityMiddleware', ...]",
        'SERVER_NAME': f"{name}.lab.vimana.local",
        'SERVER_SOFTWARE': 'gunicorn/21.2.0',
        'Django Version': app['django_version'],
    }


def build_exception_record(
    app: Dict[str, Any],
    view: Tuple[str, str, str, int],
    blueprint: Dict[str, Any],
    *,
    scan_id: str,
    index: int,
) -> Dict[str, Any]:
    """Return a DashboardException-compatible dict."""
    module, fn, path, line = view
    fullpath = f'/opt/apps/{app["name"]}/{module}'
    endpoint = f'{app["base_url"]}{path.replace("<int:pk>", "42").replace("<slug>", "hello").replace("<uuid:id>", "11111111-1111-1111-1111-111111111111").replace("<path:name>", "docs/q1.pdf")}'
    exc_id = f'mock-{app["name"]}-{index}-{uuid4().hex[:6]}'
    stack = _stack_frames(app['name'], module, fn, line)
    summary = {
        'Exception Type': blueprint['type'],
        'Exception Value': blueprint['value'],
        'Category': blueprint['category'],
        'Request Method': blueprint['method'],
        'Request URL': endpoint,
        'Django Version': app['django_version'],
        'Exception Location': f'{module} in {fn}, line {line}',
        'Python Executable': '/usr/local/bin/python',
        'Python Version': '3.11.8',
        'Server time': _utc(index),
    }
    view_trigger = {
        'app_name': app['name'],
        'fullpath': fullpath,
        'shortpath': module,
        'object': fn,
        'line_number': line,
        'trigger_line': stack[-1]['line'],
    }
    meta = {
        'exception_id': exc_id,
        'scan_id': scan_id,
        'plugin': app['plugin'],
        'summary': summary,
        'view_trigger': view_trigger,
        'traceback': stack,
        'security_issues': _security_issue(
            blueprint.get('security'),
            {'endpoint': endpoint, 'app': app['name'], 'module': module},
        ),
    }
    severity = blueprint.get('severity_hint') or 'low'
    return {
        'id': exc_id,
        'scan_id': scan_id,
        'timestamp': _utc(index * 3),
        'endpoint': endpoint,
        'method': blueprint['method'],
        'exception_type': blueprint['type'],
        'severity': severity,
        'description': blueprint['value'],
        'stack_trace': stack,
        'request_data': {
            'headers': {
                'Host': f'{app["name"]}.lab.vimana.local',
                'User-Agent': 'vimana-monitor-mock/1.0',
                'Accept': 'text/html',
            },
            'form_data': {'q': 'mock'} if blueprint['method'] == 'POST' else {},
            'form_fields': {},
        },
        'variables': stack[-1].get('variables') or {},
        'raw_output': json.dumps(meta, ensure_ascii=False, indent=2),
        'security_issues': meta['security_issues'],
        'plugin': app['plugin'],
    }


def build_demo_payload(*, apps: Optional[List[str]] = None, per_app: int = 0) -> Dict[str, Any]:
    """
    Build environments + exceptions for demo seeding.

    per_app=0 → one exception per blueprint rotated across each app's views
    (dense catalogue). Otherwise cap exceptions per application.
    """
    selected = [
        a for a in MOCK_APPS
        if not apps or a['name'] in set(apps)
    ]
    environments: Dict[str, Dict[str, Any]] = {}
    exceptions: List[Dict[str, Any]] = []
    scans: List[Dict[str, Any]] = []

    for app in selected:
        scan_id = make_scan_id(f"demo|{app['name']}|{uuid4().hex[:8]}")
        environments[app['name']] = build_environment(app)
        views = app['views']
        blueprints = list(_EXCEPTION_BLUEPRINTS)
        if per_app > 0:
            blueprints = blueprints[: max(1, per_app)]

        for i, bp in enumerate(blueprints):
            view = views[i % len(views)]
            exceptions.append(
                build_exception_record(app, view, bp, scan_id=scan_id, index=i)
            )

        scans.append({
            'scan_id': scan_id,
            'app': app['name'],
            'plugin': app['plugin'],
            'count': len(blueprints) if per_app == 0 else len(blueprints),
        })

    return {
        'generated_at': _utc(0),
        'apps': [a['name'] for a in selected],
        'scans': scans,
        'environments': environments,
        'exceptions': exceptions,
        'summary': {
            'apps': len(selected),
            'scans': len(scans),
            'exceptions': len(exceptions),
            'environments': len(environments),
        },
    }


def seed_into_server(server: Any, *, reset: bool = True, apps: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Inject demo data into a live DashboardServer instance.
    Persists via existing append/save helpers when available.
    """
    from core.api.backend.vf_server import DashboardException, ExceptionSeverity

    payload = build_demo_payload(apps=apps)
    if reset:
        server.exceptions_store.clear()
        server.environments_store.clear()
        try:
            from core.api.backend.persist import exceptions_path, environments_path
            for p in (exceptions_path(), environments_path()):
                if p.exists():
                    p.unlink()
        except Exception:
            pass

    sev_map = {
        'critical': ExceptionSeverity.CRITICAL,
        'high': ExceptionSeverity.HIGH,
        'medium': ExceptionSeverity.MEDIUM,
        'low': ExceptionSeverity.LOW,
    }

    for name, env in payload['environments'].items():
        server.environments_store[name] = env

    try:
        from core.api.backend.persist import save_environments, append_exception
        save_environments(server.environments_store)
    except Exception:
        append_exception = None  # type: ignore
        save_environments = None  # type: ignore

    for row in payload['exceptions']:
        sev = sev_map.get(str(row.get('severity', 'low')).lower(), ExceptionSeverity.LOW)
        exc = DashboardException(
            id=row['id'],
            scan_id=row.get('scan_id') or '',
            timestamp=row['timestamp'],
            endpoint=row['endpoint'],
            method=row['method'],
            exception_type=row['exception_type'],
            severity=sev,
            description=row['description'],
            stack_trace=row.get('stack_trace') or [],
            request_data=row.get('request_data'),
            variables=row.get('variables'),
            raw_output=row.get('raw_output') or '{}',
            security_issues=row.get('security_issues') or [],
            plugin=row.get('plugin') or '',
        )
        server.exceptions_store.append(exc)
        if append_exception:
            try:
                append_exception(exc.dict())
            except Exception:
                pass

    return {
        **payload['summary'],
        'scans': payload['scans'],
        'apps': payload['apps'],
        'reset': reset,
    }
