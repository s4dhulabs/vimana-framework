# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                    - DJUNCH -


    Django application fuzzer module for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch
    
"""

from pygments.formatters import TerminalFormatter
import sys, re, os, random, string, platform
from lxml.html.soupparser import fromstring
from pygments.lexers import PythonLexer
from termcolor import cprint, colored
from prettytable import PrettyTable
from collections import OrderedDict 
from html.parser import HTMLParser
from resources.colors import *
from pygments import highlight
from bs4 import BeautifulSoup
from termcolor import colored
from netaddr import IPNetwork
from datetime import datetime
from time import sleep
import argparse
import hashlib
import pygments

from settings.siddhis_shared_settings import django_envvars as djev
from settings.siddhis_shared_settings import csrf_table as csrf
from settings.siddhis_shared_settings import set_header 
from settings.siddhis_shared_settings import api_auth
from settings.siddhis_shared_settings import payloads

from core.vmnf_shared_args import VimanaSharedArgs
from core.vmnf_thread_handler import ThreadPool

from resources.session.vmnf_sessions import createSession
from resources.vmnf_text_utils import format_text
from resources import vmnf_banners

import requests.exceptions
from requests import exceptions
from random import choice
import collections
import requests

from siddhis.prana import prana
from siddhis.tictrac import tictrac




class siddhi:   
    module_information = collections.OrderedDict()
    module_information = {
        "Name":            "Djunch",
        "Info":            "Django (Unchained) fuzzer",
        "Category":        "Framework",
        "Framework":       "Django",
        "Type":            "Fuzzer",
        "Module":          "siddhis/djunch",
        "Author":          "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":           "Django application fuzzer ",
        "Description":
        """
        \r  This tool was designed to audit applications running with the Django
        \r  framework. Acts as an input module for Vimana to collect base data. 
        \r  DMT works seamlessly with other framework tools such as Djonga, DJunch,
        \r  which are respectively brute force and fuzzing tools. Among the various
        \r  actions taken are: Identification of the state of Debug extraction
        \r  and mapping of application URL Patterns. This first step will serve as
        \r  input to the fuzzer process (performed by DJunch) where tests will be
        \r  conducted to handle and map unhandled exceptions, extract and identify
        \r  sensitive information in the leaks, implementation failure testing. With
        \r  the same initial DMT input the brute force process will be performed on
        \r  the API authentication endpoints (if available) and also on the Django
        \r  administrative interface (if available).

        \r  At the end of the analysis it is possible to query the data obtained
        \r  by DMT, using the commands to access contexts, view information about
        \r  the identified exceptions, view the source code leaked by the affected
        \r  modules, track CVEs and Security Tickets.

        \r  Use 'args' cmdto see all available options: 
        \r  $ vimana args --module dmt 

        """

    }

    module_arguments = '''
    ==========
    # Djunch #
    ==========

    \r* Creating a fuzzer instance to use in another siddhi:

    \rTo create a djunch instance it is necessary to pass the target in the format: 
    \rscheme:ip/domain:port, a list with URL Patterns and the namespace with the command line arguments, 
    \rin this way, the fuzzer can be invoked:

    \rfuzz = Djunch(base_r, self.expanded_patterns,**self.vmnf_handler)
    \rfuzz.start()

    \rthe 'fuzz' object will be a list containing two entries: the issues identified and the contexts (envleak contexts).

    \r* to simplify, in this version fuzzer will run against one target at a time
    
    '''

    def __init__(
            self,
            target=False, 
            up_collection=False, 
            **vmnf_handler
        ):
    
        self.pattern = '<dmt_trigger>'
        self._trigger_= {
            'html': False,
            'rtxc_mode': False,
            'trigger_start': False,
            'context_filter': False
        }

        self.vmnf_handler = vmnf_handler
        self.base_r = target
        self.up_collection = up_collection
        self.total_patterns = len(up_collection)
        
        self.debug = self.vmnf_handler['debug'] 
        self.verbose = self.vmnf_handler['verbose']
        self.quiet_mode = True if not self.verbose else False
        self.catched_exceptions = []

        # ==[ Main Fuzzer object - analysis issues by type ]==
        self._issues_ = {
            'exceptions': [],
            'configuration': []
        }
        # ==[ DMT envleak contexts ]==
        self.contexts = {
            'server': {},
            'environment': {},
            'exception': {},
            'session': {},
            'authentication':{},
            'authorization': {},
            'credentials': {},
            'csrf': {},
            'email': {},
            'upload': {},
            'communication': {},
            'services':{},
            'security_middleware':{}
        }
        self.FUZZ_TRACEBACK = {}
        self.FUZZ_RESULT = []

    def print_it(self, tag, value, color='green'):
        self.tag    = tag
        self.value  = value
        step = 1

        print("{0} \t {1}".format(
            colored(self.tag, 'white'),
            colored(self.value, color))
        )
        sleep(0.07)

    def show_lsource(self):
        
        line_pool = []
        self.triggers =[]
        self.lsc = 0

        self.trigger_points = collections.OrderedDict()
        self.trace_points = {}
        self.traceback = []

         # catches traceback context - <li class="frame django">
        traceback_frames = self.raw_traceback.findAll("li", {"class": "frame django"})
        for frame in traceback_frames:
            self.snippet_source = [] 
            
            if frame and frame is not None:
                module_path, function = str(frame).split('\n')[1].replace(
                        '</code>','').replace(
                        '<code>','').split('in ')

            if not self.quiet_mode: 
                fuzz_msg = ('\n→ Source code of module {} in {} function'.format(module_path, function))
                cprint(fuzz_msg, 'red', 'on_white', attrs=['bold'])
                print()
                sleep(1)

            hl_function = colored(function, 'white', "on_green", attrs=['bold'])
            for tag in frame.findAll("ol", recursive=True):

                count = 0
                match_text = str(tag)
                line_number = int(match_text[match_text.find('start')+7:match_text.find('">')])
                
                for line in tag.text.split('\n'):
                    if line:
                        start_line_b = line_number
                        line = highlight(
                            line,
                            PythonLexer(),
                            TerminalFormatter(),
                        )   

                        hl_line = ('{}  {}'.format(
                            colored(str(line_number).strip('\n'), 'yellow', attrs=['bold']),
                            line.replace(function, hl_function).strip('\n')
                            )
                        )

                        self.snippet_source.append(hl_line)

                        if not self.quiet_mode:
                            print(hl_line)
                        
                        line_pool.append(line_number)
                        line_number +=1
                        count +=1

                self.trace_point = {
                    'module_path': module_path,
                    'function': function,
                    'line_number': start_line_b,
                    'source_line': line,
                    'source_snippet': self.snippet_source
                }

                self.traceback.append(self.trace_point)

                # save only trigger points (function callbacks)
                if count == 1:
                    self.triggers.append(self.trace_point)
                
        if not self.quiet_mode:
            print()        
            cprint('⣸⢠   Triggers   \t', 'red', 'on_white', attrs=['bold'])
            print()

            for trigger in self.triggers:
                for k,v in trigger.items():
                    if k != 'source_snippet':
                        print(' - {}: {}'.format(k,
                            colored(str(v).strip('\n').strip(), 'green')
                            )
                        )
                print()    

    def save_in_context(self):
        ''' save exception data in right context and feed traceback object'''        
        
        self.FUZZ_TRACEBACK[self.header] = self.value

        if self.header in djev().SECURITY_MIDDLEWARE.keys():
            self.contexts['security_middleware'][self.header] = self.value 
        elif self.header in djev().SERVER_:
            self.contexts['server'][self.header] = self.value
        elif self.header in djev().ENVIRONMENT_:
            self.contexts['environment'][self.header] = self.value
        elif self.header in djev().EXCEPTIONS_:
            self.contexts['exception'][self.header] = self.value
        elif self.header in djev().SESSION_:
            self.contexts['session'][self.header] = self.value
        elif self.header in djev().AUTHENTICATION_:
            self.contexts['authentication'][self.header] = self.value
        elif self.header in djev().CREDENTIALS_:
            self.contexts['credential'][self.header] = self.value
        elif self.header in djev().CSRF_:
            self.contexts['csrf'][self.header] = self.value
        elif self.header in djev().EMAIL_:
            self.contexts['email'][self.header] = self.value
        elif self.header in djev().FILE_UPLOAD_:
            self.contexts['upload'][self.header] = self.value
        elif self.header in djev().COMMUNICATION_:
            self.contexts['communication'][self.header] = self.value
        elif self.header in djev().SERVICES_:
            self.contexts['services'][self.header] = self.value
        
    def dxt_parser(self,**dmt_trigger_mode):
         
        # if the parser is called by the DMT instead of the fuzzer itself
        if dmt_trigger_mode:
            self._trigger_ = dmt_trigger_mode
        
        # digest _trigger_ object values
        so_windows          = False
        _slash_             = '/'
        self.html           = self._trigger_['html']
        self.rtxc_mode      = self._trigger_['rtxc_mode']
        self.trigger_start  = self._trigger_['trigger_start']
        self.context_filter = self._trigger_['context_filter']
        divisor = '-' * 100

        # dummy verification - if not exception keyword in response 
        if not str(self.html).find('Exception'):
            return False
        try:
	    # AttributeError: 'NoneType' object has no attribute 'findAll'
            soup = BeautifulSoup(self.html, 'html.parser')
            summary = soup.find("div", {"id": "summary"})
            summary = summary.findAll("table", {"class": "meta"}) # genneral information about event
            metainfo = soup.findAll("table", {"class": "req"})    # where goes the passwords
            
            # catches traceback context
            self.raw_traceback = soup.find("div", {"id": "traceback"})
            self.traceback_context = self.raw_traceback.findAll("div", {"class": "context"})
            self.source_context = BeautifulSoup(str(self.traceback_context), "lxml")
            source_lenght = len(self.source_context.findAll("li", recursive=True))

            if self.source_context and self.debug:
                print('''\n       [djunch().parser(): {}] ↓
                \r\t  + source_context.lenght: {}'''.format(    
                    datetime.now(),
                    G_c + str(source_lenght) + D_c
                    ), end=''
                )
        except AttributeError:
            """ In this case we need to implement a generic parser to 
            digest exception traceback. 
            """
            pass
        except AttributeError:
            pass
        
        for entry in metainfo:
            rows = ''
            rows = entry.findAll('tr')
            for row in rows:
                row = str(row)
                self.header = row[row.find('<td>') +4:row.find('</td>')].strip()
                self.value  = row[row.find('<pre>')+5:row.find('</pre>')].strip().replace("'",'')
                
                if self.header.find('<') == -1:
                    self.save_in_context()

        for div in summary:
            rows = ''
            rows = div.findAll('tr')
            print('\n')
            for entry in rows: 
                entry = str(entry.text).replace(':\\','_dmt_').split(':')
                self.header = str(entry[0]).strip('\n')
                self.value = str(entry[1]).strip('\n').replace('_dmt_',':\\')
                
                if self.header.find('<') == -1:
                    self.save_in_context()
            
            # if first round of trigger/parser and debug mode so show environment and django information
            if self.trigger_start and self.verbose:
                self.trigger_start = False
                '''
                    In the first round of discovery, DMT will show in real time
                    Basic information about server/environment/creds and exception 
                    if Debug mode is enabled

                '''
                cprint('⣆⣇     Server    \t', 'white', 'on_red', attrs=['bold'])
                print()
                for k,v in self.contexts['server'].items():
                    print(" {}: {}".format(
                        k.replace('_',' ').capitalize(),
                        colored(v, 'green')
                        )
                    )
                print()
                sleep(1)

                cprint('⡯⠥  Environment  \t', 'white', 'on_red', attrs=['bold'])
                print()
                for k,v in self.contexts['environment'].items():
                    print(" {}: {}".format(
                        k.replace('_',' ').capitalize(),
                        colored(v, 'green')
                        )
                    )

                print()
                sleep(1)

                if str(self.contexts['environment']).find('.exe') \
                    and str(self.contexts['environment']).find(r':\\') != -1:
                        so_windows = True
                        _slash_ = '\\'
	        
            # get exception traceback header
            _xpt_ = self.contexts['exception'] 
            exception_location = _xpt_.get('Exception Location').strip()
            exception_type = _xpt_.get('Exception Type').strip()
            exception_value = _xpt_.get('Exception Value').strip()
            snip_value = exception_value

            # original value was stored in context / this step just cut to better presentation
            if len(snip_value) > 70: 
                snip_value = snip_value[:70] + '[snip]...'
                
            # strip basic exception information
            full_module_path = exception_location[:exception_location.find('in')]
            module_path = str(_slash_).join(full_module_path.split(_slash_)[:-1]) + str(_slash_)
            python_module = full_module_path.split(str(_slash_))[-1]
            function_call, line, line_number = (exception_location[exception_location.find('in') +2:]).split() 
            function_call = function_call.replace(',','') + '()'

            # create exception pattern with absolute module path and affected line number 
            pattern = str(full_module_path + ":" + line_number)
                
            # create a hash of exception pattern to avoid parse the same exception again
            exception_hash = hashlib.sha224(pattern.encode()).hexdigest()
                
            # store exception hash to check against new exceptions 
            if exception_hash not in self.catched_exceptions:
                self.catched_exceptions.append(exception_hash)
                
                # if verbose is enabled show exceptions in realtime during discovery 
                if self.verbose:
                    cprint('⣷⣄   Exception   \t', 'white', 'on_red', attrs=['bold', 'blink'])
                    print()
                    print('      Type: {}'.format(str(R_c + exception_type    + D_c)))
                    print('     Value: {}'.format(str(G_c + snip_value  + D_c)))
                    print('  Location: {}'.format(str(G_c + full_module_path  + D_c)))
                    print('  Function: {}'.format(str(G_c + function_call + D_c)))
                    print('      Line: {}'.format(str(G_c + line_number + D_c)))
                    print('     Lines: {}'.format(G_c + str(source_lenght) + D_c))
                    print()
                
                # call show_lsource (to get triggers in quiet and to show source code in verbose mode)
                self.show_lsource()
                print()

                # save basic details about current exception
                _exception_ = { 
                    'iid':      'UX{}'.format(len(self._issues_['exceptions']) + 1),
                    'x_hash':   exception_hash,
                    'type':     exception_type,
                    'value':    exception_value,
                    'pattern':  self.pattern,
                    'location': full_module_path,
                    'lmodule':  python_module, 
                    'function': function_call,
                    'line':     line_number,
                    'lines':    source_lenght,
                    'triggers': self.triggers,
                    'traceback':self.traceback,
                    'occ': 1,                   
                    'reference': 'CWE-215'
                }
        
                # save exception object
                self._issues_['exceptions'].append(_exception_)

            # if current exception hash is found in catched_exceptions so continue
            else:      
                if self.debug:
                    print('''\r\r       [djunch().parser(): {}] ↓
                    \r\t  + caught_exception: {} 
                    \r\t  + trigger: {} in {} at line {}
                    '''.format(
                        datetime.now(),
                        (R_c + exception_type + D_c),
                        python_module,
                        function_call,
                        line_number
                        )
                    )
                    sleep(0.50)

                # update occ count (occurrences of same exception)
                for issue in self._issues_['exceptions']:
                    if issue['x_hash'] == exception_hash:
                        issue['occ'] = issue['occ'] + 1
                        break
                continue 

        if dmt_trigger_mode:
            self.FUZZ_RESULT = [
                self.contexts,
                self._issues_,
                self.FUZZ_TRACEBACK
            ]
            return self.FUZZ_RESULT
        return True

    def get_csrftoken(self):

        #self.URL = URL
        self.CSRFTOKEN = False
        self.TCSRFTOKEN= '0' * 100  # just junk / needs to implement some random chars instead numbers

        # ~ Try to get crsftoken from a given URL in application 
        try:
            soup = BeautifulSoup(self.client.get(self.target_url).content, "lxml")
            self.CSRFTOKEN = soup.find('input', dict(name='csrfmiddlewaretoken'))['value']
        except TypeError as TE:
            pass
        except exceptions.ConnectionError as CE:
            pass 

        # ~ Check if a csrftoken was found in current URL 
        if self.CSRFTOKEN: 
            # ~ just creates a simple tampered token from a legitimate one: CSRFTOKEN + '!'
            self.TCSRFTOKEN = self.CSRFTOKEN + '!' 
   
    def get_unescape_html(self, raw_content):
        HParser = HTMLParser()
        return (HParser.unescape(raw_content))

    def fuzz_loop_patterns(self):
        ''' This method just do a loop in expanded URL patterns (patterns inside patterns)
            changing request payload to trigger exceptions. Isnot a exactly process
            but the main ideia here is:

            step 1: IndexError
            step 2: UnicodeEncodeError
            step 3: RuntimeError
            step 4: CSRF_Failure_View (settings fail tests)

            Of course, the tests are quite reduced in this version and still rudimentary in some points, 
            but new techniques must be implemented in the next versions of the framework 
            
            New stages and distinct tests will be added in the next version'''
        
        step_oot = True if self.trigger_step == 1 \
            or self.trigger_step == 2 else False

        # ~ Create client request instance
        self.client = requests.session()
        self.step_method = 'GET'

        # ~ dict to store current exception /one per time, if exception is found, so data to parser will be here
        self.x_trigger = {}
        self.loop_exception_found = False

        # test to debug some features 
        djunch_mode = True
        if djunch_mode:   
            # ~ General fuzzing status when loop_patterns [all steps]
            sys.stdout.write('\r   {0} Fuzzing: step ({1}/{2}) | Patterns: ({3}/{4}): {5}'.format(
                    (Gn_c  + "→" + C_c),
                    (R_c  + str(self.trigger_step) + D_c), 
                    (R_c  + str(self.dxt_steps -1) + D_c), 
                    (Wn_c + str(self.p_count)), 
                    (str(self.total_patterns) + C_c), 
                    (Y_c  + self.pattern + D_c)
                    )
            )
            sys.stdout.flush()
            sleep(0.05)
            #p_count += 1
            
            # ~ constructs base target url
            self.target_url = "{}/{}".format(self.base_r, self.pattern)
            
            # [1] - empty 'payload' - Just request URL Patterns one by one (this could trigger IndexError Exceptions-like
            if step_oot:
                if self.trigger_step == 1:
                    payload = ''
                # [2] - if UnicodeEncodeError-like step 
                elif self.trigger_step == 2: 
                    # ~ get a random Unicode payload to check for UnicodeEncodeError Warning (serve side, no leak)
                    payload = payloads().get_random_unicode_payload()
                
                # ~ constructs base target url
                # self.target_url = "{}/{}".format(self.base_r, self.pattern)
            
                # [steps 1,2] create fuzz url
                fuzz_url = '{}{}'.format(self.target_url, payload)
             
                # ~ If GET request via createSession() module steps 1,2
                self.vmnf_handler['target_url'] = fuzz_url
                response = createSession(**self.vmnf_handler)
                fuzz_response = self.get_unescape_html(response.text)
                response_status = response.status_code

            # [3] - RuntimeError-like exception via Django APPEND_SLASH trigger 
            # [4] - CSRF_Failure_view  - config fail (doesnt need DEBUG true)
            if self.trigger_step == 3 \
                or self.trigger_step == 4:
                # ~ Get crsftoken ~
                self.get_csrftoken()

                # [4] - CSRF_Failure_view tests 
                if self.trigger_step == 4:
                    self.step_method = 'POST'
                    # use tainted crsftoken to trigger 403 template (if implemented) or a CSRF FAILURE VIEW warning
                    self.CSRFTOKEN = self.TCSRFTOKEN
                
                # ~ Forge fake login data to send via POST request form [step 3,4]
                login_data = dict(
                    username=csrf().USERNAME,
                    password=csrf().PASSWORD,
                    csrfmiddlewaretoken=self.CSRFTOKEN
                )
                
                # ~ Set default request header from _shared_settings_
                request_headers = set_header(self.target_url, login_data, self.CSRFTOKEN).request_headers
                # ~ POST request with form login_data/csrftoken but without final slash '/'
                try:
                    RuntimeData = self.client.post(self.target_url, data=login_data, headers=request_headers)
                except requests.exceptions.ConnectionError:
                    print('[djunch:{}] Connection Error in fuzzer step {} / loop_patterns: {} / method: {}'.format(
                            datetime.now(),
                            self.trigger_step,
                            str(self.total_patterns),
                            self.step_method
                        )
                    )
                    #return False
                    pass

                # ~ RuntimeError Exception data
                fuzz_response = RuntimeData.content
                response_status = RuntimeData.status_code

            # ~ Check response (any step)
            if fuzz_response: 
                if response_status == 403:
                    # save configuration issues
                    _config_issue_ = {
                        'iid': 'CI{}'.format(len(self._issues_['configuration']) + 1),
                        'status': response_status,
                        'pattern': self.pattern,
                        'method': self.step_method,
                        'issue': 'csrf_failure_view',
                        'reference': 'CWE-209'
                    }
                    self._issues_['configuration'].append(_config_issue_)

                # ~ If response status equal 'Internal Server Error'
                if response_status == 500:
                    # set exception found flag (used by main_trigger)
                    self.loop_exception_found = True    # test: working
                    # if not UnicodeEncodeError [warning, no leak to parse]
                    if self.trigger_step != 2:
                        # create exception data object    
                        self._trigger_= {  
                            'html': fuzz_response,
                            'rtxc_mode': False,
                            'trigger_start': self.trigger_start,
                            'context_filter': False
                        }

                        exception = self.dxt_parser() 
                        
                        # disable trigger start status (used by parser to show a detailed output of current exception)
                        self.trigger_start = False

    def parse_args(self):
        ''' ~ siddhi needs only shared arguments from VimanaSharedArgs() ~'''

        parser = argparse.ArgumentParser(
                add_help=False,
                parents=[VimanaSharedArgs().args()]
        )

        return parser

    def start(self):
        '''in fact most modules do not need to implement their own parser, 
        because vimana already sends the command line handler with all 
        the arguments for the modules executed with the 'run' command
        so this is just a test'''

        djunch_handler= argparse.Namespace(
            ignore_state = False,       # ignore state - disable IP and port state verification
            single_target = False,      # single target scope
            scope  = False,             # file with a list of targets
            range  = False,             # ip range, 192.168.12.0-20
            cidr   = False,             # cidr range: 192.168.32.0/26
            port   = False,             # single port verification
            single_port   = None,       # single port verification
            portr  = False,             # port range: 8000-8010
            portl  = False,             # port list: 8999, 5001, 9000, 7120
            debug  = False              # debug mode
        )

        options = self.parse_args()
        djunch_handler.args = options.parse_known_args(
            namespace=djunch_handler)[1]

        num_threads = 3
        self.dxt_steps = 5
        self.trigger_start = True
        count_step = 1
        self.trigger_step = 1   
        pool = ThreadPool(num_threads)

        print('{0} Starting DJunch fuzzer against {1} / {2} URL Patterns'.format(
            (Gn_c  + "⠿⠥" + C_c), 
            (G_c  + self.base_r + W_c), 
            (str(self.total_patterns) + D_c))
        )
        sleep(1)

        # ~ range in dxt_steps, starts in 1 defines how many steps to run with loop patterns (according with payloads)
        for _ts_ in range(1, self.dxt_steps):
            self.p_count= 1
            self.trigger_step = _ts_
            
            '''this fuzzing steps needs some threads, but in recente tests things goes wrong'''
            for pattern in self.up_collection:
                if pattern.startswith('/'):
                    pattern = pattern[1:]

                self.pattern = pattern.strip('\n').rstrip()
                #pool.add_task(self.fuzz_loop_patterns) # threading tests 
                self.fuzz_loop_patterns()
                self.p_count +=1
            #pool.wait_completion() # threading tests

        # final object results - used in dmt to show final result and inspect issues
        self.FUZZ_RESULT = [
            self.contexts,
            self._issues_,
            self.FUZZ_TRACEBACK
        ]

        for k,v in self.FUZZ_TRACEBACK.items():
            print('\t{}:    {}'.format(k,v))
            sleep(0.5)
        input()
        return self.FUZZ_RESULT



