# -*- coding: utf-8 -*-
'''
    Setting module for Vimana Framework
    ===================================
    
    This modules shares some django configurations to be used
    by modules 

'''


from . __colors import *
from prettytable import PrettyTable
import random


class api_auth:
    def __init__(self):
        endpoints = [
            'signup',
            'logedin',
            'api-auth',
            'api-token-auth',
            'api-token-verify',
            'api-token-refresh'
        ]

        self.endpoints  = endpoints

class common:
    def __init__(self):
        '''common settings'''
        
        # common ports when application is running in homolog environment
        # feel free to change it and add or remove entries
        self.homolog_ports = [
            '9001','8081','5001','8000','8080',
            '8009','8888', '9002', '8889','9000',
            '7000', '9003', '9001'
        ]

class csrf_table:
    def __init__(self):

        index    = Wn_c + "#"        + D_c
        pattern  = Wn_c + "pattern"  + D_c
        status   = Wn_c + "status"   + D_c
        csrffvc  = Wn_c + "CFVS"   + D_c
        aslash   = Wn_c + 'APPEND_SLASH' + D_c
        config   = Wn_c + 'config_fail' + D_c
        exception= Wn_c + 'exception'+ D_c
        infoleak = Wn_c + 'issue'+ D_c

        CSRF_FVT = PrettyTable()
        CSRF_FVT.field_names = [
            index,
            pattern,
            status,
            config,
            exception,
            infoleak
        ]
        CSRF_FVT.align = "l"

        self.FORBIDDEN = 403
        self.INTERNAL_SERVER_ERROR = 500
        self.CSRFFV = 'CSRF_FAILURE_VIEW'
        self.CSRF_FAILURE_VIEW = False
        self.APPEND_SLASH = False
        self.DEBUG_STATUS = False
        self.EXCEPTION_CACHE_EMPTY = True
        self.EXCEPTION = False
        self.STATUS = {}
        self.CSRFTOKEN = False
        self.URL = False
        self.USERNAME = 'DJANGO'
        self.PASSWORD = 'UNHANDLED'
        self.CSRF_FVT = CSRF_FVT

        self.expected_status = [
            'Verificação CSRF falhou',
            'CSRF verification failed'
        ]


class set_header:
    
    def __init__(
        self, 
        URL, 
        login_data, 
        csrf_token
        ):

        request_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(login_data)),
            'Connection': 'close',
            'Referer': '{}'.format(URL),
            'Cookie': 'csrftoken= {}'.format(csrf_token),
            'Upgrade-Insecure-Requests': '1'
        }

        self.request_headers = request_headers

