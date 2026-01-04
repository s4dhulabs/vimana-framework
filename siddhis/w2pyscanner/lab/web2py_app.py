#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vulnerable Web2py Application for W2PyScanner Testing

This application contains intentional security vulnerabilities for testing:
- Exposed admin interface with weak credentials
- File upload vulnerabilities
- Session management issues
- CSRF protection bypasses
- Information disclosure
- Database exposure
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi
import time
import traceback

DEBUG_MODE = True

# Simple Web2py-like application for testing
class VulnerableWeb2pyApp:
    def __init__(self):
        self.admin_password = 'admin123'
        self.admin_email = 'admin@example.com'
        self.session_data = {}
        self.upload_dir = 'uploads'
        
        # Create uploads directory
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Create database
        self.init_database()

    def init_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect('storage.sqlite')
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                session_id TEXT UNIQUE,
                user_id INTEGER,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default admin user
        cursor.execute('''
            INSERT OR IGNORE INTO users (email, password) 
            VALUES (?, ?)
        ''', (self.admin_email, self.admin_password))
        
        conn.commit()
        conn.close()

    def generate_session_id(self):
        """Generate a session ID."""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def get_session(self, session_id):
        """Get session data."""
        if session_id in self.session_data:
            return self.session_data[session_id]
        return None

    def set_session(self, session_id, data):
        """Set session data."""
        data['created_at'] = time.time()
        self.session_data[session_id] = data

# Create a global app instance
app_instance = VulnerableWeb2pyApp()

class VulnerableHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.app = app_instance
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)
        
        # Session cookie logic
        session_id = self.get_cookie('session_id')
        session = self.app.get_session(session_id) if session_id else None
        
        if path == '/':
            content = self.handle_index()
        elif path == '/login':
            self.handle_login_page()
            return
        elif path == '/logout':
            self.handle_logout()
            return
        elif path == '/profile':
            self.handle_profile(session)
            return
        elif path == '/leak_session':
            content = self.handle_leak_session(session_id)
        elif path == '/admin/':
            content = self.handle_admin()
        elif path == '/about':
            content = self.handle_about()
        elif path == '/upload':
            content = self.handle_upload_page()
        elif path == '/api':
            content = self.handle_api(query)
        elif path == '/database':
            content = self.handle_database()
        elif path == '/session_test':
            content = self.handle_session_test(query)
        elif path == '/csrf_test':
            content = self.handle_csrf_test()
        elif path == '/error':
            content = self.handle_error(query)
        elif path == '/exception_test':
            content = self.handle_exception_test(query)
        elif path == '/debug_info':
            content = self.handle_debug_info()
        elif path == '/config_leak':
            content = self.handle_config_leak()
        elif path == '/stack_trace':
            content = self.handle_stack_trace()
        elif path == '/sql_injection':
            content = self.handle_sql_injection(query)
        elif path == '/file_access':
            content = self.handle_file_access(query)
        else:
            content = self.handle_404()
        if 'content' in locals():
            self.send_response(200)
            self.send_header('X-Powered-By', 'web2py')
            self.send_header('Server', 'Rocket3')
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

    def do_POST(self):
        """Handle POST requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/admin/login':
            content = self.handle_admin_login()
        elif path == '/login':
            self.handle_login()
            return
        elif path == '/upload':
            content = self.handle_file_upload()
        elif path == '/csrf_test':
            content = self.handle_csrf_action()
        else:
            content = self.handle_404()
        if 'content' in locals():
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('X-Powered-By', 'web2py')
            self.send_header('Server', 'Rocket3')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

    def handle_index(self):
        """Main page with admin interface indicators."""
        session_id = self.generate_session_id()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>Welcome to Vulnerable Web2py App</h1>
            <p>This is a vulnerable Web2py application for security testing</p>
            
            <h2>Admin Information (Intentionally Exposed)</h2>
            <ul>
                <li>Admin URL: <a href="/admin/">/admin/</a></li>
                <li>Admin Email: {self.app.admin_email}</li>
                <li>Admin Password: {self.app.admin_password}</li>
                <li>Session ID: {session_id}</li>
                <li>Applications: welcome, admin, examples</li>
                <li>Database Path: applications/welcome/databases/storage.sqlite</li>
            </ul>
            
            <h2>Available Endpoints</h2>
            <ul>
                <li><a href="/about">About Page</a></li>
                <li><a href="/admin/">Admin Interface</a></li>
                <li><a href="/upload">File Upload</a></li>
                <li><a href="/api">API Endpoint</a></li>
                <li><a href="/database">Database Info</a></li>
                <li><a href="/session_test">Session Test</a></li>
                <li><a href="/csrf_test">CSRF Test</a></li>
                <li><a href="/error">Error Page</a></li>
                <li><a href="/leak_session">Session Leak</a></li>
                <li><a href="/exception_test">Exception Test</a></li>
                <li><a href="/debug_info">Debug Info</a></li>
                <li><a href="/config_leak">Config Leak</a></li>
                <li><a href="/stack_trace">Stack Trace</a></li>
                <li><a href="/sql_injection">SQL Injection</a></li>
                <li><a href="/file_access">File Access</a></li>
            </ul>
            
            <p>Current Time: {datetime.now()}</p>
        </body>
        </html>
        """
        return html

    def handle_admin(self):
        """Admin interface."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Web2py Admin Interface</title>
        </head>
        <body>
            <h1>Web2py Administration</h1>
            <p>Welcome to the Web2py admin interface</p>
            
            <h2>Manage Applications</h2>
            <ul>
                <li><a href="/admin/default/manage">Manage Applications</a></li>
                <li><a href="/admin/default/design">Design Applications</a></li>
                <li><a href="/admin/default/edit">Edit Applications</a></li>
                <li><a href="/admin/default/upload">Upload Applications</a></li>
                <li><a href="/admin/default/backup">Backup Applications</a></li>
                <li><a href="/admin/default/restore">Restore Applications</a></li>
            </ul>
            
            <h2>Login</h2>
            <form method="POST" action="/admin/login">
                <p>Email: <input type="email" name="email" value="{self.app.admin_email}"></p>
                <p>Password: <input type="password" name="password" value="{self.app.admin_password}"></p>
                <p><input type="submit" value="Login"></p>
            </form>
            
            <p>Session ID: {self.generate_session_id()}</p>
        </body>
        </html>
        """
        return html

    def handle_about(self):
        """About page with information disclosure."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>About - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>About</h1>
            <p>This page intentionally exposes sensitive information</p>
            
            <h2>Sensitive Information (Intentionally Exposed)</h2>
            <ul>
                <li>Web2py Version: 2.22.4</li>
                <li>Python Version: {sys.version}</li>
                <li>Database Path: applications/welcome/databases/storage.sqlite</li>
                <li>Admin Credentials: {self.app.admin_email}:{self.app.admin_password}</li>
                <li>Debug Mode: True</li>
                <li>Secret Key: vulnerable_secret_key_12345</li>
                <li>Database URL: sqlite://storage.sqlite</li>
            </ul>
        </body>
        </html>
        """
        return html

    def handle_upload_page(self):
        """File upload page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>File Upload - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>File Upload</h1>
            <p>This endpoint is vulnerable to file upload attacks</p>
            
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <p>Select file: <input type="file" name="file"></p>
                <p><input type="submit" value="Upload"></p>
            </form>
            
            <p><strong>Vulnerabilities:</strong></p>
            <ul>
                <li>No file type validation</li>
                <li>No file size limits</li>
                <li>No path traversal protection</li>
                <li>Accepts any file type including PHP, shell scripts</li>
            </ul>
        </body>
        </html>
        """
        return html

    def handle_api(self, query):
        """API endpoint with weak authentication."""
        api_key = query.get('api_key', [''])[0] or self.headers.get('X-API-Key', '')
        
        if api_key == 'vulnerable_api_key_12345' or not api_key:
            data = {
                'status': 'success',
                'message': 'API accessible with weak authentication',
                'timestamp': datetime.now().isoformat(),
                'session_id': self.generate_session_id(),
                'admin_url': '/admin/',
                'database_path': 'applications/welcome/databases/storage.sqlite'
            }
            self.send_header('Content-type', 'application/json')
            return json.dumps(data, indent=2)
        else:
            data = {'status': 'error', 'message': 'Invalid API key'}
            self.send_header('Content-type', 'application/json')
            return json.dumps(data, indent=2)

    def handle_database(self):
        """Exposed database endpoint."""
        try:
            conn = sqlite3.connect('storage.sqlite')
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Get some data from tables
            data = {}
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    data[table_name] = rows
                except:
                    pass
            
            conn.close()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Database Exposure - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>Database Exposure</h1>
                <p>Database intentionally exposed for testing</p>
                
                <h2>Database Path</h2>
                <p>applications/welcome/databases/storage.sqlite</p>
                
                <h2>Tables</h2>
                <ul>
                    {''.join([f'<li>{table[0]}</li>' for table in tables])}
                </ul>
                
                <h2>Data (Intentionally Exposed)</h2>
                <pre>{json.dumps(data, indent=2)}</pre>
            </body>
            </html>
            """
            return html
            
        except Exception as e:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Database Exposure - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>Database Exposure</h1>
                <p>Error accessing database: {str(e)}</p>
            </body>
            </html>
            """
            return html

    def handle_session_test(self, query):
        """Session management test endpoint."""
        session_id = self.generate_session_id()
        test_var = query.get('test_var', ['default_value'])[0]
        
        session_data = {
            'session_id': session_id,
            'test_var': test_var,
            'timestamp': datetime.now().isoformat(),
            'user_agent': self.headers.get('User-Agent', ''),
            'remote_addr': self.client_address[0]
        }
        
        self.app.set_session(session_id, session_data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Session Test - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>Session Test</h1>
            <p>Session information intentionally exposed</p>
            
            <h2>Session Information (Intentionally Exposed)</h2>
            <pre>{json.dumps(session_data, indent=2)}</pre>
            
            <h2>Test Session</h2>
            <form method="GET" action="/session_test">
                <p>Test Variable: <input type="text" name="test_var" value="{test_var}"></p>
                <p><input type="submit" value="Update Session"></p>
            </form>
        </body>
        </html>
        """
        return html

    def handle_csrf_test(self):
        """CSRF protection test endpoint."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSRF Test - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>CSRF Test</h1>
            <p>This endpoint is vulnerable to CSRF attacks</p>
            
            <h2>Dangerous Actions (CSRF Vulnerable)</h2>
            <form method="POST" action="/csrf_test">
                <input type="hidden" name="action" value="delete_user">
                <input type="submit" value="Delete User (CSRF Test)">
            </form>
            
            <form method="POST" action="/csrf_test">
                <input type="hidden" name="action" value="change_password">
                <input type="submit" value="Change Password (CSRF Test)">
            </form>
            
            <p><strong>Vulnerabilities:</strong></p>
            <ul>
                <li>No CSRF token validation</li>
                <li>No origin checking</li>
                <li>No referer validation</li>
                <li>Accepts any POST request without verification</li>
            </ul>
        </body>
        </html>
        """
        return html

    def handle_error(self, query):
        """Error page with information disclosure."""
        error_type = query.get('type', ['general'])[0]
        
        if error_type == 'database':
            error_info = {
                'error_type': 'Database Error',
                'error_message': 'Table non_existent_table does not exist',
                'sql_query': 'SELECT * FROM non_existent_table',
                'database_path': 'applications/welcome/databases/storage.sqlite',
                'web2py_version': '2.22.4',
                'python_version': sys.version,
                'stack_trace': 'Full stack trace would be here in debug mode'
            }
        elif error_type == 'file':
            error_info = {
                'error_type': 'File Error',
                'error_message': 'No such file or directory: non_existent_file.txt',
                'file_path': 'non_existent_file.txt',
                'current_directory': os.getcwd(),
                'file_permissions': 'File permissions would be here'
            }
        else:
            error_info = {
                'error_type': 'General Error',
                'error_message': 'This is a test error for security testing',
                'debug_info': 'Debug information would be exposed here',
                'server_info': {
                    'web2py_version': '2.22.4',
                    'python_version': sys.version,
                    'platform': sys.platform
                }
            }
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>Error Page</h1>
            <p>This error page intentionally exposes sensitive information</p>
            
            <h2>Error Information (Intentionally Exposed)</h2>
            <pre>{json.dumps(error_info, indent=2)}</pre>
            
            <h2>Test Different Errors</h2>
            <ul>
                <li><a href="/error?type=database">Database Error</a></li>
                <li><a href="/error?type=file">File Error</a></li>
                <li><a href="/error?type=general">General Error</a></li>
            </ul>
        </body>
        </html>
        """
        return html

    def handle_404(self):
        """404 page with information disclosure."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 Not Found - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>404 Not Found</h1>
            <p>This 404 page intentionally exposes application structure</p>
            
            <h2>Requested URL</h2>
            <p>{self.path}</p>
            
            <h2>Available Endpoints (Intentionally Exposed)</h2>
            <ul>
                <li>/ (index)</li>
                <li>/admin/</li>
                <li>/about</li>
                <li>/upload</li>
                <li>/api</li>
                <li>/database</li>
                <li>/session_test</li>
                <li>/csrf_test</li>
                <li>/error</li>
            </ul>
            
            <h2>Server Information (Intentionally Exposed)</h2>
            <ul>
                <li>Server: Rocket3</li>
                <li>X-Powered-By: web2py</li>
                <li>Python Version: {sys.version}</li>
                <li>Platform: {sys.platform}</li>
            </ul>
        </body>
        </html>
        """
        return html

    def handle_admin_login(self):
        """Handle admin login."""
        # Parse form data
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = parse_qs(post_data)
        
        email = form_data.get('email', [''])[0]
        password = form_data.get('password', [''])[0]
        
        if email == self.app.admin_email and password == self.app.admin_password:
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Admin Dashboard - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>Admin Dashboard</h1>
                <p>Welcome to the admin dashboard!</p>
                
                <h2>Manage Applications</h2>
                <ul>
                    <li><a href="/admin/default/manage">Manage Applications</a></li>
                    <li><a href="/admin/default/design">Design Applications</a></li>
                    <li><a href="/admin/default/edit">Edit Applications</a></li>
                    <li><a href="/admin/default/upload">Upload Applications</a></li>
                    <li><a href="/admin/default/backup">Backup Applications</a></li>
                    <li><a href="/admin/default/restore">Restore Applications</a></li>
                </ul>
                
                <p><strong>Login successful with default credentials!</strong></p>
            </body>
            </html>
            """
        else:
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Admin Login - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>Admin Login</h1>
                <p>Invalid credentials. Try admin@example.com / admin123</p>
                
                <form method="POST" action="/admin/login">
                    <p>Email: <input type="email" name="email"></p>
                    <p>Password: <input type="password" name="password"></p>
                    <p><input type="submit" value="Login"></p>
                </form>
            </body>
            </html>
            """
        
        return html

    def handle_login_page(self):
        self.send_response(200)
        self.send_header('X-Powered-By', 'web2py')
        self.send_header('Server', 'Rocket3')
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"""
        <html><head><title>Login</title></head><body>
        <h1>Login</h1>
        <form method='POST' action='/login'>
        Email: <input name='email' type='text'><br>
        Password: <input name='password' type='password'><br>
        <input type='submit' value='Login'>
        </form>
        </body></html>
        """)

    def handle_login(self):
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.get('content-length'))
            postvars = parse_qs(self.rfile.read(length).decode('utf-8'), keep_blank_values=1)
        else:
            postvars = {}
        email = postvars.get('email', [''])[0]
        password = postvars.get('password', [''])[0]
        # Validate user
        conn = sqlite3.connect('storage.sqlite')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email=? AND password=?', (email, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            # Authenticated
            session_id = self.app.generate_session_id()
            self.app.set_session(session_id, {'user_id': row[0], 'email': email})
            self.send_response(302)
            self.send_header('Set-Cookie', f'session_id={session_id}; HttpOnly; Path=/')
            self.send_header('Location', '/profile')
            self.send_header('X-Powered-By', 'web2py')
            self.send_header('Server', 'Rocket3')
            self.end_headers()
            return
        else:
            self.send_response(401)
            self.send_header('X-Powered-By', 'web2py')
            self.send_header('Server', 'Rocket3')
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"Login failed")
            return

    def handle_logout(self):
        session_id = self.get_cookie('session_id')
        if session_id and session_id in self.app.session_data:
            del self.app.session_data[session_id]
        self.send_response(302)
        self.send_header('Set-Cookie', 'session_id=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/')
        self.send_header('Location', '/')
        self.send_header('X-Powered-By', 'web2py')
        self.send_header('Server', 'Rocket3')
        self.end_headers()

    def handle_profile(self, session):
        session_timeout = 5  # seconds, for testing
        if session:
            now = time.time()
            created = session.get('created_at', now)
            if now - created > session_timeout:
                # Expire session
                for sid, sdata in list(self.app.session_data.items()):
                    if sdata is session:
                        del self.app.session_data[sid]
                        break
                self.send_response(401)
                self.send_header('X-Powered-By', 'web2py')
                self.send_header('Server', 'Rocket3')
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(b"Session expired. Please <a href='/login'>login</a>.")
                return
            self.send_response(200)
            self.send_header('X-Powered-By', 'web2py')
            self.send_header('Server', 'Rocket3')
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"<html><body><h1>Profile</h1><p>Email: {session['email']}</p></body></html>".encode())
        else:
            self.send_response(401)
            self.send_header('X-Powered-By', 'web2py')
            self.send_header('Server', 'Rocket3')
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"Unauthorized. Please <a href='/login'>login</a>.")

    def handle_file_upload(self):
        """Handle file upload."""
        try:
            # Parse multipart form data
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            if 'file' in form:
                uploaded_file = form['file']
                filename = uploaded_file.filename
                
                # Vulnerable file upload - no validation
                upload_path = os.path.join(self.app.upload_dir, filename)
                with open(upload_path, 'wb') as f:
                    f.write(uploaded_file.file.read())
                
                message = f"File {filename} uploaded successfully to {upload_path}"
            else:
                message = "No file uploaded"
                
        except Exception as e:
            message = f"Upload error: {str(e)}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>File Upload - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>File Upload</h1>
            <p>{message}</p>
            
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <p>Select file: <input type="file" name="file"></p>
                <p><input type="submit" value="Upload"></p>
            </form>
        </body>
        </html>
        """
        return html

    def handle_csrf_action(self):
        """Handle CSRF vulnerable actions."""
        # Parse form data
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = parse_qs(post_data)
        
        action = form_data.get('action', [''])[0]
        
        if action == 'delete_user':
            result = f"User deleted (CSRF vulnerable) - Action: {action}"
        elif action == 'change_password':
            result = f"Password changed (CSRF vulnerable) - Action: {action}"
        else:
            result = f"Action performed (CSRF vulnerable) - Action: {action}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSRF Test - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>CSRF Test</h1>
            <p>{result}</p>
            
            <p><strong>This action was performed without CSRF protection!</strong></p>
            
            <a href="/csrf_test">Back to CSRF Test</a>
        </body>
        </html>
        """
        return html

    def generate_session_id(self):
        """Generate a session ID."""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

    def get_cookie(self, name):
        cookies = self.headers.get('Cookie')
        if not cookies:
            return None
        for cookie in cookies.split(';'):
            if '=' in cookie:
                k, v = cookie.strip().split('=', 1)
                if k == name:
                    return v
        return None

    def handle_leak_session(self, session_id):
        # Leak session ID in URL, HTML, and JS
        sid = session_id or 'none'
        html = f"""
        <html><head><title>Session Leak</title></head><body>
        <h1>Session Leak Demo</h1>
        <a href='/profile?session_id={sid}'>Profile (leaked in URL)</a><br>
        <div>Session ID in HTML: <span id='sid'>{sid}</span></div>
        <script>var sessionId = '{sid}'; // Leaked in JS</script>
        </body></html>
        """
        return html

    def handle_exception_test(self, query):
        """Test endpoint that triggers actual Python exceptions."""
        exception_type = query.get('type', ['division'])[0]
        
        try:
            if exception_type == 'division':
                result = 1 / 0
            elif exception_type == 'attribute':
                result = None.some_attribute
            elif exception_type == 'index':
                result = [1, 2, 3][10]
            elif exception_type == 'key':
                result = {'a': 1}['b']
            elif exception_type == 'import':
                import non_existent_module
            elif exception_type == 'file':
                with open('/non/existent/file.txt', 'r') as f:
                    result = f.read()
            elif exception_type == 'database':
                conn = sqlite3.connect('storage.sqlite')
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM non_existent_table")
                result = cursor.fetchall()
                conn.close()
            else:
                raise Exception(f"Test exception of type: {exception_type}")
        except Exception as e:
            import traceback
            if DEBUG_MODE:
                tb = e.__traceback__
                frames = traceback.extract_tb(tb)
                frame_details = []
                while tb:
                    frame = tb.tb_frame
                    lineno = tb.tb_lineno
                    code = frame.f_code
                    local_vars = {k:repr(v) for k,v in frame.f_locals.items()}
                    frame_details.append(f"File: {code.co_filename}, Line: {lineno}, Function: {code.co_name}\n  Locals: {local_vars}")
                    tb = tb.tb_next
                # Request info
                headers = getattr(self, 'headers', {})
                cookies = self.headers.get('Cookie', '') if hasattr(self, 'headers') else ''
                post_data = ''
                if self.command == 'POST':
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Exception Test - Vulnerable Web2py App</title>
                </head>
                <body>
                    <h1>Exception Test</h1>
                    <p>Exception type: {exception_type}</p>
                    <h2>Exception Details (Intentionally Exposed)</h2>
                    <pre>
