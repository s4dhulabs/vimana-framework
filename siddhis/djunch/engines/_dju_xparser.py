# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                - DJUNCH v2 -


    Django application fuzzer module for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch
    
"""


import sys
sys.path.insert(0, '../')

from random import random, choice, randint
from scrapy.exceptions import CloseSpider
from urllib.parse import urlparse
from datetime import datetime
from res import vmnf_banners
from mimesis import Internet
from mimesis import Generic
import urllib3.exceptions
import copy
import scrapy
import twisted
import hashlib
import random
import os

from . _dju_report import resultParser
from . _dju_utils import DJUtils

import inspect
import secrets
from itertools import chain

from scrapy import signals
from scrapy.shell import inspect_response
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from scrapy.utils.log import configure_logging  
from scrapy.http import HtmlResponse
from scrapy.http.headers import Headers
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from neotermcolor import colored,cprint
from pygments import highlight
import django.core.exceptions as django_cx

from time import sleep
from urllib.parse import urljoin

from settings.siddhis_shared_settings import django_envvars as djev
from settings.siddhis_shared_settings import csrf_table as _csrf_
from . exceptions._items import ExceptionItem
from . exceptions._items import ExceptionPool
from . exceptions._items import FuzzURLsPool 
from . exceptions._items import ConfigIssuesItem
from . exceptions._items import IssuesPool

from siddhis.djunch.engines._dju_utils import DJUtils
from res.vmnf_fuzz_data import VMNFPayloads 
from res.colors import *



class DJEngineParser(scrapy.Spider):
    name = 'DJEngineParser'

    def __init__(self, *args, **vmnf_handler):
        super(DJEngineParser, self).__init__(*args,**vmnf_handler)
       
        self._vmnfp_ = VMNFPayloads(**vmnf_handler)
        self.cookies = {}
        self.djx_def = {}
        self.x_trigger_status = [400, 500]
        self.follow_responses = [200, 302]
        self.vmnf_handler = vmnf_handler
        self.target = vmnf_handler.get('target_url')
        self.debug_is_on = vmnf_handler['debug']
        self.step_method = vmnf_handler.get('method')
        self.headers =  vmnf_handler.get('headers')
        self.data = self._vmnfp_.get_random_credential()
        self.cookies = vmnf_handler.get('cookie')
        self.download_timeout = vmnf_handler.get('download_timeout')
        self.meta = vmnf_handler.get('meta')
        self.patterns = vmnf_handler.get('patterns')
        self.fuzz_step = vmnf_handler.get('fuzz_step')
        self.caught_exceptions = []
        self.collected_sample = False
        
        _ISSUES_ = IssuesPool()
        _ISSUES_['ISSUES'] = {
            'EXCEPTIONS': [],
            'CONFIGURATION': [],
            'FUZZ_STATUS_LOG': [],
            'GENERAL_OBJECTS': [],
            'FUZZ_SCOPE': False
        }
        self._ISSUES_POOL = _ISSUES_['ISSUES']
        self._XP_ = ExceptionPool()
        self._XP_['ENTRIES'] = []
        self._EXCEPTION_POOL_ = self._XP_['ENTRIES']
        
        self.general_request_status = []
        self.fuzz_start = True
        self.GenObj = Generic()
        self.General_Traceback_Objects = []

    def closed(self,reason):
        self._ISSUES_POOL['GENERAL_OBJECTS'] = self.General_Traceback_Objects

        if not self._ISSUES_POOL['EXCEPTIONS']:
            cprint("\n[{}]→ No exception found with given settings.\n".format(datetime.now()), 'cyan')
            if self.debug_is_on:
                for request_status in self._ISSUES_POOL['FUZZ_STATUS_LOG']:
                    print(request_status)

            os._exit(os.EX_OK) 
            #return False
        
        # create instance of dju_reporter to issues presentation
        result = resultParser(self._ISSUES_POOL, **self.vmnf_handler).show_issues()
        os._exit(os.EX_OK) 

    def start_requests(self):

        # This will be used in future versions to configure the fuzzer options: full, fast, etc.
        scope = DJUtils(False,False)
        self._FuzzURLsPool_ = scope.get_scope(self.target, self._vmnfp_, **self.vmnf_handler)
        self.fuzz_scope_size = len(self._FuzzURLsPool_['FULL_SCOPE'])
        self.fuzz_rounds = len(self._FuzzURLsPool_) 
        step_mark = colored('↪', 'white', attrs=['bold'])
        ramdata = scope.get_random_data_list()
       
        ssti_p = self._vmnfp_.get_ssti_payloads()
        xss_p = self._vmnfp_.get_xss_payloads()
        
        if not self.target or self.target is None:
            print('[{}:{}]→ Missing target'.format(self.vmnf_handler['module_run'], datetime.now()))
            return False
        
        if not self.vmnf_handler.get('sample'):
            print(' {} Starting DJunch against {} | {} rounds / {} URL variations'.format(
                colored("✔", 'green'),
                (G_c  + self.target + W_c),
                self.fuzz_rounds,
                self.fuzz_scope_size
                )
            )
            sleep(1)

        f_count = 1
        for url_step_type, fuzz_urls in self._FuzzURLsPool_.items():
            _fzz_headers_ = copy.copy(self.headers)
            filter_mode = False
            self.fuzz_step = url_step_type.lower()
            hl_url_step_type = colored(self.fuzz_step, 'cyan')
            step_urls = len(fuzz_urls)
            t_count = 1
            hl_color = 'white'
            f_hl_fuzz = hl_color
            set_max = 5

            if self.vmnf_handler.get('sample'):
                self.meta["max_retry_times"] = 1
                set_max = 1
           
            for target_url in fuzz_urls:
                
                # to avoid make request to outofscope targets parsed in test response
                if not self.target in target_url:
                    continue
                 
                _fzz_headers_['Host'] = '127.0.0.1'
                _fzz_headers_['Content-Length'] = 123
                self.step_method = 'GET'

                if self.fuzz_step == 'raw_urls':
                    self.step_method = 'POST'
                    if target_url.endswith('/'):
                        target_url = target_url[:-1]
                
                # all urls in current scope - last step
                if f_count == self.fuzz_rounds:
                    # this could be used as redundance in future releases / loopdangerous 
                    #filter_mode = True
                    
                    # randomize UA (this could be change in following step or not/random v to random h
                    _fzz_headers_['User-Agent'] = self.GenObj.internet.user_agent()
                    
                    # random payloads
                    payloads = ssti_p if (f_count % 2) == 0 else xss_p

                    # random set to a random header
                    _fzz_headers_[choice([k for k in self.headers.keys()])] = choice(payloads)

                    # random setup unreal header and change content-type for whatever
                    if self.fuzz_rounds - f_count < 10:
                        _fzz_headers_[self.GenObj.person.name()]= choice(range(1000))  
                        _fzz_headers_['Content-Type'] = self.GenObj.internet.content_type()

                    # random method 2 / other methods to be implemented to enrich fuzzer
                    self.step_method = choice(['GET','POST','PUT','PATCH'])
                    
                    # because in this mode we expect to be faster, set as 1 before
                    if not self.vmnf_handler.get('sample'):
                        self.meta["max_retry_times"] = choice(range(1,set_max))
                        self.meta["download_timeout"] = choice(range(1,set_max))

                    f_hl_fuzz = 'green'
                    
                if t_count == step_urls:
                    hl_color = 'green'
                    step_mark = colored('✔', hl_color)
                
                if not self.vmnf_handler.get('sample'):
                    align = ' ' if self.step_method == 'GET' else ''
                    hl_t_count = colored(str(t_count), hl_color)
                    hl_step_urls= colored(str(step_urls), hl_color)
                    hl_f_count = colored(str(f_count), hl_color)
                    hl_fuzz_rounds = colored(str(self.fuzz_rounds), f_hl_fuzz)
                    hl_fuzz_steps = '{}/{}'.format(hl_f_count,hl_fuzz_rounds)
                    urls_step_count = '{}/{}'.format(hl_t_count,hl_step_urls)
                    hl_method = colored(self.step_method + align, 'blue')

                    fuzz_step_msg = (' {} Fuzzer step ({}) | {} {} ({})'.format(
                        step_mark,
                        hl_fuzz_steps,
                        hl_method,
                        hl_url_step_type,
                        urls_step_count,
                        )
                    )
                
                    if self.debug_is_on:
                        print(fuzz_step_msg)
                    else:
                        print()
                        print(fuzz_step_msg.ljust(os.get_terminal_size().columns - 1), end="\r")
                
                if self.step_method == 'GET':
                    yield scrapy.Request(
                        target_url, 
                        callback=self.status_handler,
                        headers=_fzz_headers_,
                        meta=self.meta,
                        errback=self.failure_handler,
                        dont_filter = filter_mode
                    )
                elif self.step_method == 'POST':
                    yield scrapy.FormRequest(
                        target_url, 
                        callback=self.status_handler,
                        method=self.step_method, 
                        formdata=self.data,
                        cookies=self.cookies,
                        headers=_fzz_headers_,
                        meta=self.meta,
                        errback=self.failure_handler,
                        dont_filter = filter_mode
                    )

                sleep(0.01)
                t_count +=1
            
            f_count +=1
            sleep(1)
            print()
        
        if not self.vmnf_handler.get('sample'):
            cprint('\n → Waiting for threads [fell free to cut this short with a CTRL+C]...', 'cyan') 
        sleep(1)
        raise CloseSpider('-- [fuzz:done] --')



    def failure_handler(self, failure):
        self._ISSUES_POOL['FUZZ_STATUS_LOG'].append(
            {
                'method': self.step_method,
                'request': str(failure.request),
                'status': failure.value,
                'step': self.fuzz_step
            }
        )

        if self.debug_is_on:
            method_name = (inspect.currentframe().f_code.co_name)
            try: 
                failure_type = failure.type() 
            except TypeError: 
                failure_type = failure.type

            print("""\n     [DJUParser().{}(): {}]
                \r\t+ Fuzz step: {}
                \r\t+ Step method: {}
                \r\t+ Failure type: {}""".format(
                method_name,
                datetime.now(),
                colored(self.fuzz_step.lower(), 'cyan'),
                colored(self.step_method, 'cyan'),
                colored(failure_type, 'magenta')
                )
            )
            print()
        pass

    def status_handler(self, response):
        caught_ignore_keys = ['Python Path', 'Exception Value', 'Request URL']
        response_data = str(response.body.decode("utf-8"))
    
        self._ISSUES_POOL['FUZZ_STATUS_LOG'].append(
            {
                'method': self.step_method,
                'url': response.url,    
                'status': response.status,
                'step': self.fuzz_step
            }
        )
        
        if response.status in self.follow_responses:
            try:
                yield scrapy.FormRequest.from_response(
                    response,
                    formdata=self._vmnfp_.get_random_credential(),
                    callback=self.status_handler,
                    errback=self.failure_handler,
                    method='POST'
                )
                pass
            except ValueError:
                pass

        if response.status == 403:
            for p in _csrf_().expected_status:
                if response_data.find(p) != -1:
                    debug_step = "CSRF_FAILURE_VIEW warning"
                    
                    if not self.vmnf_handler.get('sample'):
                        flag_status = colored(" djunch().parser({}) ".format(response.status),'red', 'on_cyan')
                        status_msg=colored('Triggered a Django forbidden warning:','cyan')
                        cprint("\n{} {} {} \n  → '{}'".format(flag_status,status_msg,p,debug_step))
                    
                    self._ISSUE_ = ConfigIssuesItem()
                    self._ISSUE_['ISSUE_TYPE'] = 'CONFIGURATION'
                    self._ISSUE_['IID'] = 'CI{}'.format(len(self._ISSUES_POOL['CONFIGURATION']) + 1)
                    self._ISSUE_['URL'] = response.url
                    self._ISSUE_['METHOD'] = self.step_method
                    self._ISSUE_['COOKIE'] = self.cookie
                    self._ISSUE_['RESPONSE'] = response.headers
                    self._ISSUE_['ISSUE'] = debug_step
                    self._ISSUE_['STATUS'] = response.status
                    
                    self._ISSUES_POOL['CONFIGURATION'].append(self._ISSUE_)
                
                    if self.debug_is_on:
                        print()
                        print('     + URL: {}'.format(response.url))
                        print('     + Method: {}'.format(self.step_method))
                        print('     + Cookie: {}'.format(self.cookie))

                        for k,v in (response.headers.items()):
                            print('     + {}: {}'.format(k.decode(),v[0].decode()))
                        print()
                    
                    return False

        elif response.status in self.x_trigger_status:
            self.EXCEPTION_PATTERN = (response.xpath('//div[@id="summary"]//tr')) 
            self.EXCEPTION_MATCH = self.EXCEPTION_PATTERN.xpath('.//td/text()').getall()[2:-1]

            if self.EXCEPTION_MATCH:
                self.EXCEPTION_ID = hashlib.sha256(str(self.EXCEPTION_MATCH).encode('utf-8')).hexdigest()[:10]
            
            if len(self.EXCEPTION_PATTERN) == 0:
                status_msg=colored("The application's response does not match with an expected exception. Maybe a server issue:", 'yellow')
                print("[djunch().status_handler({})] {} \n{}".format(
                    response.status,
                    status_msg,
                    response_data
                    )
                )
                return False

            if self.EXCEPTION_ID in self.caught_exceptions:
                method_name = (inspect.currentframe().f_code.co_name)
                
                print("""\n     [DJUParser().{}({}): {}] 
                    \r\t+ Exception already caught: {}""".format(
                    method_name,
                    colored(response.status, 'magenta'),
                    datetime.now(),
                    colored(self.EXCEPTION_ID, 'blue')
                    )
                )
                #print()
                if self.debug_is_on:
                    for EXCEPTION in self._ISSUES_POOL['EXCEPTIONS']:
                        if EXCEPTION['EXCEPTION_ID'] == self.EXCEPTION_ID:
                            EXCEPTION['EXCEPTION_COUNT'] = EXCEPTION['EXCEPTION_COUNT'] + 1
                            x_loc = EXCEPTION['EXCEPTION_SUMMARY'].get('Exception Location').split()
                            
                            print('\r\t+ XCount: {}'.format(
                                colored(EXCEPTION['EXCEPTION_COUNT'], 'magenta')
                                )
                            )
                            print("""\r\t+ Exception Type: {}
                                     \r\t+ Module: {}
                                     \r\t+ Function: {}
                                     \r\t+ Line: {}
                                    """.format(
                                        colored(EXCEPTION['EXCEPTION_TYPE'], 'blue'),
                                        colored(x_loc[0], 'magenta'),
                                        colored(x_loc[2], 'magenta'),
                                        colored(x_loc[4], 'magenta')
                                    )
                            )
                            #print()
                            sleep(0.15)
                return False
            
            if self.vmnf_handler.get('sample') \
                and self.collected_sample:                
                raise CloseSpider('-- sample mode enabled')
                sleep(0.10)

            # normal exception parser sample or regular fuzzer mode
            self.djx_parser(response)
        
    def djx_parser(self, response):
        ''' Parse and register a new exception '''

        self.caught_exceptions.append(self.EXCEPTION_ID)
        REQUEST_HEADERS = response.request.headers
        TRACEBACK_OBJECTS = []
       
        [self.djx_def.__setitem__(x, getattr(django_cx, x).__doc__) \
            for x in [attr for attr in dir(django_cx) \
                if not attr.startswith('__')
            ]
        ]
        
        mark = colored(' ⠶ ', 'green', attrs=['bold'])
        stage = colored('→', 'green')
        
        RAW_X_SUMMARY       = self.EXCEPTION_PATTERN
        EXCEPTION_TRACEBACK = response.xpath('//div[@id="traceback"]//li[@class="frame django"]')
        REQS_TABLES         = response.xpath('//*[@class="req"]//tbody')
        TABLES_ROWS         = REQS_TABLES.xpath('.//tr')
        EXCEPTION_VAR_CACHE = [ROW.xpath('td//text()').get() for ROW in TABLES_ROWS]
        PASTEBIN_TRACEBACK  = response.xpath(
            '//div[@id="pastebinTraceback"]//textarea[@name="content"]//text()').get()
        
        ENVIRONMENT = {}
        KEY_ENV_CONTEXTS = {}
        for ROW in TABLES_ROWS:
            key, value = (ROW.xpath('td//text()').getall())
            ENVIRONMENT[key] = value
            k_ref = key.upper()
            
            # consider this case wsgi.file_wrapper - split by '.' not only _ !ctp: handler this cases
            if '_' in k_ref:
                k_ref = k_ref.split('_')[0]
            elif '.' in k_ref \
                and not '_' in k_ref:
                k_ref = k_ref.split('.')[0]

            if KEY_ENV_CONTEXTS.get(k_ref) is None:
                KEY_ENV_CONTEXTS[k_ref] = list()
            KEY_ENV_CONTEXTS[k_ref].append(key + ':' + value)

        INSTALLED_ITEMS = DJUtils(PASTEBIN_TRACEBACK,False).parse_raw_tb()
        DB_SETTINGS = DJUtils(False,KEY_ENV_CONTEXTS).parse_db_settings()
        CONTEXTS = DJUtils(False, False).parse_contexts(**ENVIRONMENT)
        
        if not self.vmnf_handler.get('sample'):
            cprint('\n\n {} {} Django applications identified on host {} with {}'.format(
                stage,colored(len(INSTALLED_ITEMS['Installed Applications']),'green'),
                colored(CONTEXTS['server'].get('SERVER_NAME'), 'green'),
                colored(CONTEXTS['server'].get('SERVER_SOFTWARE'), 'green')
                )
            )
            print()
            sleep(0.30)
        else:
            print("\033c", end="")
            vmnf_banners.sample_mode(colored(' sample caught  ','white', 'on_red', attrs=['bold']))
            sleep(1)
        
        EXCEPTION_SUMMARY = {}
        for s in RAW_X_SUMMARY:
            hl_color = 'green'
            values = []
            key = (s.xpath('.//th/text()').get()).strip(':')
            value = (s.xpath('.//td/text()').get())
            value_base = (s.xpath('.//td//span').get())
            span_flag = True if value_base\
                    and value_base is not None else False
            
            if span_flag:
                v = (s.xpath('.//td').get())
                v = v[v.find('class="fname">')+14:]
                value = v.replace('</span>','').replace('</td>','').strip()

            if not value or value is None:
                value = (s.xpath('.//td//pre/text()').get())

                if len(value.split('\n')) > 1:
                    for v in value.split('\n'):
                        values.append(
                            v.replace('[','').replace(']','').replace("'",'').replace(',','').strip()
                        )
                    value = values
                
            EXCEPTION_SUMMARY[key]=value
            if key == 'Exception Type':
                hl_color = 'magenta'

            # print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,colored(value, hl_color)))
       
        # link exception type with related environment variable (if exists)
        EXCEPTION_TYPE = EXCEPTION_SUMMARY['Exception Type']
        EXCEPTION_REASON = False
        EXCEPTION_ENV_VAR = False
        EXCEPTION_ENV_VALUE = False

        if EXCEPTION_TYPE in djev().EXCEPTION_RELVARS.keys():
            EXCEPTION_ENV_VAR = djev().EXCEPTION_RELVARS.get(EXCEPTION_TYPE) 
            EXCEPTION_ENV_VALUE = ENVIRONMENT.get(EXCEPTION_ENV_VAR)
        
        try:
            exception_type = EXCEPTION_SUMMARY['Exception Type'].strip()
        except KeyError:  
            return False

        if not self.vmnf_handler.get('sample'):
            print('{}{}:\t   {}'.format(
                (' ' * int(5-len('Variables') + 14)),
                'Variables',colored(len(EXCEPTION_VAR_CACHE), 'green')
                )
            )
        
            if self.djx_def.get(exception_type) is not None:
                EXCEPTION_REASON = (self.djx_def.get(exception_type))
                print('{}{}:\t   {}'.format(
                    (' ' * int(5-len('Exception reason') + 14)),
                    'Exception reason',colored(EXCEPTION_REASON, 'green')
                    )
                )
        
            sleep(1)

        trace_count = 0
        EXCEPTION_PARSED_TRACEBACK = []
        MODULE_TRIGGER_INFO = {}
        
        for entry in EXCEPTION_TRACEBACK:
            highlight_code_snippets = []
            raw_code_snippets = []
            object_mapping = {}
            trace_count +=1

            try:
                ''' Django Version: 1.*.* (p:1.4.5)
                    Python Version: 2.*.* (p:2.6.6)
                    [module_path, function()]
                '''
                module, function = (entry.xpath('.//code/text()').getall())
            except ValueError:
                ''' Django Version: 3.*.* (p:3.1.12)
                    Python Version: 3.*.* (p:3.6.9)
                    [module_path]
                '''
                module = entry.xpath('.//code/text()').getall()[0].strip().replace(',','')      
                function = entry.xpath('.//text()').getall()[2].strip().replace(',','').replace('in ','').split()[-1]

            code_snippet = [l for l in entry.xpath('.//div[@class="context"]//ol//li//pre').getall()]
            context_line_number = int(entry.xpath('.//div//ol[@class="context-line"][1]').get()[11:20].split()[0].strip('"'))
            context_line = entry.xpath('.//div//ol[@class="context-line"]//li//pre/text()').get()
            ref_line_number = int(entry.xpath('.//div//ol').get().split('\n')[0].split()[1].split('=')[1].strip('"'))
            trigger_point = str(context_line_number)  + '   ' + context_line.strip()
            args_keys = entry.xpath('.//table[@class="vars"]/tbody/tr/td/text()').getall()
            args_values = entry.xpath('.//table[@class="vars"]//tbody//tr//td[@class="code"]//pre/text()').getall()
            module_args = dict(zip(args_keys,args_values))
            
            trigger = {"Module": module, "Function":function,"Line trigger":trigger_point}

            cs_count = 0
            for l in code_snippet:
                cs_count +=1
                if l.strip() == '<pre></pre>':
                    l=' '
                line = highlight(l, PythonLexer(),TerminalFormatter())
                line = line.strip().replace('<pre>','').replace('</pre>','').replace('\n','')
                l = l.strip().replace('<pre>','').replace('</pre>','').replace('\n','')
                
                raw_line = (' {}  {}'.format(str(ref_line_number),l))
                hl_line = ('    {}    {}'.format(
                    colored(str(ref_line_number).strip('\n'), 'green', attrs=['bold']),line
                    )
                )
                raw_code_snippets.append(raw_line)
                highlight_code_snippets.append(hl_line)
                
                ref_line_number +=1
            
            for key,value in module_args.items():
                if 'object at' in value and \
                        '<django.' in value:
                    
                    obj = value.split() 
                    object_mapping = {
                        'variable'  : key.strip(),
                        'object'    : obj[0].replace('<','').strip(),
                        'address'   : obj[3].replace('>','').strip()
                    }
                    TRACEBACK_OBJECTS.append(object_mapping)
                    self.General_Traceback_Objects.append(object_mapping)
            
            MODULE_TRIGGER_INFO = {
                'RAW_CODE_SNIPPET': raw_code_snippets,  
                'HL_CODE_SNIPPET': highlight_code_snippets,
                'MODULE_ARGS': module_args,
                'MODULE_TRIGGERS': trigger
            }
            
            EXCEPTION_PARSED_TRACEBACK.append(MODULE_TRIGGER_INFO)

        _EXCEPTION_ = ExceptionItem()
        _EXCEPTION_['IID'] = 'UX{}'.format(len(self._ISSUES_POOL['EXCEPTIONS']) + 1)
        _EXCEPTION_['ISSUE_TYPE'] = 'EXCEPTION'
        _EXCEPTION_['EXCEPTION_COUNT'] = 1 
        _EXCEPTION_['EXCEPTION_ID'] = self.EXCEPTION_ID
        _EXCEPTION_['EXCEPTION_TYPE'] = EXCEPTION_TYPE
        _EXCEPTION_['EXCEPTION_ENV_VAR'] = EXCEPTION_ENV_VAR
        _EXCEPTION_['EXCEPTION_ENV_VALUE'] = EXCEPTION_ENV_VALUE
        _EXCEPTION_['EXCEPTION_REASON'] = EXCEPTION_REASON
        _EXCEPTION_['EXCEPTION_TRACEBACK'] = EXCEPTION_PARSED_TRACEBACK
        _EXCEPTION_['ENVIRONMENT'] = ENVIRONMENT
        _EXCEPTION_['EXCEPTION_SUMMARY'] = EXCEPTION_SUMMARY
        _EXCEPTION_['KEY_ENV_CONTEXTS'] = KEY_ENV_CONTEXTS
        _EXCEPTION_['REQUEST_HEADERS'] = REQUEST_HEADERS
        _EXCEPTION_['FUZZ_URLS_SCOPE'] = self._FuzzURLsPool_ 
        _EXCEPTION_['INSTALLED_ITEMS'] = INSTALLED_ITEMS
        _EXCEPTION_['DB_SETTINGS'] = DB_SETTINGS
        _EXCEPTION_['CONTEXTS'] = CONTEXTS
        _EXCEPTION_['OBJECTS'] = TRACEBACK_OBJECTS

        self.LAST_EXCEPTION = _EXCEPTION_ 
        self._ISSUES_POOL['EXCEPTIONS'].append(_EXCEPTION_)
        self.collected_sample = self.LAST_EXCEPTION
        
        # in sample mode we're looking for just one exception 
        if self.vmnf_handler.get('sample'):
            raise CloseSpider('-- [VIMANA: Exception Caught]→ Running in sample mode')
            
        DJUtils(False,False).show_exception(**_EXCEPTION_)
        sleep(1)


