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
import sys
from os import path
sys.path.insert(0, '../')

from pprint import pprint

from random import choice
from scrapy.utils.response import open_in_browser

from pygments.formatters import TerminalFormatter
from urllib.parse import urlparse, urljoin
from pygments.lexers import Python3Lexer, PythonLexer, BrainfuckLexer
from pygments.lexers import HtmlDjangoLexer
from pygments.lexers import HtmlLexer
from pygments.lexers import PythonConsoleLexer
from pygments import lexers
from pygments import highlight
from tabulate import tabulate

from res.vmnf_fuzz_data import VMNFPayloads
from neotermcolor import colored,cprint
from urllib.parse import urlparse
from requests.exceptions import *
from urllib.parse import urljoin
from datetime import datetime
from res.colors import *
from copy import deepcopy
from time import sleep 
from random import choice
import jsonpickle
import requests
import hashlib
import scrapy
import yaml
import json
import os
import re

from core._dbops_.vmnf_dbops import VFDBOps
from siddhis.djunch.engines._dju_utils import DJUtils
from .._intro import default
from siddhis.djunch.engines._djxip import ParseXItem
from twisted.internet import reactor
from ..utils import (
    parse_rule_scope,
    is_valid_url, 
    dlexer,
    get_form_dict,
    is_django_exception
)

from siddhis.djunch.engines._djxip import ParseXItem
from core.vmnf_utils import generate_exception_id
from core.api.dashboard_utils import send_to_dashboard
from core.api.dashboard_utils import prepare_dashboard_data