Exception Type: {type(e).__name__}
Exception Message: {str(e)}
Exception Args: {e.args}

Full Traceback:
{traceback.format_exc()}

Stack Frames:
{chr(10).join(frame_details)}

Request Headers:
{headers}

Cookies:
{cookies}

POST Data:
{post_data}

Debug Information:
- Python Version: {sys.version}
- Platform: {sys.platform}
- Current Working Directory: {os.getcwd()}
- Environment Variables: {dict(os.environ)}
- Process ID: {os.getpid()}
- User ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}
                    </pre>
                    <h2>Test Different Exceptions</h2>
                    <ul>
                        <li><a href="/exception_test?type=division">Division by Zero</a></li>
                        <li><a href="/exception_test?type=attribute">Attribute Error</a></li>
                        <li><a href="/exception_test?type=index">Index Error</a></li>
                        <li><a href="/exception_test?type=key">Key Error</a></li>
                        <li><a href="/exception_test?type=import">Import Error</a></li>
                        <li><a href="/exception_test?type=file">File Not Found</a></li>
                        <li><a href="/exception_test?type=database">Database Error</a></li>
                    </ul>
                </body>
                </html>
                """
            else:
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Exception Test - Vulnerable Web2py App</title>
                </head>
                <body>
                    <h1>Exception Test</h1>
                    <p>Exception type: {exception_type}</p>
                    <h2>Exception Occurred</h2>
                    <pre>
An error occurred while processing your request. Please contact the administrator.
                    </pre>
                </body>
                </html>
                """
            return html

    def handle_debug_info(self):
        """Expose debug information and system details."""
        import platform
        import psutil
        
        try:
            cpu_info = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
        except:
            cpu_info = "N/A"
            memory_info = "N/A"
            disk_info = "N/A"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Debug Info - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>Debug Information (Intentionally Exposed)</h1>
            
            <h2>System Information</h2>
            <ul>
                <li>Python Version: {sys.version}</li>
                <li>Platform: {sys.platform}</li>
                <li>Architecture: {platform.architecture()}</li>
                <li>Machine: {platform.machine()}</li>
                <li>Processor: {platform.processor()}</li>
                <li>Hostname: {platform.node()}</li>
            </ul>
            
            <h2>Process Information</h2>
            <ul>
                <li>Process ID: {os.getpid()}</li>
                <li>User ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}</li>
                <li>Current Working Directory: {os.getcwd()}</li>
                <li>CPU Usage: {cpu_info}%</li>
                <li>Memory Usage: {memory_info}</li>
                <li>Disk Usage: {disk_info}</li>
            </ul>
            
            <h2>Environment Variables</h2>
            <pre>{dict(os.environ)}</pre>
            
            <h2>Application Configuration</h2>
            <ul>
                <li>Admin Email: {self.app.admin_email}</li>
                <li>Admin Password: {self.app.admin_password}</li>
                <li>Database Path: applications/welcome/databases/storage.sqlite</li>
                <li>Upload Directory: {self.app.upload_dir}</li>
                <li>Debug Mode: True</li>
                <li>Secret Key: vulnerable_secret_key_12345</li>
            </ul>
        </body>
        </html>
        """
        return html

    def handle_config_leak(self):
        """Expose configuration files and sensitive settings."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Configuration Leak - Vulnerable Web2py App</title>
        </head>
        <body>
            <h1>Configuration Information (Intentionally Exposed)</h1>
            
            <h2>Database Configuration</h2>
            <pre>