class django_envvars:
    
    def __init__(self):
        '''
            This method loads Django environment variable names to djxtri 
            This variables are used in fuzzing steps to recognize specific 
            kind of information leaked by some exception.

            These are defaut values used by Vimana, feel free to add 
            new items in the format bellow. You need to specify a list object
            with variables in the choosen context or just add new item in 
            categories bellow.

            When DMT plugin stops you can specify a given context to show
            especific informations, e.g: 
                        
                        dmt> show contexts
                        dmt> inspect LC1 (leaked context 1)

        '''

        # this could be used in vimana by siddhis that looks for django issues
        self.SECURITY_MIDDLEWARE = {
            'SECURE_BROWSER_XSS_FILTER': '''
                \r sets the X-XSS-Protection: 1; mode=block header on all responses that do not already have it.

                \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-browser-xss-filter
            ''',
            'SECURE_CONTENT_TYPE_NOSNIFF': '''
                \r sets the X-Content-Type-Options: nosniff header on all responses that do not already have it.

                \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-content-type-nosniff
            ''',
            'SECURE_HSTS_INCLUDE_SUBDOMAINS': '''
                \r adds the includeSubDomains directive to the HTTP Strict Transport Security header.
                \r It has no effect unless SECURE_HSTS_SECONDS is set to a non-zero value.

                \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-hsts-include-subdomains
            ''',
            'SECURE_HSTS_PRELOAD': '''
                \r adds the preload directive to the HTTP Strict Transport Security header. 
                \r It has no effect unless SECURE_HSTS_SECONDS is set to a non-zero value.

                \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-hsts-preload
            ''',
            'SECURE_HSTS_SECONDS': '''
                \r sets the HTTP Strict Transport Security header on all responses that do not already have it.
                \r SecurityMiddleware will set HTTP Strict Transport Security header automatically if SECURE_HSTS_SECONDS is not False

                \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-hsts-seconds
            ''',
            '\r SECURE_REDIRECT_EXEMPT': '''
                \r If a URL path matches a regular expression in this list, the request will not be redirected to HTTPS. (require  SECURE_SSL_REDIRECT=True)
                
                \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-redirect-exempt
            ''',
            'SECURE_REFERRER_POLICY': '''
                \r sets the Referrer Policy header on all responses that do not already have it to the value provided.

                \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-referrer-policy
            ''',
            'SECURE_SSL_HOST': '''
                 \r all SSL redirects will be directed to this host rather than the originally-requested host (require  SECURE_SSL_REDIRECT=True)

                 \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-ssl-host
            ''',
            'SECURE_SSL_REDIRECT': '''
                 \r redirects all non-HTTPS requests to HTTPS (except for those URLs matching a regular expression listed in SECURE_REDIRECT_EXEMPT).

                 \r https://docs.djangoproject.com/en/3.1/ref/settings/#secure-ssl-redirect
            '''
                
        }

        SERVER_ = [
            'SERVER_NAME', 
            'HOSTNAME',
            'SERVER_PROTOCOL', 
            'SERVER_SOFTWARE', 
            'SERVER_ADMIN', 
            'wsgi.version', 
            'REMOTE_ADDR', 
            'REMOTE_PORT', 
            'LANGUAGE_CODE', 
            'BASE_DIR', 
            'ALLOWED_HOSTS', 
            'INTERNAL_IPS',
            'STATIC_ROOT',
            'Server time', 
            'USER'
        ]
        ENVIRONMENT_ = [
            'HOME', 
            'DJANGO_SETTINGS_MODULE', 
            'DJANGO_VERSION', 
            'Django Version', 
            'Python Executable', 
            'Python Version', 
            "Server time", 
            'DEFAULT_EXCEPTION_REPORTER_FILTER', 
            'PYTHON_PIP_VERSION', 
            'CONTEXT_DOCUMENT_ROOT', 
            'MAIL',
            'PYTHON_VERSION', 
            'S3_BUCKET_NAME', 
            'SENTRY_DSN', 
            'UWSGI_CHDIR'
        ]
        EMAIL_ = [
            'MAIL',
            'EMAIL_BACKEND',	
            'EMAIL_HOST',	
            'EMAIL_HOST_PASSWORD',	
            'EMAIL_HOST_USER',	
            'EMAIL_PORT',	
            'EMAIL_SSL_CERTFILE',	
            'EMAIL_SSL_KEYFILE',	
            'EMAIL_SUBJECT_PREFIX',	
            'EMAIL_TIMEOUT',	
            'EMAIL_USE_SSL',	
            'EMAIL_USE_TLS' 
        ]	
        FILE_UPLOAD_ = [
            'FILE_CHARSET',	
            'FILE_UPLOAD_DIRECTORY_PERMISSIONS',	
            'FILE_UPLOAD_HANDLERS',	
            'FILE_UPLOAD_MAX_MEMORY_SIZE',	
            'FILE_UPLOAD_PERMISSIONS',	
            'FILE_UPLOAD_TEMP_DIR'	
        ]
        EXCEPTIONS_ = [
            'Exception Type', 
            'Exception Value', 
            'Exception Location'
        ]
        SESSION_ = [
            'SESSION_ENGINE',
            'SESSION_CACHE_ALIAS',	
            'SESSION_COOKIE_AGE',	
            'SESSION_COOKIE_DOMAIN',	
            'SESSION_COOKIE_HTTPONLY',	
            'SESSION_COOKIE_NAME',	
            'SESSION_COOKIE_PATH',	
            'SESSION_COOKIE_SECURE',	
            'SESSION_ENGINE',	
            'SESSION_EXPIRE_AT_BROWSER_CLOSE',	
            'SESSION_FILE_PATH',	
            'SESSION_SAVE_EVERY_REQUEST',	
            'SESSION_SERIALIZER',	
            'HTTP_COOKIE'
        ]
        COMMUNICATION_ = [	
            'SECURE_BROWSER_XSS_FILTER',	
            'SECURE_CONTENT_TYPE_NOSNIFF',	
            'SECURE_HSTS_INCLUDE_SUBDOMAINS',	
            'SECURE_HSTS_SECONDS',	
            'SECURE_PROXY_SSL_HEADER',	
            'SECURE_REDIRECT_EXEMPT',	
            'SECURE_SSL_HOST',	
            'SECURE_SSL_REDIRECT'
        ]
        CSRF_ = [
            'CSRF_COOKIE_AGE', 	
            'CSRF_COOKIE_DOMAIN', 	
	    'CSRF_COOKIE_HTTPONLY', 	
	    'CSRF_COOKIE_NAME', 	
	    'CSRF_COOKIE_PATH', 	
	    'CSRF_COOKIE_SECURE', 	
	    'CSRF_FAILURE_VIEW', 	
	    'CSRF_HEADER_NAME', 	
	    'CSRF_TRUSTED_ORIGINS', 	
	    'CSRF_USE_SESSIONS' 	
        ]
        AUTHENTICATION_ = [
            'AUTHENTICATION_BACKEND', 
            'AUTHENTICATION_BACKENDS',
            'AUTH_USER_MODEL', 
            'AUTHENTICATION_BACKENDS'
        ]
        CREDENTIALS_ = [
            'USER', 
            'SECRET_KEY', 
            'CLIENT_KEY', 
            'CLIENT_SECRET', 
            'ACCESS_KEY', 
            'PASSWORD_HASHERS', 
	    'ADMINS', 
            'USER', 
            'PASSWORD', 
            'DB_USER', 
            'DB_PASSWORD', 
            'USER_PASSWORD', 
	    'API_PASSWORD', 
            'API_KEY', 
            'CLIENT_ACCESS_KEY',
            'ROOT_PASSWORD', 
            'PASSWD', 
	    'SENHA', 
            'SENHA_BANCO', 
            'SENHA_AWS', 
            'AWS_SECRET', 
            'AWS_CLIENT', 
            'CONSOLE_KEY_ID', 
	    'CONSOLE_SECRET_KEY', 
            'AUTH_PASSWORD_VALIDATORS', 
            'JWT_AUTH'
        ]
        SERVICES_ = [
            'SSH_CLIENT', 
            'SSH_CONNECTION', 
            'SSH_CONNECTIONS', 
            'SSH_TTY', 
            'SSH_PASSWORD'
        ]


        self.SERVER_        = SERVER_
        self.ENVIRONMENT_   = ENVIRONMENT_
        self.EMAIL_         = EMAIL_
        self.FILE_UPLOAD_   = FILE_UPLOAD_
        self.EXCEPTIONS_    = EXCEPTIONS_
        self.SESSION_       = SESSION_
        self.COMMUNICATION_ = COMMUNICATION_
        self.CSRF_          = CSRF_
        self.AUTHENTICATION_= AUTHENTICATION_
        self.CREDENTIALS_   = AUTHENTICATION_
        self.SERVICES_      = AUTHENTICATION_


class payloads():

    def __init__(self):

        # simple unicode characteres (fell free to change for you needs)
        self.unicode_payloads = [
            'ĸĸ', 'ĦĦ', 'ø',
            '»','þ','©ð€', 
            'łæ','ÆÆ',
            '®', 'µŁÞ', '¬',
            '¢¢', '£', 'ŧŧ',
            '¹','²','³','←',
            '↓→←'
        ]

    def get_random_unicode_payload(self):
        u_payload = '/' + \
            random.choice(self.unicode_payloads) + \
            random.choice(self.unicode_payloads) + \
            random.choice(self.unicode_payloads) * \
            random.choice(range(5))              + \
            random.choice(self.unicode_payloads)
    
        return u_payload