class d4m8(scrapy.Spider):
    name = 'd4m8'
    
    def __init__(self, *args,**handler):
        super(d4m8, self).__init__(*args,**handler)
    
        self.started = False
        self.handler = handler
        self.start_urls = []

        self.RULE_SCAN_MODE = self.handler.get('rule_scan')
        self.saved_items = []
        self.url_pool =[]
        self.discovered_urls = []
        self.csrftokens = []
        self.url_count = 0
        self.started = False
        self._vmnfp_ = VMNFPayloads(**handler)
        self.single_target = True \
            if len(self.start_urls) == 1 \
                else False

        self.tested_urls = []
        self.exception_count = 0
        self.missing_token = []
        self.missing_token_urls = []
        self.done_urls = []
        self.EXCEPTIONS = []
        self.extended_scope = []
        self.out_of_scope_urls = []
        self.depth = 0
        self.max_depth = 2

        issue_type = 'dast/output'
        plugin_scope = f'django/{issue_type}'
        self.cache_dir = f"vimana/__cache__/{plugin_scope}"
        self.abs_cache_path = os.path.join(os.path.expanduser("~"), self.cache_dir)

        self.agressive_mode = self.handler.get('agressive_mode')
        self.extended_scope = self.handler.get('extended_scope')
        self.verbose_enabled = handler.get('verbose', False)
        self.sample_mode = handler.get('sample',False)

        self.scan_time = datetime.now()
        scan_pattern = f"{self.scan_time}{self.handler}"
        sha256 = hashlib.sha256()
        sha256.update(scan_pattern.encode())
        self.scan_hash = sha256.hexdigest()
        self.scan_id = self.scan_hash[:10]
        self.app_name = None
        
    def start_requests(self):
        self.silent_mode = False
        self.RULE_ACTIONS = False
        ################################################
        # --scan-rules mode / using rules to set fuzzer
        ################################################
        if self.RULE_SCAN_MODE:
            target_type = 'rule'
            self.RULE_COLLECTOR = []
            
            # get_all rules  
            self.RULES = parse_rule_scope()
            total_rules = len(self.RULES)
            target_type = target_type + ('s' if total_rules > 1 else '')

            print(colored(f"\n[{datetime.now()}] → Starting D4M8 in RuleScan mode with {total_rules} {target_type}...", 'cyan'))
            sleep(1)
            
            for RULE_NAME, RULE_SCOPE in self.RULES.items():
                self.RULE_NAME = RULE_NAME
                target_type = 'endpoint'
                scope_size = len(RULE_SCOPE['SCOPE'])
                target_type = target_type + ('s' if scope_size > 1 else '')
                self.RULE_SCOPE = RULE_SCOPE
                self.FUZZER_SETTINGS = RULE_SCOPE.get('FUZZER_SETTINGS', False)
                self.RULE_REQUEST = self.RULE_SCOPE.get('REQUEST',False)
                self.RULE_RESPONSE = self.RULE_SCOPE.get('RESPONSE',False)
                self.RULE_ACTIONS = self.RULE_SCOPE.get('ACTIONS',False)
                self.RULE_OUTPUT = self.RULE_SCOPE.get('OUTPUT',False)
                self.RULE_DATA_SET = self.RULE_SCOPE['DATA']
                self.RULE_REQS = self.RULE_ACTIONS
                self.silent_mode = False

                if self.FUZZER_SETTINGS:
                    self.silent_mode = self.FUZZER_SETTINGS.get('silent',False)
                
                DATA_SPECS = ' / '.join(f"{k}: {len(v)}" for k,v in self.RULE_DATA_SET.items())

                print(f"        ✔ Found Rule: {colored(RULE_NAME,99)}: {scope_size} {target_type} / {DATA_SPECS}")
                sleep(0.10)
                
                # rule.request_urls: 
                for REQUEST_URL in RULE_SCOPE['SCOPE']:
                    if is_valid_url(REQUEST_URL):
                        yield scrapy.Request(REQUEST_URL, callback=self.parse_form)
            
        ################################################
        # --target-url, --use-request options: default
        ################################################
        else:
            self.start_urls = self.handler.get('scope')
            target_type = 'URL'
            total_urls = len(self.start_urls)
            target_type = target_type + ('s' if total_urls > 1 else '')
            self.domain_filter = urlparse(self.start_urls[0]).netloc
            
            if not self.start_urls:
                self.log('[d4m8:{}] Missing scope!'.format(datetime.now()))
                print('Missing scope')
                return

            print(colored(f"\n[{datetime.now()}] → Starting D4M8 against {total_urls} inital {target_type}...\n",99))
            
            for url in self.start_urls:
                if not url.startswith(self.handler['target_url']):
                    continue

                if is_valid_url(url):
                    yield scrapy.Request(url, callback=self.parse_form)
    
    def parse_form(self, response):
        if response.url in self.done_urls:
            return 

        self.done_urls.append(response.url)
        
        if self.agressive_mode or self.extended_scope:
            if response.status == 500:
                self.parse_exception(response)

        # In agressive mode we'll let pass responses without forms 
        if not self.agressive_mode:
            if not response.xpath('//form').extract():
                return
        
        ################################################
        # using dict data --data "{'email':'someemail'}"
        ################################################
        data_set = False
        if self.handler['data_set']:
            data_set = self.handler['data_set']
            data_set = data_set.replace("'", "\"")
            data_set = json.loads(data_set)

        ################################################
        # using request from file --use-request <file>
        ################################################
        elif self.handler['request_data_set']:
            data_set = self.handler['request_data_set']
        
        ################################################
        # using data from rule - form_target_input_data
        ################################################
        elif self.RULE_SCAN_MODE:
            if self.RULE_DATA_SET:
                data_set = self.RULE_DATA_SET
            
        token_input_value = 'input[name="csrfmiddlewaretoken"]::attr(value)'
        csrftoken = response.css(token_input_value).extract_first()
        self.csrftokens.append(csrftoken)
        base_form = get_form_dict(response)
        fuzz_forms = DJUtils(False,False).set_form_fuzz(base_form, data_set)
        fields = response.xpath('//form//input').extract()

        for fuzz_type, forms in fuzz_forms.items():
            for fform in forms:

                meta = {
                    'fuzz_type': fuzz_type,
                    'form_data':fform, 
                    'form_fields':fields
                }

                if csrftoken:
                    if fuzz_type not in ['allin']:
                        fform['csrfmiddlewaretoken'] = csrftoken
                else:
                    if response.status == 200 and fields:
                        if response.url not in self.missing_token_urls:
                            self.missing_token_urls.append(response.url)

                            pattern = {
                                'status': response.status,
                                'url': response.url,
                                'form': fields,
                                'response': response
                            }
                            self.missing_token.append(pattern)
                
                yield scrapy.FormRequest(
                    url=response.url,
                    formdata=fform,
                    callback=self.parse_exception,
                    errback=self.parse_exception,
                    meta=meta
                )

                if self.agressive_mode:
                    yield scrapy.FormRequest.from_response(
                        response,
                        formdata=fform,
                        callback=self.parse_exception,
                        errback=self.parse_exception,
                        meta=meta
                    )

    def exception_match(self, response):
        if self.RULE_RESPONSE:
            target_exception_types = self.RULE_RESPONSE.get('target_exception_types', False)
        
            if target_exception_types:
                return next((xt for xt in target_exception_types if xt in response.text), None)
        
        return True

    def req_match(self, REQ, XITEM):
        if self.RULE_REQS:
            REQ_TYPE = self.RULE_REQS.get(REQ, False)

            if isinstance(REQ_TYPE, dict):
                REQ_TYPE = [RT for RT in REQ_TYPE.keys()]

            if REQ_TYPE:
                return next((RT for RT in REQ_TYPE if RT == XITEM), None)

        return None

    def handle_exception_item(self, response):
        ''' Handle exception item: Vimana Monitor API '''
        
        dashboard_data = prepare_dashboard_data(
            response=response,
            exception_info=self.exception_info,
            extracted_vars=False
        )
        if not self.app_name:
            environment = self.exception_parser.dump_environment()
            
            if 'ROOT_URLCONF' in environment:
                self.app_name = environment['ROOT_URLCONF'].split('.')[0].strip().replace("'", "").replace(",", "")

                if self.app_name:
                    send_to_dashboard(app_env={self.app_name: environment})

        dashboard_data['exception_meta']['view_trigger']['app_name'] = self.app_name
        dashboard_data['exception_meta']['plugin'] = 'd4m8'

        send_to_dashboard(data=dashboard_data)

    def parse_exception(self, response):
        if response.status == 500 and is_django_exception(response):
            if self.RULE_SCAN_MODE and not self.exception_match(response):
                return

            module_args = {}
            extracted_vars = {}
            #cprint(f"Fuzzing / {response.meta['fuzz_type']}: {response}", 'red')
            #print()
            
            if not self.silent_mode:
                print()
                cprint(f" ⮚  {'Request':>19}                       ", 'white', 'on_red', attrs=['bold'])
                print()
                ############################
                #   Request Headers        #
                ############################
                for k,v in response.request.headers.items():
                    k = k.decode('utf-8')
                    v = v[0].decode('utf-8')
                    print(f"{colored(k):>23}: {colored(v, 'green')}")
                    sleep(0.01)
                
                print(f"{colored('csrfmiddlewaretoken'):>30}: {colored(self.csrftokens[-1], 'green')}")
                print()
                ############################
                #   POST request fuzzform  #
                ############################
                if 'form_data' in response.meta:
                    for k,v in response.meta['form_data'].items():
                        print(f"{colored(k):>23}: {colored(v, 'green')}")
                        sleep(0.01)
                ############################
                #   Base form fields       #
                ############################
                if 'form_fields' in response.meta:
                    print()
                    fields = response.meta['form_fields']
                    dlexer(fields)

                print()    
                cprint(f" ⮘  {'Response':>19}                       ", 'white', 'on_red', attrs=['bold'])
                print()
                ############################
                #   Response Headers       #
                ############################
                for k,v in response.headers.items():
                    k = k.decode('utf-8')
                    v = v[0].decode('utf-8')
                    print(f"{colored(k):>23}: {colored(v, 'green')}")
                    sleep(0.01)
                print()

            ############################
            #   Exception summary      #
            ############################
            #exception_id = 'x-' + (hashlib.sha256(response.text.encode('utf-8')).hexdigest())[:5]
            exception_id = generate_exception_id(response.text)
            self.exception_parser = ParseXItem(response)

            self.exception_info = self.exception_parser.dump_traceback()
            self.exception_info['meta'] = response.meta
            self.exception_info['exception_id'] = exception_id
            _summary_ = self.exception_info['summary']
            _traceback_ = self.exception_info['traceback']
            exception_type = _summary_.get('Exception Type')
            self.EXCEPTIONS.append(self.exception_info)  
            exception_category = _summary_['Category']
            view_trigger = self.exception_info['view_trigger']

            if exception_category:
                exception_category = _summary_['Category'].split()[0]

            # add a new exception to the collection  
            exception = {
                'scan_id': self.scan_id,
                'scan_plugin': 'd4m8',
                'exception_id': exception_id,
                'exception_type': exception_type,
                'exception_class': exception_category,
                'module': view_trigger.get('shortpath'),
                'module_object': view_trigger.get('object'),
                'line_number': view_trigger.get('line_number'),
                'trigger': view_trigger.get('trigger_line'),
                'method': _summary_['Request Method'],
                'framework': 'Django',
                'framework_version': _summary_['Django Version'],
                'exception_meta': self.exception_info,
            }
            
            # Add the new exception to the collection
            VFDBOps(**exception).register('_EXCEPTIONS_')
            
            '''
            # >> Vimana API connector
            if response.xpath('//div[@id="summary"]//tr'):
                self.handle_exception_item(response)
            '''
            if not self.silent_mode:
                print(f"{colored(f'    {exception_type} ', 99, attrs=['bold']):>35}")
                print()
                for k,v in _summary_.items():
                    hl_color = 'green'
                    attrs=[]
                    if k in ['Exception Type']:
                        continue
                    
                    print(f"{colored(k):>23}: {colored(v,hl_color, attrs=attrs)}")
                print()
            
            # ** Exception trigger **
            for trigger in _traceback_:
                #######################################
                # Check for rule RESPONSE reqs
                #######################################
                #if self.RULE_SCAN_MODE and self.RULE_RESPONSE:
                if self.RULE_SCAN_MODE:
                    
                    # set default as Rule's Response req
                    self.RULE_REQS = self.RULE_RESPONSE

                    # Current Exception Module
                    CXM_FULL_PATH = trigger['MODULE_TRIGGERS']['Module']
                    CXM = CXM_FULL_PATH.split('/')[-1]
                    
                    # Check if Rule's Response is define and requirements match
                    if not self.req_match('target_modules', CXM):
                        continue
                    
                    trigger['MODULE_TRIGGERS']['Module'] = CXM_FULL_PATH.replace(CXM,colored(CXM, 'red'))
                                        
                    # Current Exception Function
                    CXF = trigger['MODULE_TRIGGERS']['Function']
                    
                    # Check if Rule's Response is define and requirements match
                    if not self.req_match('target_module_functions', CXF):
                        continue
                    
                    # Highlight matched function 
                    trigger['MODULE_TRIGGERS']['Function'] = colored(CXF, 'red')
                
                if not self.silent_mode:
                    print(f"{colored(' ➤  Trigger ', 99, attrs=[]):>35}")
                    print()
                    
                    for  k,v in trigger['MODULE_TRIGGERS'].items():
                        print(f"{colored(k.strip()):>25}: {colored(v.strip(), 'green')}")
                    
                    # ** Exception leaked vars ** 
                    print()
                    print(f"{colored(' ◎  vars ', 99):>40}")
                    print()

                hl_color_var = 'white'
                for APP_VAR,VALUE in trigger['MODULE_ARGS'].items():
                    if self.RULE_SCAN_MODE and self.RULE_ACTIONS:

                        # List of dicts
                        for ACTION in self.RULE_ACTIONS:
                            #extracted_vars = {}
                            ACTION_TYPE = ACTION.get('action_type', False)

                            if ACTION_TYPE and ACTION_TYPE == 'extract_function_vars':
                                
                                if not ACTION.get('function_vars', False):
                                    MAK = [k for k in trigger['MODULE_ARGS'].keys() if k not in ['request']]
                                    ACTION['function_vars'] = dict(zip(MAK, ['' for ma in MAK]))

                                    #input(f"++ Function vars not defined! → using: {ACTION['function_vars']}")

                                # update REQs to reflect ACTION 
                                self.RULE_REQS = ACTION

                                if self.req_match('function_vars', APP_VAR):
                                    hl_color_var = 'red'

                                    #needs to check if its a regex or what
                                    var_regex = ACTION['function_vars'].get(APP_VAR)

                                    if var_regex:
                                        match = re.search(var_regex, VALUE)
                                        if match:
                                            VALUE = match.group(1)

                                    extracted_vars[APP_VAR.strip()]=VALUE.replace("'",'').replace('"','').strip()

                            #elif ACTION_TYPE and ACTION_TYPE == 'exec':
                    
                    if not self.silent_mode:
                        if APP_VAR in ['request']:
                            continue

                        VALUE = VALUE.strip().replace("\n",'')
                        VALUE = highlight(VALUE,Python3Lexer(),TerminalFormatter()).strip()
                        print(f"{colored(APP_VAR.strip(), hl_color_var):>34}: {VALUE.strip()}")

                if self.RULE_SCAN_MODE and extracted_vars:
                    #self.RULE_COLLECTOR[self.RULE_NAME]['OUTPUT'].append(extracted_vars)
                    self.RULE_COLLECTOR.append(extracted_vars)

            if not self.silent_mode:
                print()
                print(colored('\u2500'*140, 'red', attrs=['dark']))
                input() if self.handler.get('pause_steps') else None
        #else:
        #    input(f"{response}: {response.meta['form_data']}")

    def test_file(self, file):
        with open(file, 'r') as file:
            yaml_data = file.read()

        deserialized_data = yaml.load(yaml_data, Loader=yaml.SafeLoader)
        deserialized_data = jsonpickle.decode(deserialized_data)
        print(f"++ Scan file Suscessfully recorded: {deserialized_data[0].keys()}")

    def record(self):
        from siddhis.prana.prana import siddhi as prana
        
        cves = []
        scan_file = f'{self.scan_id}.yaml'
        scan_output_path = f"{self.abs_cache_path}/{self.scan_id}"
        scan_output_file = f"{scan_output_path}/{scan_file}"
        scan_template = VFDBOps(**self.handler).get_model_dict("_SCANS_")
        
        scope = {
            'urls': self.start_urls
        }
        
        if self.EXCEPTIONS:
            scan_template['has_issues'] = True

            try:
                cves,cves_table = prana(**self.handler).get_cves_for_version()
            # TypeError: cannot unpack non-iterable bool object
            except TypeError:
                cves = []

            serialized_data = jsonpickle.encode(self.EXCEPTIONS)
            yaml_data = yaml.dump(serialized_data, sort_keys=False)

            os.makedirs(os.path.dirname(scan_output_file), exist_ok=True)

            with open(scan_output_file, 'w') as file:
                file.write(yaml_data)
        
            self.test_file(scan_output_file)

        scan_template.update(
            {
                'scan_id': self.scan_id,
                'scan_type': 'DAST',
                'scan_date': self.scan_time,
                'scan_hash': self.scan_hash,
                'scan_target': self.handler['target_url'],
                'scan_target_full_path': 'N.A',
                'scan_cache_dir': scan_output_path,
                'scan_output_file':scan_output_file,
                'project_framework': 'Django',
                'project_framework_version': self.handler['django_version'],
                'project_framework_total_cves': len(cves),
                'project_total_requirements': 'N.A',
                'project_total_view_modules': '?',
                'scan_scope': jsonpickle.encode(scope),
                'scan_plugin': self.handler['module_run'],
                'vmnf_handler': jsonpickle.encode(self.handler),
            }
        )
        
        VFDBOps(**scan_template).register('_SCANS_')
            
        print(f"[{datetime.now()}]: {self.scan_id} sucessfully recorded!")
        sleep(1)

    def closed(self,reason):
        import textwrap
        from tabulate import tabulate
        response_headers = {}

        if self.EXCEPTIONS:
            # if rule scan_mode
            ##########################################
            #  Handle defined Rule's Output format
            ##########################################
            if self.RULE_SCAN_MODE:
                if self.RULE_OUTPUT:
                    output_format = self.RULE_OUTPUT.get('format', False)
                    if output_format and output_format.lower() == 'table':
                        headers = self.RULE_COLLECTOR[0].keys() 
                        table_data = [[dct[key] for key in headers] for dct in self.RULE_COLLECTOR]  
                        rule_matches_table = tabulate(table_data, headers=headers, tablefmt="fancy_grid")
                        print(rule_matches_table)
                    elif output_format and output_format.lower() == 'json':
                        # export to json
                        pass

            # *** it'll fail right here when there's missing tokens but not exceptions, change this!
            exception_sample = self.EXCEPTIONS[0]
            summary = exception_sample.get('summary')
            response_sample = exception_sample['traceback'][0]
            response_headers = response_sample['RESPONSE_HEADERS']
            response_headers['Django Version'] = summary['Django Version']
            response_headers['Python Version'] = summary['Python Version']
            response_headers['Target'] = self.handler['target_url']
            self.handler['django_version'] = summary['Django Version']

        ##########################################
        #  POST endpoints missing CSRF Token
        ##########################################
        if self.missing_token: 
            cprint(' ➤ Endpoints missing csrftokenmiddleware:', 'white', attrs=['bold'])
            print()
            
            explanation = """These endpoints are associated with data-modifying actions performed through web forms in a Django application. Despite not implementing Django's csrftokenmiddleware, they are vulnerable to CSRF attacks."""
            
            explanation = '\n'.join('   ' + line for line in textwrap.wrap(explanation, width=60))
            print(explanation)
            print()

            if response_headers:
                # Response Headers
                for k,v in response_headers.items():
                    print(f"{colored(k, 'cyan'):>25}: {colored(v, 'green')}")
                    sleep(0.01)
                print()

            for endpoint in self.missing_token:
                for k,v in endpoint.items():
                    if k in ['response']:
                        continue
                    #print(f"{k:>25}: {v}")
                    if isinstance(v, list):
                        print(f"{k:>15}:")
                        for item in v:
                            item = f"\t\t{item:>25}"
                            item = ('\t   ' + highlight(str(item),HtmlLexer(),TerminalFormatter()).strip())
                            print(item)
                        continue
                    elif isinstance(v,dict):
                        print(f"{k:>15}:")
                        for i,j in v.items():
                            print(f"{i:>35}: {j}")
                        print()
                        continue

                    print(f"{k:>15}: {v}")
                print()
    
        self.record()
        reactor.stop()
        os._exit(os.EX_OK)