DATABASE_CONFIG = {{
    'type': 'sqlite',
    'path': 'applications/welcome/databases/storage.sqlite',
    'url': 'sqlite://storage.sqlite',
    'pool_size': 10,
    'max_overflow': 20,
    'echo': True
}}
            </pre>
            
            <h2>Security Configuration</h2>
            <pre>
SECURITY_CONFIG = {{
    'secret_key': 'vulnerable_secret_key_12345',
    'session_timeout': 3600,
    'csrf_protection': False,
    'debug_mode': True,
    'admin_email': '{self.app.admin_email}',
    'admin_password': '{self.app.admin_password}'
}}
            </pre>
            
            <h2>Application Configuration</h2>
            <pre>
APP_CONFIG = {{
    'name': 'vulnerable_web2py_app',
    'version': '1.0.0',
    'debug': True,
    'host': '0.0.0.0',
    'port': 8080,
    'upload_dir': '{self.app.upload_dir}',
    'allowed_extensions': ['*'],
    'max_file_size': '100MB'
}}
            </pre>
            
            <h2>Server Configuration</h2>
            <pre>
SERVER_CONFIG = {{
    'server': 'Rocket3',
    'x_powered_by': 'web2py',
    'content_type': 'text/html; charset=utf-8',
    'cors_enabled': True,
    'cors_origins': ['*']
}}
            </pre>
        </body>
        </html>
        """
        return html

    def handle_stack_trace(self):
        """Generate a realistic stack trace with sensitive information."""
        try:
            def inner_function():
                def deeper_function():
                    non_existent_variable = undefined_variable
                deeper_function()
            inner_function()
        except Exception as e:
            import traceback
            if DEBUG_MODE:
                tb = e.__traceback__
                frames = traceback.extract_tb(tb)
                frame_details = []
                while tb:
                    frame = tb.tb_frame
                    lineno = tb.tb_lineno
                    code = frame.f_code
                    local_vars = {k:repr(v) for k,v in frame.f_locals.items()}
                    frame_details.append(f"File: {code.co_filename}, Line: {lineno}, Function: {code.co_name}\n  Locals: {local_vars}")
                    tb = tb.tb_next
                headers = getattr(self, 'headers', {})
                cookies = self.headers.get('Cookie', '') if hasattr(self, 'headers') else ''
                post_data = ''
                if self.command == 'POST':
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ''
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Stack Trace - Vulnerable Web2py App</title>
                </head>
                <body>
                    <h1>Stack Trace (Intentionally Exposed)</h1>
                    <h2>Exception Information</h2>
                    <pre>
Exception Type: {type(e).__name__}
Exception Message: {str(e)}
Exception Args: {e.args}
                    </pre>
                    <h2>Full Stack Trace</h2>
                    <pre>{traceback.format_exc()}</pre>
                    <h2>Stack Frames</h2>
                    <pre>{chr(10).join(frame_details)}</pre>
                    <h2>Request Headers</h2>
                    <pre>{headers}</pre>
                    <h2>Cookies</h2>
                    <pre>{cookies}</pre>
                    <h2>POST Data</h2>
                    <pre>{post_data}</pre>
                    <h2>Debug Context</h2>
                    <pre>
File: {__file__}
Local Variables:
- admin_email: {self.app.admin_email}
- admin_password: {self.app.admin_password}
- session_data: {self.app.session_data}
- upload_dir: {self.app.upload_dir}
- Python Version: {sys.version}
- Platform: {sys.platform}
- Current Working Directory: {os.getcwd()}
- Environment Variables: {dict(os.environ)}
- Process ID: {os.getpid()}
- User ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}
                    </pre>
                </body>
                </html>
                """
            else:
                html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Stack Trace - Vulnerable Web2py App</title>
                </head>
                <body>
                    <h1>Stack Trace</h1>
                    <h2>Exception Occurred</h2>
                    <pre>
