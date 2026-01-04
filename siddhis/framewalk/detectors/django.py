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

import re
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from urllib.parse import urljoin

from .base import BaseDetector


class DjangoDetector(BaseDetector):
    """Django-specific detection methods with enhanced capabilities"""
    
    FRAMEWORK = "Django"
    
    # Common Django paths to check
    COMMON_PATHS = [
        '/admin/',
        '/admin/login/',
        '/accounts/login/',
        '/api/',
        '/media/',
    ]
    
    # Django static resource patterns by version
    STATIC_PATTERNS = [
        # Path, Version, Confidence
        ('/static/admin/css/dark_mode.css', '4.2+', 9),
        ('/static/admin/css/nav_sidebar.css', '3.1+', 8),
        ('/static/admin/js/theme.js', '3.2+', 8),
        ('/static/admin/css/responsive.css', '2.0+', 7),
        ('/static/admin/fonts/README.txt', '1.9+', 6),
        ('/static/admin/js/vendor/jquery/jquery.js', '1.8+', 6),
        ('/static/admin/js/vendor/select2/LICENSE.md', '2.0+', 7),
        ('/static/admin/js/filters.js', '3.0+', 7),
        ('/static/admin/js/inlines.js', 'All', 5),
        ('/static/admin/img/tooltag-add.svg', '1.9+', 6),
        ('/static/admin/css/base.css', 'All', 5),
        ('/static/admin/js/admin/DateTimeShortcuts.js', 'All', 6),
        ('/static/admin/js/collapse.js', 'All', 5),
        ('/static/admin/js/prepopulate.js', 'All', 5),
    ]
    
    # Common Django packages to detect
    COMMON_PACKAGES = [
        # Path, Package Name, Description
        ('/admin/wagtail/', 'Wagtail', 'Wagtail CMS'),
        ('/admin_tools/', 'Django Admin Tools', 'Django Admin Tools'),
        ('/cms/', 'Django CMS', 'Django CMS'),
        ('/ckeditor/', 'CKEditor', 'CKEditor integration'),
        ('/admin/filebrowser/', 'FileBrowser', 'Django FileBrowser'),
        ('/markdownx/', 'MarkdownX', 'Django MarkdownX'),
        ('/summernote/', 'Summernote', 'Django Summernote'),
        ('/grappelli/', 'Grappelli', 'Grappelli admin interface'),
        ('/jet/', 'Django Jet', 'Django Jet admin interface'),
        ('/__debug__/render_panel/', 'Debug Toolbar', 'Django Debug Toolbar'),
        ('/graphql', 'Graphene', 'GraphQL integration'),
        ('/admin/debug_toolbar/', 'Debug Toolbar', 'Django Debug Toolbar'),
        ('/rosetta/', 'Rosetta', 'Django Rosetta translation interface'),
        ('/redisboard/', 'Redisboard', 'Redis monitoring'),
    ]
    
    # Django error page patterns
    ERROR_PATTERNS = [
        # Status Code, Pattern, Version, Confidence
        (404, r'<h1>Page not found <span>\(404\)</span></h1>', 'All', 7),
        (500, r'<h1>Server Error <span>\(500\)</span></h1>', 'All', 7),
        (403, r'<h1>Forbidden <span>\(403\)</span></h1>', 'All', 7),
        (404, r'Using the URLconf defined in .+?\.urls', '1.8+', 9),
        (404, r'Django tried these URL patterns', '1.10+', 9),
        (404, r'The current path, .+?, didn\'t match any of these', '2.0+', 9),
        (500, r"You're seeing this error because you have <code>DEBUG = True</code>", '1.10+', 9),
    ]
    
    def detect(self) -> None:
        """Run Django detection methods"""
        # Execute all detection methods
        self._check_common_paths()
        self._check_csrf_patterns()
        self._check_admin_interface()
        self._check_static_patterns()
        self._check_rest_framework()
        self._check_common_packages()
        self._check_error_pages()
        self._check_template_patterns()
        self._check_security_patterns()
        self._check_settings_leaks()
        self._check_response_metadata()
        self.detect_version()
        
    def _add_score(self, 
                  points: int, 
                  evidence_type: str, 
                  detail: str, 
                  raw_data: Optional[Dict[str, Any]] = None) -> None:
        """Add score for Django"""
        self.result_manager.add_score(self.FRAMEWORK, points, evidence_type, detail, raw_data)
        
    def _add_version_hint(self, 
                         version: str, 
                         confidence: int, 
                         evidence: str) -> None:
        """Add version hint for Django"""
        self.result_manager.add_version_hint(self.FRAMEWORK, version, confidence, evidence)
        
    def _add_component(self, 
                      component: str, 
                      evidence: str) -> None:
        """Add component for Django"""
        self.result_manager.add_component(self.FRAMEWORK, component, evidence)
        
    def _check_common_paths(self) -> None:
        """Check for Django-specific paths"""
        for path in self.COMMON_PATHS:
            response = self.request_manager.make_request(path)
            if not response:
                continue
                
            if response.status_code == 200:
                self._add_score(
                    8, 
                    'Endpoint', 
                    f"{path} returns 200 OK",
                    {"url": path, "status": response.status_code}
                )
                
                # Analyze the response content for additional clues
                self._analyze_response(response, path)
                
        # Check for Django admin login redirect (common pattern)
        response = self.request_manager.make_request('/admin')
        if response and response.status_code == 302:
            location = response.headers.get('Location', '')
            if location.endswith('/admin/') or '/admin/login' in location:
                self._add_score(
                    5,
                    'Redirect',
                    f"/admin redirects to {location} (Django pattern)"
                )
                
    def _analyze_response(self, 
                         response: Any, 
                         path: str) -> None:
        """Analyze response content for Django indicators"""
        if not response or not response.text:
            return
            
        content = response.text.lower()
        headers = response.headers
        
        # Look for Django-specific patterns
        patterns = {
            'csrfmiddlewaretoken': ("CSRF middleware token found in HTML", 5),
            'django': ("Django reference in HTML", 2),
            '/static/admin/': ("Django admin static path found", 3),
            'admin/jsi18n': ("Django admin i18n JavaScript", 4),
            'data-admin-utc-offset': ("Django admin UTC offset marker", 7),
            'coltype-checkbox': ("Django admin checkbox pattern", 5),
            'django-admin-prepopulated-fields-constants': ("Django admin prepopulated fields", 6),
            '<tr class="model-': ("Django admin model list pattern", 6),
            'viewlink': ("Django admin view link", 4),
            'data-model-name': ("Django admin model data attribute", 5),
        }
        
        for pattern, (description, points) in patterns.items():
            if pattern in content:
                self._add_score(
                    points, 
                    'Content', 
                    description
                )
                
        # Look for DTL (Django Template Language) patterns
        template_patterns = [
            (r'{%\s+[a-z_]+\s+[^%]+%}', "Django Template Language (DTL) tag syntax"),
            (r'{{\s+[a-z_.]+\s+}}', "Django Template Language (DTL) variable syntax"),
            (r'{#\s+.+?\s+#}', "Django Template Language (DTL) comment syntax"),
            (r'{%\s+if\s+.+?\s+%}', "Django Template Language (DTL) if statement"),
            (r'{%\s+for\s+.+?\s+in\s+.+?\s+%}', "Django Template Language (DTL) for loop"),
            (r'{%\s+block\s+.+?\s+%}', "Django Template Language (DTL) block tag"),
            (r'{%\s+extends\s+.+?\s+%}', "Django Template Language (DTL) extends tag"),
            (r'{%\s+include\s+.+?\s+%}', "Django Template Language (DTL) include tag"),
            (r'{%\s+csrf_token\s+%}', "Django Template Language (DTL) CSRF token tag"),
            (r'{%\s+static\s+.+?\s+%}', "Django Template Language (DTL) static tag"),
            (r'{%\s+url\s+.+?\s+%}', "Django Template Language (DTL) url tag"),
        ]
        
        for pattern, description in template_patterns:
            if re.search(pattern, content):
                self._add_score(
                    4, 
                    'Template', 
                    description
                )
                self._add_component('Django Templates', "DTL syntax in response")
                break  # One template match is enough to indicate Django Templates
                
        # Check for Django admin interface
        admin_patterns = [
            ('django administration', "Django admin interface detected", 10),
            ('log in | django site admin', "Django admin login page", 10),
            ('<div class="login"', "Django admin login form", 8),
            ('<input type="hidden" name="next" value="/admin/"', "Django admin login next parameter", 9),
        ]
        
        for pattern, description, points in admin_patterns:
            if pattern in content:
                self._add_score(
                    points, 
                    'Content', 
                    description
                )
                self._add_component('Django Admin', "Admin interface detected")
                
        # Check for Django Debug Toolbar
        if 'djdt' in content or 'django-debug-toolbar' in content:
            self._add_score(
                10, 
                'Content', 
                "Django Debug Toolbar detected"
            )
            self._add_component('Django Debug Toolbar', "Debug toolbar references in HTML")
            self._add_version_hint('1.8+', 5, "Django Debug Toolbar enabled")
            
        # Check for specific headers that Django sets
        if 'vary' in headers and 'cookie' in headers['vary'].lower():
            self._add_score(
                3,
                'Header',
                "Django-like Vary header with Cookie"
            )
            
        # Check for Django 3.0+ admin features
        if 'data-theme-mode' in content or 'data-popup-opener' in content:
            self._add_version_hint(
                '3.0+',
                7,
                "Django 3.0+ admin attributes detected"
            )
            
        # Check for Django 4.0+ admin features
        if 'data-color-scheme' in content or 'data-filtered' in content:
            self._add_version_hint(
                '4.0+',
                7,
                "Django 4.0+ admin attributes detected"
            )
            
    def _check_csrf_patterns(self) -> None:
        """Check for Django CSRF patterns"""
        response = self.request_manager.make_request()
        if not response:
            return
            
        # Check cookies for CSRF token
        if 'csrftoken' in response.cookies:
            self._add_score(
                8, 
                'Cookie', 
                "CSRF token cookie present"
            )
            
            # Analyze the CSRF token format for version hints 
            csrf_token = response.cookies.get('csrftoken')
            if csrf_token:
                token_str = str(csrf_token)
                if len(token_str) == 64:  # Django 1.10+
                    self._add_version_hint(
                        '1.10+', 
                        5, 
                        "64-character CSRF token length"
                    )
                elif len(token_str) == 32:  # Django 1.4 - 1.9
                    self._add_version_hint(
                        '1.4-1.9', 
                        5, 
                        "32-character CSRF token length"
                    )
                
        # CSRF middleware in POST forms
        content = response.text.lower() if response.text else ""
        if 'csrfmiddlewaretoken' in content:
            self._add_score(
                6, 
                'Content', 
                "CSRF middleware token in forms"
            )
            
            # other CSRF token implementation
            if 'csrf_token' in content:
                self._add_score(
                    3, 
                    'Content', 
                    "CSRF template tag usage"
                )
                
        # For Django 4.0+ → X-CSRFToken header in AJAX requests
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        ajax_response = self.request_manager.make_request('/', headers=headers)
        if ajax_response and 'X-CSRFToken' in ajax_response.headers:
            self._add_score(
                7,
                'Header',
                "X-CSRFToken header in AJAX response"
            )
            self._add_version_hint('1.9+', 5, "X-CSRFToken AJAX support")
                
    def _check_admin_interface(self) -> None:
        """Check Django admin interface patterns"""
        response = self.request_manager.make_request('/admin/login/')
        if not response or response.status_code != 200:
            return
            
        # Look for admin interface patterns in content
        content = response.text.lower()
        
        # Version-specific admin features
        admin_features = [
            # Pattern, Version, Description, Confidence
            ('data-theme-mode', '3.2+', "Admin theme mode toggle", 8),
            ('theme-toggle', '3.2+', "Admin theme toggle", 8),
            ('data-html-class', '4.0+', "Admin HTML class data attribute", 9),
            ('data-color-scheme', '4.0+', "Admin color scheme data attribute", 9),
            ('data-admin-utc-offset', '2.1+', "Admin UTC offset", 7),
            ('responsive', '2.0+', "Responsive admin design", 6),
            ('data-main', '3.0+', "Admin data-main attribute", 7),
            ('django-admin-select2', '3.0+', "Admin Select2 integration", 8),
            ('data-model-name', '4.0+', "Admin model name data attribute", 8),
            ('<div class="breadcrumbs">', '1.11-', "Old admin breadcrumbs", 6),
            ('<form method="post" id="login-form"', 'All', "Admin login form", 5),
        ]
        
        for pattern, version, description, confidence in admin_features:
            if pattern in content:
                self._add_version_hint(
                    version,
                    confidence,
                    f"Admin feature: {description}"
                )
                
        # Check for admin login CSS classes
        if '<div class="login"' in content:
            self._add_score(
                7,
                'Content',
                "Django admin login form structure"
            )
            
        # Check for CSRF token in login form
        if 'csrfmiddlewaretoken' in content:
            self._add_score(
                5,
                'Content',
                "Django admin login CSRF protection"
            )
            
        # Check for theme toggling (Django 3.2+)
        if 'data-theme-mode' in content or 'theme-toggle' in content:
            self._add_component(
                'Django Admin Theme',
                "Dark/light mode support (Django 3.2+)"
            )
            
    def _check_static_patterns(self) -> None:
        """Check for Django static file patterns"""
        for path, version, confidence in self.STATIC_PATTERNS:
            response = self.request_manager.make_request(path)
            if response and response.status_code == 200:
                self._add_version_hint(
                    version,
                    confidence,
                    f"Admin static resource exists: {path}"
                )
                
                # For CSS files, do deeper analysis
                if path.endswith('.css'):
                    self._analyze_css_content(response.text, path, version)
                    
                # For JS files, look for Django patterns
                if path.endswith('.js'):
                    self._analyze_js_content(response.text, path, version)
                    
    def _analyze_css_content(self, content: str, path: str, version: str) -> None:
        """Analyze CSS content for version-specific patterns"""
        # Django 3.2+ dark mode
        if path == '/static/admin/css/dark_mode.css':
            if '[data-theme-mode="dark"]' in content:
                self._add_version_hint('3.2+', 9, "Dark mode CSS with data-theme-mode")
            if 'media (prefers-color-scheme: dark)' in content:
                self._add_version_hint('4.0+', 8, "CSS with prefers-color-scheme")
                
        # Django 4.2+ CSS patterns
        if 'color-scheme:' in content and path.endswith('base.css'):
            self._add_version_hint('4.2+', 8, "CSS with color-scheme property")
            
        # Django 2.0+ responsive admin
        if path == '/static/admin/css/responsive.css':
            if '.sticky' in content:
                self._add_version_hint('3.1+', 5, "Responsive CSS contains .sticky class")
            if '@media (prefers-reduced-motion)' in content:
                self._add_version_hint('4.0+', 8, "CSS with prefers-reduced-motion")
                
    def _analyze_js_content(self, content: str, path: str, version: str) -> None:
        """Analyze JavaScript content for version-specific patterns"""
        # Django 3.2+ theme toggle
        if path == '/static/admin/js/theme.js':
            if 'data-theme-mode' in content:
                self._add_version_hint('3.2+', 9, "Theme.js with data-theme-mode")
            if 'prefers-color-scheme' in content:
                self._add_version_hint('4.0+', 8, "Theme.js with prefers-color-scheme")
                
        # Django admin JS patterns
        if 'django.jQuery' in content:
            self._add_score(5, 'JavaScript', "Django jQuery namespace")
            
        # Django 3.0+ async patterns
        if 'async function' in content or 'await ' in content:
            self._add_version_hint('3.0+', 6, "JavaScript with async/await")
            
        # Django 4.0+ fetch API use
        if '.fetch(' in content:
            self._add_version_hint('4.0+', 7, "JavaScript with fetch API")
            
    def _check_rest_framework(self) -> None:
        """Check for Django REST Framework"""
        # Common DRF paths
        drf_paths = [
            '/api/',
            '/api/schema/',
            '/api-auth/login/',
            '/api/docs/',
            '/swagger/',
            '/redoc/',
            '/api/swagger/',
            '/api/redoc/',
        ]
        
        for path in drf_paths:
            response = self.request_manager.make_request(path)
            if not response:
                continue
                
            if response.status_code == 200:
                content = response.text.lower() if response.text else ""
                headers = response.headers
                
                # Look for DRF signatures
                drf_patterns = [
                    ('rest_framework', "Django REST Framework reference"),
                    ('api-docs', "API documentation"),
                    ('swagger', "Swagger API docs"),
                    ('redoc', "ReDoc API docs"),
                    ('api-explorer', "API explorer"),
                    ('browsable api', "Browsable API reference"),
                    ('drf-yasg', "DRF YASG extension"),
                    ('djangorestframework', "DRF package reference"),
                    ('openapi', "OpenAPI schema"),
                ]
                
                for pattern, description in drf_patterns:
                    if pattern in content:
                        self._add_score(
                            6,
                            'API',
                            f"{description} at {path}"
                        )
                        self._add_component('Django REST Framework', f"API component at {path}")
                        
                # Check for API version hints
                if 'openapi' in content and 'swagger' in content:
                    self._add_component('drf-yasg', "Swagger schema generator")
                    
                if 'spectacular' in content:
                    self._add_component('drf-spectacular', "OpenAPI 3 schema generator")
                    
                # Check for DRF-specific HTTP headers
                if 'allow' in headers:
                    self._add_score(
                        4,
                        'Header',
                        f"DRF Allow header: {headers['allow']}"
                    )
                    
                # jSON API responses
                try:
                    content_type = headers.get('content-type', '')
                    if 'application/json' in content_type:
                        try:
                            json_data = json.loads(response.text)
                            if isinstance(json_data, dict):
                                # DRF patterns in JSON
                                if 'results' in json_data and ('count' in json_data or 'next' in json_data):
                                    self._add_score(
                                        8,
                                        'API',
                                        "DRF pagination pattern in JSON response"
                                    )
                                    self._add_component('DRF Pagination', "Standard pagination detected")
                        except json.JSONDecodeError:
                            pass
                except Exception:
                    pass
                    
    def _check_common_packages(self) -> None:
        """Check for common Django packages/extensions"""
        for path, package, description in self.COMMON_PACKAGES:
            response = self.request_manager.make_request(path)
            if response and response.status_code == 200:
                self._add_score(
                    7,
                    'Package',
                    f"{package} detected at {path}"
                )
                self._add_component(package, description)
                
                # For debug toolbar, also check HTML for references
                if package == 'Debug Toolbar':
                    base_response = self.request_manager.make_request('/')
                    if base_response and base_response.text and 'djdt' in base_response.text.lower():
                        self._add_score(
                            5, 
                            'Package', 
                            "Django Debug Toolbar detected in HTML"
                        )
                        
    def _check_error_pages(self) -> None:
        """Check for Django-specific error pages"""
        # Generate some error responses
        error_paths = [
            # Path, Expected Status
            ('/this_should_not_exist_12345', 404),
            ('/admin/this_should_not_exist', 404),
            ('/media/this_should_not_exist.jpg', 404),
        ]
        
        for path, expected_status in error_paths:
            response = self.request_manager.make_request(path)
            if not response:
                continue
                
            status_code = response.status_code
            if status_code != expected_status:
                continue
                
            content = response.text
            
            # Error patterns
            for code, pattern, version, confidence in self.ERROR_PATTERNS:
                if code == status_code and re.search(pattern, content, re.DOTALL | re.IGNORECASE):
                    self._add_score(
                        7,
                        'Error Page',
                        f"Django-style {status_code} error page"
                    )
                    self._add_version_hint(
                        version, 
                        confidence,
                        f"Error page pattern for Django {version}"
                    )
                    
                    # Look for DEBUG=True in error pages / DMT does this in a different way
                    if re.search(r'DEBUG\s*=\s*True', content):
                        self._add_score(
                            9,
                            'Configuration',
                            "Django DEBUG mode enabled"
                        )
                        
                    # Look for version information in error pages
                    version_match = re.search(r'<div id="info">.*?Django Version: (\d+\.\d+\.\d+).*?</div>', 
                                           content, re.DOTALL | re.IGNORECASE)
                    if version_match:
                        detected_version = version_match.group(1)
                        self._add_version_hint(
                            detected_version,
                            10,
                            f"Explicit Django version in error page: {detected_version}"
                        )
                        
    def _check_template_patterns(self) -> None:
        """Check for Django template engine patterns"""
        response = self.request_manager.make_request('/')
        if not response or not response.text:
            return
            
        content = response.text
        
        # Django template patterns
        template_patterns = [
            (r'{%\s+[a-z_]+\s+[^%]+%}', "Django Template tag"),
            (r'{{\s+[a-z_.]+\s+}}', "Django Template variable"),
            (r'{%\s+if\s+.+?\s+%}', "Django Template if statement"),
            (r'{%\s+for\s+.+?\s+in\s+.+?\s+%}', "Django Template for loop"),
            (r'{%\s+block\s+.+?\s+%}', "Django Template block tag"),
            (r'{%\s+extends\s+.+?\s+%}', "Django Template extends tag"),
            (r'{%\s+include\s+.+?\s+%}', "Django Template include tag"),
            (r'{%\s+csrf_token\s+%}', "Django Template CSRF token tag"),
            (r'{%\s+static\s+.+?\s+%}', "Django Template static tag"),
            (r'{%\s+url\s+.+?\s+%}', "Django Template url tag"),
            (r'{%\s+load\s+.+?\s+%}', "Django Template load tag"),
            (r'{%\s+trans\s+.+?\s+%}', "Django Template trans tag"),
            (r'{%\s+blocktrans\s+.+?\s+%}', "Django Template blocktrans tag"),
            (r'{%\s+comment\s+.+?\s+%}', "Django Template comment tag"),
            (r'{%\s+endblock\s+.+?\s+%}', "Django Template endblock tag"),
            (r'{%\s+endfor\s+%}', "Django Template endfor tag"),
            (r'{%\s+endif\s+%}', "Django Template endif tag"),
            (r'{%\s+endcomment\s+%}', "Django Template endcomment tag"),
            (r'{%\s+endblocktrans\s+%}', "Django Template endblocktrans tag"),
        ]
        
        dtl_patterns_found = 0
        for pattern, description in template_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                dtl_patterns_found += 1
                
        if dtl_patterns_found >= 2:
            self._add_score(
                8,
                'Template',
                f"Multiple Django Template patterns detected ({dtl_patterns_found})"
            )
            self._add_component('Django Templates', "Multiple DTL patterns detected")
            
            if re.search(r'{%\s+blocktrans\s+', content, re.IGNORECASE):
                self._add_version_hint('1.4-3.0', 6, "blocktrans tag (pre-Django 3.1)")
                
            if re.search(r'{%\s+translate\s+', content, re.IGNORECASE):
                self._add_version_hint('3.1+', 8, "translate tag (Django 3.1+)")
                
    def _check_security_patterns(self) -> None:
        """Check for Django security patterns"""
        response = self.request_manager.make_request('/')
        if not response:
            return
            
        headers = response.headers
        
        # Django security headers
        if 'x-frame-options' in headers and headers['x-frame-options'].upper() == 'SAMEORIGIN':
            self._add_score(
                5,
                'Security',
                "Django default X-Frame-Options: SAMEORIGIN"
            )
            
        # Django 4.0+ default security headers
        if 'referrer-policy' in headers:
            self._add_version_hint('2.1+', 5, "Django Referrer-Policy header")
            
        if 'x-content-type-options' in headers and headers['x-content-type-options'].lower() == 'nosniff':
            self._add_version_hint('3.0+', 6, "Django X-Content-Type-Options: nosniff")
            
        # Django 4.0+ security features
        for header in ['cross-origin-opener-policy', 'permissions-policy']:
            if header in headers:
                self._add_version_hint('4.0+', 8, f"Django {header} security header")
                
        # Check for non-field errors class (Django-specific)
        if response.text and 'errorlist nonfield' in response.text.lower():
            self._add_score(
                6,
                'Form',
                "Django non-field errors element"
            )
            
    def _check_settings_leaks(self) -> None:
        """Check for Django settings leaks (especially in DEBUG mode)"""
        # Common Django paths that might leak settings
        leak_paths = [
            '/',
            '/admin/',
            '/debug/',
            '/__debug__/',
            '/app-config/',
            '/api/docs/',
        ]
        
        for path in leak_paths:
            response = self.request_manager.make_request(path)
            if not response or not response.text:
                continue
                
            content = response.text.lower()
            
            # Look for settings module references
            settings_patterns = [
                (r'settings\.py', "Django settings.py file reference"),
                (r'django\.conf\.settings', "Django settings module reference"),
                (r'DEBUG\s*=\s*True', "Django DEBUG mode enabled"),
                (r'ALLOWED_HOSTS\s*=', "Django ALLOWED_HOSTS setting"),
                (r'INSTALLED_APPS\s*=', "Django INSTALLED_APPS setting"),
                (r'MIDDLEWARE\s*=', "Django MIDDLEWARE setting"),
                (r'DATABASES\s*=', "Django DATABASES setting"),
                (r'SECRET_KEY\s*=', "Django SECRET_KEY setting"),
            ]
            
            for pattern, description in settings_patterns:
                if re.search(pattern, content):
                    self._add_score(
                        9,
                        'Configuration',
                        description
                    )
                    
        # Check for Django Debug Toolbar
        debug_response = self.request_manager.make_request('/__debug__/render_panel/')
        if debug_response and debug_response.status_code != 404:
            self._add_score(
                10,
                'Debug',
                "Django Debug Toolbar detected (__debug__ endpoint)"
            )
            self._add_component('Django Debug Toolbar', "Debug URLs exposed")
            
    def _check_response_metadata(self) -> None:
        """Check for Django-specific response metadata"""
        response = self.request_manager.make_request('/')
        if not response:
            return
            
        headers = response.headers
        cookies = response.cookies
        
        # Check for Django session cookie
        if 'sessionid' in cookies:
            self._add_score(
                8,
                'Cookie',
                "Django session cookie detected"
            )
            self._add_component('Django Sessions', "sessionid cookie")
            
            # Django 1.8+ changed how session cookies work
            if cookies.get('sessionid') and 'httponly' in str(cookies.get('sessionid')).lower():
                self._add_version_hint('1.8+', 5, "HttpOnly Session Cookie (Django 1.8+)")
                
        # Look for Django version comment
        content = response.text
        version_match = re.search(r'<!-- Rendered by Django (\d+\.\d+\.\d+) -->', content)
        if version_match:
            version = version_match.group(1)
            self._add_version_hint(
                version,
                10,
                f"Django version comment: {version}"
            )
            
        # X-Frame-Options with other content
        if 'x-frame-options' in headers:
            value = headers['x-frame-options'].lower()
            if value != 'sameorigin' and value != 'deny' and 'allow-from' in value:
                self._add_version_hint('1.3-3.0', 6, "X-Frame-Options with allow-from (pre-Django 3.1)")
                
        # Vary header with Cookie
        if 'vary' in headers and 'cookie' in headers['vary'].lower():
            self._add_score(
                3,
                'Header',
                "Django-like Vary header with Cookie"
            )
            
    def detect_version(self) -> None:
        """Attempt to determine Django version from various signals"""
        # Version comment in HTML source
        response = self.request_manager.make_request('/')
        if not response:
            return
            
        content = response.text
        
        # Version in HTML comments
        version_patterns = [
            (r'<!-- Rendered by Django (\d+\.\d+\.\d+) -->', 10),
            (r'<!-- Django Version: (\d+\.\d+\.\d+) -->', 10),
            (r'<meta name="generator" content="Django (\d+\.\d+\.\d+)"', 10),
            (r'__version__ = \'(\d+\.\d+\.\d+)\'', 8),
            (r'Django/(\d+\.\d+\.\d+)', 9),
            (r'django-version: (\d+\.\d+\.\d+)', 9),
        ]
        
        for pattern, confidence in version_patterns:
            version_match = re.search(pattern, content)
            if version_match:
                version = version_match.group(1)
                self._add_version_hint(
                    version,
                    confidence,
                    f"Django version signature: {version}"
                )
                
        # Check 404 page for version info
        response_404 = self.request_manager.make_request('/this_should_not_exist_12345')
        if response_404:
            content_404 = response_404.text
            
            # debug info leak in 404 pages: djunch also checks it sometimes
            for pattern, confidence in version_patterns:
                version_match = re.search(pattern, content_404)
                if version_match:
                    version = version_match.group(1)
                    self._add_version_hint(
                        version,
                        confidence,
                        f"Django version in 404 page: {version}"
                    )
                    
            # Django 2.0+ 404 pages mention URLconf
            if 'urlconf' in content_404.lower():
                self._add_version_hint('1.10+', 5, "URLconf mentioned in 404 page")
                
            # Django 3.0+ 404 pages have a specific structure
            if re.search(r'The current path, .+?, didn\'t match', content_404):
                self._add_version_hint('2.0+', 7, "Django 2.0+ style 404 message")
                
        # Add a check for Django 5.0 features
        response_admin = self.request_manager.make_request('/admin/')
        if response_admin and response_admin.text:
            content_admin = response_admin.text.lower()
            
            # Django 5.0 specific features
            if 'data-admin-color-theme' in content_admin:
                self._add_version_hint('5.0+', 10, "Django 5.0+ admin color theme data attribute")
                
            if 'module-theme' in content_admin or 'data-color-mode' in content_admin:
                self._add_version_hint('5.0+', 9, "Django 5.0+ admin theme attributes")