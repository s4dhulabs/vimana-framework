# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                 - DMT v2 -


    Django Misconfiguration Tracker module for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch

"""




import sys
sys.path.insert(0, '../')

from random import random, choice, randint
from urllib.parse import urlparse
from datetime import datetime
from mimesis import Generic

import re
import os
import signal
import scrapy
import twisted
import requests
from time import sleep
import urllib3.exceptions
from mimesis import Generic
from urllib.parse import urljoin
from scrapy.http import HtmlResponse

from scrapy import signals
from scrapy.shell import inspect_response
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from scrapy.utils.log import configure_logging  
from scrapy.http import HtmlResponse
from scrapy.http.headers import Headers
from neotermcolor import colored,cprint
from pygments import highlight

from res.vmnf_validators import get_tool_scope as get_scope
from siddhis.sttinger.sttinger import siddhi as sttinger
from core.vmnf_shared_args import VimanaSharedArgs
from siddhis.djunch.djunch import siddhi as Djunch
from res import colors


class DMTEngine(scrapy.Spider):
    name = 'DMTengineParser'

    def __init__(self, *args, **vmnf_handler):
        super(DMTEngine, self).__init__(*args,**vmnf_handler)
        
        self.tps = False
        self.f_start = ' _n0p_ '
        self.f_map = ' _n0p_ '
        self.vmnf_handler = vmnf_handler
        self.target_url = vmnf_handler.get('target_url')
        self.debug_is_on = vmnf_handler.get('debug')
        self.step_method = vmnf_handler.get('method')
        self.headers =  vmnf_handler.get('headers')
        self.cookies = vmnf_handler.get('cookie')
        self.download_timeout = vmnf_handler.get('download_timeout')
        self.meta = vmnf_handler.get('meta')
        self.patterns = vmnf_handler.get('patterns')
        self.auto_mode = vmnf_handler.get('auto')
        self.silent_mode = True if vmnf_handler.get('silent') \
            or vmnf_handler.get('sample') else False

        self.set_closed = False
        self.found_version = False
        self.GenObj = Generic()

        self.only_patterns=[]
        self.raw_patterns =[]
        self.app_patterns =[]
        self.exit_step = False
   
    def get_raw_patterns(self,response):
        return [('/'.join(pattern.split()).replace('//','/'))\
            for pattern in [p.xpath('.//text()').get().strip()\
                for p in response.xpath('//div[@id="info"]//li')
                ]
            ]

    def closed(self,reason):
        if self.exit_step:
            return False

        if not self.raw_patterns:
            if not self.tps:
                cprint("""[{}] Missing scope!\n""".format(
                    datetime.now()), 'magenta', attrs=['bold'])
            else:
                cprint("""[{}] The target doesn't seem to be up. Check out if the application is running, and try again.\n""".format(
                    datetime.now()), 'magenta', attrs=['bold'])

            os._exit(os.EX_OK) 

        self.vmnf_handler['fuzz_regex_flags'] = self.fuzz_flags_context
        self.vmnf_handler['view_context'] = self.p_context
        self.vmnf_handler['raw_patterns'] = self.raw_patterns
        self.vmnf_handler['app_patterns'] = self.app_patterns
        self.vmnf_handler['patterns'] = self.only_patterns
        self.vmnf_handler['target_url'] = self.target_url
        self.vmnf_handler['fingerprint'] = self.found_version
        
        # call new djunch engine
        Djunch(**self.vmnf_handler).start()

        #os._exit(os.EX_OK)

    def start_requests(self):
        
        targets_ports_set = []
        
        # This will be used in future versions to configure the fuzzer options: full, fast, etc.
        if not self.vmnf_handler['scope'] \
            and not self.vmnf_handler['docker_scope']\
            and not self.vmnf_handler['runner_mode']:

            print(VimanaSharedArgs().shared_help.__doc__)
            try: 
                sys.exit(1) 
            except builtins.SystemExit:
                pass

        self.tps = targets_ports_set
        self.target_url = self.vmnf_handler.get('target_url')
        self.base_url = self.vmnf_handler.get('target_url')
        self.tps = self.target_url

        if not self.base_url.startswith('http'):
            self.target_url = 'http://' + self.base_url

        try:
            requests.get(self.target_url)
        except requests.exceptions.ConnectionError:
            self.target_url = 'https://' + self.base_url

        dmt_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c_target = colored(self.target_url,'white')
            
        if not self.vmnf_handler.get('sample'):
            cprint("\n[{}] Starting DMT against {}...".format(datetime.now(),c_target), 'cyan')
            sleep(1)
            
        self.target_trigger = urljoin(self.target_url,str(random()))

        yield scrapy.Request(
            self.target_trigger, 
            callback=self.status_handler,
            headers=self.headers,
            meta=self.meta,
            errback=self.failure_handler,
            dont_filter = True
        )

        self.set_closed = True

    def failure_handler(self,failure):
        if "ResponseNeverReceived" in str(failure.type):
            cprint("[{}] The target doesn't seem to be vulnerable.\nException: {}".format(
                datetime.now(), colored(failure.type,'red')), 'magenta')
            os._exit(os.EX_OK)

    def run_passive_fingerprint(self):
        sttd = {
            'target_url': self.target_url,
            'siddhi_call': self.vmnf_handler.get('module_run'),
            'quiet_mode': True,
            'search_issues':True
        }
        
        cprint('\n{}Starting passive fingerprint...'.format(self.f_start),'cyan')
        sleep(1)
        
        self.found_version = sttinger(**sttd).start()
        
        if not self.found_version:
            print('{} Version not identified'.format(self.f_map))
            return False

        hl_v = colored(self.found_version.get('versions'),'red',attrs=['bold'])

        print('{} Running Django {} / ({} - {}) → {} associated tags.'.format(
            self.f_map,hl_v,self.found_version.get('min'),
            self.found_version.get('max'),len(self.found_version.get('version_list'))
            )
        )
        print('{} {} CVEs'.format(self.f_map,len(self.found_version.get('cves'))))
        print('{} {} Security Tickets'.format(self.f_map,len(self.found_version.get('tcts'))))
        
    def status_handler(self,response):
        self.f_start = colored('▸ ','red',attrs=['bold'])
        self.f_map = colored('  ↪','blue')
        self.exit_step = False

        if not self.vmnf_handler.get('sample'):
            print()
            for k,v in response.headers.items():
                print('   - {}: {}'.format(k.decode(),v[0].decode()))
        
        # passive framework version fingerprint - sttinger
        if not self.vmnf_handler.get('sample'):
            self.run_passive_fingerprint()
        
        if not self.vmnf_handler.get('sample'):
            cprint('\n{}Checking DEBUG status...'.format(self.f_start),'cyan')
            sleep(0.20)

        if response.status == 404:
            d = colored('DEBUG', 'green', attrs=['bold'])
            
            exp_msg = (response.xpath('//div[@id="explanation"]//p//code/text()').get())
            
            if (exp_msg) is None:
                exp_msg = colored('Debug is not enabled', 'red')
                cprint("\n[{}] The target doesn't seem to be vulnerable: {}.\n".format(
                    datetime.now(), exp_msg), 'magenta')
                os._exit(os.EX_OK)

            exp_msg = exp_msg.replace(' ','').strip()

            if exp_msg != 'DEBUG=True':
                d = colored('DEBUG', 'red',attrs=['dark'])
                if not self.vmnf_handler.get('sample'):
                    print('{} {} mode is disabled.\n'.format(self.f_map,d))
                    return False
            
            if not self.vmnf_handler.get('sample'):
                print('{} {} mode is activated.\n'.format(self.f_map,d))
                sleep(1)
            
            if not self.auto_mode \
                and not self.vmnf_handler.get('sample'):

                confirm_step = 'n'
                confirm_step = input(colored('[DMT] The target is vulnerable, would you like to continue? (Y/n) → ', 'cyan'))
            
                if not confirm_step\
                    or confirm_step.lower() == 'n':
                    
                    self.exit_step=True 
                    
                    cprint('\nSeeya sadhu! Leaving the ship...\n', 'green')
                    sleep(1)
                    os._exit(os.EX_OK)

            self.URLconf=(response.xpath('//div[@id="info"]//p//code/text()').get()).strip()
            
            if self.URLconf is not None:
                hl_uc = colored(self.URLconf, 'blue')
                if not self.vmnf_handler.get('sample'):
                    print('{} Dumping APP patterns from URLconf {}'.format(self.f_start,hl_uc))
                    sleep(0.10)

            if not self.app_patterns:
                
                # get apps patterns
                self.get_app_patterns(response)
                
                # expand patterns 
                self.patterns_mapper()
                
                # patterns by view
                self.get_view_context_patterns()
        
                # set fuzzer flags: antiregex
                self.set_flag_regex_patterns()
                
                #return 
            
    def get_view_context_patterns(self):
        self.p_context={}
        
        for p in self.raw_patterns:
            pwv = p
            view = p.split('/')[1].strip()\
                if p.count('/') >= 2 else False
            view = self.get_clean_pattern(self.strip_chars(view))\
                if view else '?'

            if '[name=' in p:
                view = p.split('/')[-1].split('=')[1][:-1].strip("'")
                pwv = p[:p.find('[')]
            
            if view not in self.p_context.keys():
                self.p_context[view] = []

            if pwv not in self.p_context[view]:
                self.p_context[view].append(pwv)
 
    def set_flag_regex_patterns(self):
        
        fuzz_flag = '{{fuzz_flag}}'
        self.fuzz_flags_context = {}
        total_views = len(self.p_context.keys())
        tv_hl = colored(total_views, 'white')
        
        if not self.vmnf_handler.get('sample'):
            print(f'\n{self.f_start} Setting up contextual fuzzing flags for {tv_hl} views')
            sleep(0.20)
        
        v_count=0
        for view,patterns in self.p_context.items(): 
            v_count +=1
            v_hl = colored(view, 'blue')
            t_hl = colored(len(patterns),'blue')
            
            if not self.vmnf_handler.get('sample'):
                dmt_step=(f'{self.f_map} Parsing ({t_hl}) patterns in view {v_hl} ({v_count}/{total_views})...')

                print(dmt_step.ljust(os.get_terminal_size().columns - 1), end="\r")
                sleep(0.10)
            
            for pattern in patterns:
                found_regex=False
                _p_ = self.strip_chars(pattern)
                
                # save clean patterns to feed djunch scope builder
                c_pattern = self.strip_chars(self.clean_regex_marks(_p_))
                if c_pattern \
                    and c_pattern\
                    not in self.only_patterns:
                    
                    self.only_patterns.append(c_pattern)

                for item in _p_.split('/'):
                    if item.startswith('('):
                        found_regex = True
                        _p_ = _p_.replace(item,fuzz_flag)
                       
                        # sample mode enabled, avoid verbose/debug messages
                        if not self.vmnf_handler.get('sample'):
                            reg_found = ('\n\t+ regex: {}'.format(
                                colored(item.strip(),'magenta',attrs=[])
                                )
                            )

                            print(reg_found.ljust(os.get_terminal_size().columns - 1), end="\r")
                            sleep(0.10)

                        if view not in self.fuzz_flags_context.keys():
                            self.fuzz_flags_context[view]=[]
                            
                if found_regex:
                    self.fuzz_flags_context[view].append(_p_)
                    ff_hl = colored(fuzz_flag, 'magenta', attrs=[])
                    _p_hl = colored(_p_.strip(),'blue').strip()

                    if not self.vmnf_handler.get('sample'):
                        print('\n\t→ {}\n'.format(_p_hl.replace(fuzz_flag,ff_hl)))
                        sleep(0.01)

                else:
                    if not self.vmnf_handler.get('sample'):
                        print()

    def strip_chars(self,pattern):
        return(pattern.replace('^','').replace(
            '/$/','/').replace('\\','').replace(
                '^r','').replace('?P','').replace(
                    '$','').replace('//','/').replace(
                            '/r/','/').strip())

    def clean_regex_marks(self,pattern):
        return(re.sub('(\<.*\>|\(.*\))','',pattern))

    def get_clean_pattern(self,pattern):
        return re.sub('[^0-9a-zA-Z\__]+', '', pattern)

    def patterns_mapper(self, external_mode=False):

        if external_mode:
            self.app_patterns = self.vmnf_handler.get('fuzz_patterns')
            self.headers = {'Origin': ''}

        trick = colors.bn_c + 'NoReverseMatch' + colors.D_c
        p_count = 0
        total_p = len(self.app_patterns)
        hl_total = colored(total_p, 'blue')
        
        if not self.vmnf_handler.get('sample'):
            print(f'{self.f_start}Starting PatternMapper via {trick}')
            sleep(0.30)
        
        for pattern in self.app_patterns:
            p_count +=1
            hl_p_count = colored(p_count, 'white')
            if p_count == total_p:
                hl_p_count = colored(p_count,'blue')

            self.raw_patterns.append(pattern)
            
            if pattern.startswith('[name='):
                continue

            if pattern.find('['):
                pattern = pattern[:pattern.find('[')]

            p = colored(pattern, 'white', attrs=['bold'])
            
            if not self.vmnf_handler.get('sample'):
                print(f'\n{self.f_map} Mapping app {p} ({hl_p_count}/{hl_total})...\n')
                sleep(0.10)

            payload = self.get_clean_pattern(pattern) + '/' + str(random())
            
            self.new_target_url = urljoin(self.target_url, payload)
            self.headers['Origin']  = self.target_url
            self.headers['Referer'] = self.new_target_url
            
            try:
                r = requests.get(self.new_target_url,headers=self.headers)
            except KeyboardInterrupt: #requests.exceptions.MissingSchema:
                print('[DMT:PMap] → Invalid scope: Missing HTTP scheme.\n')
                return False

            response = HtmlResponse(url=self.new_target_url, body=r.text, encoding='utf-8')
            
            if r.status_code == 404:
                for map_p in self.get_raw_patterns(response):
                    map_p_hl = map_p
                    if map_p.startswith(pattern):
                        if '[name=' in map_p:
                            view = map_p.split('/')[-1]
                            view_hl = colored(view,'blue')
                            map_p_hl = map_p.replace(view,view_hl)

                        if not self.vmnf_handler.get('sample'):
                            print('   + {}'.format(map_p_hl))
                    
                        if map_p not in self.raw_patterns:
                            self.raw_patterns.append(map_p)

                        sleep(0.02)

        if external_mode:
            return self.raw_patterns

    def get_app_patterns(self,response):
        for pattern in self.get_raw_patterns(response):
           self.app_patterns.append(pattern)
        
        hl_ap = colored(len(self.app_patterns), 'white')
        if not self.vmnf_handler.get('sample'):
            print(f"{self.f_map} {hl_ap} app patterns\n")
            sleep(0.30)

            for pattern in self.app_patterns:
                print(f'   - {pattern}')
                sleep(0.05)
            print()