An error occurred while processing your request. Please contact the administrator.
                    </pre>
                </body>
                </html>
                """
            return html

    def handle_sql_injection(self, query):
        """Simulate SQL injection vulnerability with error exposure."""
        user_input = query.get('id', ['1'])[0]
        
        try:
            conn = sqlite3.connect('storage.sqlite')
            cursor = conn.cursor()
            
            # Vulnerable SQL query (intentionally unsafe)
            sql_query = f"SELECT * FROM users WHERE id = {user_input}"
            cursor.execute(sql_query)
            result = cursor.fetchall()
            
            conn.close()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SQL Injection Test - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>SQL Injection Test</h1>
                <p>User input: {user_input}</p>
                <p>SQL Query: {sql_query}</p>
                <p>Result: {result}</p>
                
                <h2>Test SQL Injection</h2>
                <ul>
                    <li><a href="/sql_injection?id=1">Normal Query</a></li>
                    <li><a href="/sql_injection?id=1'">SQL Error</a></li>
                    <li><a href="/sql_injection?id=1 OR 1=1">Always True</a></li>
                    <li><a href="/sql_injection?id=1; DROP TABLE users;">Drop Table</a></li>
                </ul>
            </body>
            </html>
            """
            return html
            
        except Exception as e:
            import traceback
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SQL Error - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>SQL Error (Intentionally Exposed)</h1>
                
                <h2>Error Details</h2>
                <pre>
User Input: {user_input}
SQL Query: {sql_query}
Exception: {str(e)}
Exception Type: {type(e).__name__}

Full Traceback:
{traceback.format_exc()}

Database Information:
- Database Path: applications/welcome/databases/storage.sqlite
- Connection String: sqlite://storage.sqlite
- Tables: users, sessions
                </pre>
            </body>
            </html>
            """
            return html

    def handle_file_access(self, query):
        """Simulate file access vulnerability with path traversal."""
        file_path = query.get('file', ['/etc/passwd'])[0]
        
        try:
            # Vulnerable file access (intentionally unsafe)
            with open(file_path, 'r') as f:
                content = f.read()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>File Access - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>File Access Test</h1>
                <p>Requested file: {file_path}</p>
                
                <h2>File Content</h2>
                <pre>{content}</pre>
                
                <h2>Test File Access</h2>
                <ul>
                    <li><a href="/file_access?file=/etc/passwd">/etc/passwd</a></li>
                    <li><a href="/file_access?file=/etc/hosts">/etc/hosts</a></li>
                    <li><a href="/file_access?file=../../../etc/shadow">Path Traversal</a></li>
                    <li><a href="/file_access?file=storage.sqlite">Database File</a></li>
                </ul>
            </body>
            </html>
            """
            return html
            
        except Exception as e:
            import traceback
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>File Access Error - Vulnerable Web2py App</title>
            </head>
            <body>
                <h1>File Access Error (Intentionally Exposed)</h1>
                
                <h2>Error Details</h2>
                <pre>
Requested File: {file_path}
Exception: {str(e)}
Exception Type: {type(e).__name__}

Full Traceback:
{traceback.format_exc()}

System Information:
- Current Directory: {os.getcwd()}
- File Permissions: {oct(os.stat('.').st_mode)[-3:]}
- User ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}
- Process ID: {os.getpid()}
                </pre>
            </body>
            </html>
            """
            return html

def run_server():
    """Run the vulnerable Web2py application."""
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, VulnerableHTTPHandler)
    print("Vulnerable Web2py application running on http://0.0.0.0:8080")
    print("Admin interface: http://0.0.0.0:8080/admin/")
    print("Admin credentials: admin@example.com / admin123")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 