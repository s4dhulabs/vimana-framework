# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                    - DMT -


    Django Misconfiguration Tracker module for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch

"""

from . _dmt_report import resultParser
from core.vmnf_shared_args import VimanaSharedArgs
from core.vmnf_thread_handler import ThreadPool
from core.vmnf_thread_handler import Worker
from core.vmnf_thread_handler import ThreadPool

from resources.session.vmnf_sessions import createSession
from resources.vmnf_validators import get_tool_scope

from .. djunch.djunch import siddhi as Djunch 
from settings.siddhis_shared_settings import api_auth as APIAuth
from resources import colors

from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from pygments import highlight

import sys, re, os, random, string, platform
from lxml.html.soupparser import fromstring
from termcolor import colored, cprint
from prettytable import PrettyTable
from collections import OrderedDict
from html.parser import HTMLParser
from urllib.parse import urlsplit
from resources.colors import *
from tldextract import extract
from bs4 import BeautifulSoup
from netaddr import IPNetwork
from datetime import datetime
from time import sleep
import collections
import argparse
import hashlib
import pygments


    

class siddhi:  
    module_information = collections.OrderedDict() 
    module_information = {
        "Name":         "DMT",
        "Info":         "Django Misconfiguration Tracker",
        "Category":     "Framework",
        "Framework":    "Django",
        "Type":         "Tracker",
        "Module":       "core/modules/tracker/dmt",
        "Author":       "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":        "Tracks and exploits misconfigurations in Django applications", 
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
        \r  modules.

        \r  Run DMT with 'args' command to show all available options: 
        \r  $ vimana args --module dmt

        """

    }
    
    # help to 'args' command in main vimana board: vimana args --module dmt
    module_arguments = VimanaSharedArgs().shared_help.__doc__

    def __init__(self, **vmnf_handler):

        self.vmnf_handler = vmnf_handler
        self.threads = vmnf_handler['threads'] 
        self.num_threads = self.threads if self.threads <= 10 else 10
        self.fuzz_mode = False
        self.pool = ThreadPool(self.num_threads)

        # root URL patterns
        self.xlp_tbl = PrettyTable()
        self.xlp_tbl.field_names = [' # ', 'URL Pattern', 'View name']
        self.xlp_tbl.align = "l"
        self.xlp_tbl.title = colored(
            "Root URL Patterns",
            "white",
            attrs=['bold']
        )

        # mapped URL patterns
        self.xlp_tbl_x = PrettyTable()
        self.xlp_tbl_x.field_names = [' # ', 'URL Pattern', 'View name']
        self.xlp_tbl_x.align = "c"
        self.xlp_tbl_x.title = colored(
            "Mapped URL Patterns",
            "white",
            attrs=['bold']
        )

        self.debug_status = False
        self.mu_patterns = []

    def random_value(self, stringLength=6):
        extensions = ['','.txt','.html','.','.js','.css',"_","~"]
        ext = ''
        if int(str(datetime.now())[-3]) % 2:
            ext = str(random.choice(extensions))
            _p_ = string.ascii_letters + string.digits
        else: 
            ext = ''
            _p_ = string.ascii_letters
        
        return ''.join(random.choice(_p_) for i in range(stringLength)) + ext

    def print_it(self, tag, value, color='green'):
        self.tag    = tag
        self.value  = value
        step = 1

        print("{0} \t {1}".format(
            colored(self.tag, 'white'),
            colored(self.value, color))
        )
        sleep(0.07)
        
    def debug_is_true(self):
        not_debug_status = True
        
        if not self.dmt_start_request:
            print("[+] Something went wrong in Rama Empire, bro...")
            return False
        try:
            soup = BeautifulSoup(self.dmt_start_request, "lxml")
            status = str((soup.find("div", {"id": "explanation"})).find("p"))
            debug_status = ((status[status.find("DEBUG"):status.find("</")]).split('=')[1]).strip()
            debug_status = bool(debug_status)
            
            if debug_status:
               not_debug_status = False
               self.print_it('   → Django Port:', self.dmt_start_port)   
               self.print_it('   → Django DEBUG:', 'True')  

               # extracts URLConf file
               info = str((soup.find("div", {"id": "info"})).find("p"))
               URLConf = info[info.find("<code>")+6:info.find("</")]
               URLConf = 'empl_cms.urls'
               self.print_it('   → ROOT_URLCONF:', URLConf)  
               return True
            else:
                if not_debug_status and self.last_step:
                   print("{}-{} Django {}DEBUG{} seems to be disabled".format(
                       Pn_c, D_c, Rn_c, D_c
                       )
                    )
                   return False 	
        except AttributeError:
            if not_debug_status and self.last_step:
               print("{}-{} Django {}DEBUG{} seems to be disabled".format(
                   Pn_c, D_c, Rn_c, D_c)) 
               return False 	
        except TypeError: 
            pass

    def get_unescape_html(self, raw_content):        
        HParser = HTMLParser()
        return (HParser.unescape(raw_content))

    def check_api_auth_points(self):
        api_auth = PrettyTable()
        api_auth.field_names = ['id', 'URL', 'status', 'methods']
        api_auth.align = "l"
        api_auth.border = True
        api_auth.header = True
        api_auth.padding_width = 0

        ef = False
        APIAuthUrls = []
        methods = None

        for pattern in self.root_url_patterns:
            if pattern.endswith('/'):
                pattern = pattern[:pattern.find('/')]
            sys.stdout.write('\r{0} Checking common API authorization endpoints ({1})'.format(
                (Cn_c + "ø" + C_c),
                (Y_c + pattern + D_c)
                )
            )
            sys.stdout.flush()
            sleep(0.07)

            if pattern in APIAuth().endpoints:
               if not pattern in APIAuthUrls:
                  APIAuthUrls.append(pattern)   
           
        count = 1
        for path in APIAuthUrls:
            auth_path = self.dmt_start_base_r + '/' + path
            self.vmnf_handler['target_url'] = auth_path
            api_test_response = createSession(**self.vmnf_handler)
            response = self.get_unescape_html(api_test_response.text)        
            response_status = api_test_response.status_code

            if not response:
               continue
              
            if response_status == 405:
                ef = True
                methods   = str(api_test_response.headers['Allow'])
                methods_c = colored(methods, 'green')
                status_c  = colored(response_status, 'yellow')
                  
                if len(auth_path) > 45:
                    auth_path = path
               	api_auth.add_row([count, auth_path, status_c, methods_c])
                count +=1
        print() 
        if ef:
            print(api_auth)
            sleep(1)
            return True
        
        print("   {0} No authorization endpoints identified".format((Rn_c + "→" + D_c))) 
        return False
    
    def check_django_adm(self):
        
        _fmwk_ = "Django"
        ok    = str(Gn_c + "→" + D_c)
        vrf   = str(Yn_c + "→" + D_c)
        fail  = str(Rn_c + "→" + D_c)
        path = ''
        adm_path =(Gn_c + "{}" + D_c).format(path) 
        rel_path    = '/login/?next=/admin/'	
        
        print("{0} Looking for Django Administration Interfaces...{1}".format(
            (Gn_c + "⠿⠥" + C_c),
            D_c,
            )
        )
        
        if not found_admin_flag:
            if found_admin_pattern:
                print("   {0} Django Administration: no-default path...".format(vrf))
                django_adm_path = "/" + found_admin_pattern + rel_path
            else:
                print("   {0} Django Admin path not found".format(fail))
                return False
        else:
            django_adm_path = "/admin" + rel_path
	    #/api/admin/login/?next=/api/admin/
	    #/admin/login
	
        adm_path = (self.dmt_start_base_r + django_adm_path) 
        self.vmnf_handler['target_url'] = adm_path
        response = createSession(**self.vmnf_handler)
        djadmin_response = self.get_unescape_html(response.text)
        response_status = response.status_code

        if not djadmin_response:
            print("  {0} Django administration interface seems to be disabled".format(fail))
            return False
             
        if response_status == 200:
            print("   {0} Django administration: seems to be available...".format(ok))
            sleep(0.10)
            print("   {0} Django administration: Checking...".format(ok))
            sleep(0.10)
              
            soup = BeautifulSoup(djadmin_response, 'lxml')
            try:
                r_check = ''	
                check = str((soup.find("h1", {"id": "site-name"})).find("a"))
                adm_pattern = (check[check.find("<a"):check.find("</a>")]).split(">")[1]
            except AttributeError as AE:
                return False
             
            if adm_pattern == "Django administration":
                print("   {0} Django administration: {1}".format(ok, str(P_c + adm_path + D_c)))
                sleep(0.10)
                return True
	      
	    # Django 管理 
            elif (adm_pattern.split()[0]) == _fmwk_:
                print("   {0} Django administration: abducting {1}...".format(ok, adm_pattern.split()[1]))
                sleep(0.10)
                print("   {0} Django administration: {1}".format(ok, str(Gn_c + adm_path + D_c)))
            elif (soup.title.string).find('Django') > -1:
                print("   {0} Django administration: {1}".format(ok, str(Gn_c + adm_path + D_c)))
            else: 
                return False		
        elif response_status == 404:
            print('[+] DMTSTATUS {}:{}'.format(len(dadmp_request),status))
        elif response_status == 500:
            self.dxt_parser(dadmp_request, True)
        else: return False  		      
    
    def get_url_patterns(self):

        login_flags =['login', 'auth', 'logout',' loggedin', 'signup']            
        login_flag_count = 0

        # yeap this is uggly, soon I will fix it 
        global found_admin_flag
        global found_admin_pattern
        global found_api_flag
        global api_flag
        global tag_count
        global tag_count_x
        global xp_count

        if self.fuzz_mode:
            self.fuzz_mode = False
            xp_count = 0
            tag_count_x = 1
        
        if not self.exp_mode:
            self.root_url_patterns = []
            self.expanded_patterns  = []
            api_flag = False
            found_admin_flag = False
            found_admin_pattern = False
            found_api_pattern = False
            tag_count   = 1
            tag_count_x = 1
            xp_count = 0

        epf = False
        last_ptn = False
        found_pattern = False
        name = "*"
        
        tree = fromstring(self.expanded_response)
        for i in tree.xpath("//li/text()"):
            found_pattern = True
            # removing blank lines in case of paths jose-admin/ login/
            rgx = re.compile(r'\s+')
            parsed_tag = re.sub(rgx, '', i)
            url_pattern = (parsed_tag[:parsed_tag.find("[")]).strip("(?").strip("^").rstrip('\/')
            url_pattern = url_pattern.replace("^","").replace("$","").replace("\.",'')

            if (parsed_tag.find('[') != -1):
               try: name = parsed_tag.split("[")[1].split('=')[1].replace("]",'').replace("'",'')
               except IndexError: pass

            for lflag in login_flags:
                if lflag in url_pattern:
                   login_flag_count += 1

            # if not URL expassion phase (mapping)
            if not self.exp_mode:
                if url_pattern == 'admin': 
                    found_admin_flag = True
                elif 'admin' in url_pattern:
                    found_admin_pattern = url_pattern
                elif url_pattern == 'api-auth':
                    api_flag = True
                elif 'api' in url_pattern:
                    found_api_pattern = url_pattern

                if not url_pattern in self.root_url_patterns:
                    self.root_url_patterns.append(url_pattern)
                    self.xlp_tbl.add_row([tag_count, url_pattern, name])
                    tag_count += 1
            else:
                if url_pattern \
                    and not url_pattern in self.expanded_patterns:

                    xp_count += 1
                    self.expanded_patterns.append(url_pattern)
                    
                    current_pattern = {
                        ' # ': tag_count_x,
                        'pattern': url_pattern,
                        'view': name
                    }
                    
                    self.mu_patterns.append(current_pattern)
                    self.xlp_tbl_x.add_row([tag_count_x, url_pattern, name])
                    tag_count_x += 1

        if not self.exp_mode:
           self.print_it('   → URL Patterns:', (tag_count - 1))  
           self.print_it('   → Login URLs:', login_flag_count)  
           sleep(2)
           print(self.xlp_tbl)
    
    def djmimic(self):

        if not self.expanded_patterns:
            return False

        # Django setting files mimic: urls.py
        # Should be a separated function
        print("\n\n{}/urls.py".format(self.x_pattern))
        print("app_name= '{0}'\n".format(colored(self.x_pattern, 'yellow')))
        print('urlpatterns = [')
        for pattern in self.expanded_patterns:
            if pattern.startswith(self.x_pattern): 
                url = pattern[pattern.find('/')+1:]
                if len(url) > 0 and url[-1] == '/':
                    url = url[:-1]
                view = url
                name = view
                if len(url) == 0:
                    view = self.x_pattern
                    name = view
                if url != self.x_pattern:
                    print(colored("    url(r'^{0}',\n        views.{1},\n        name='{2}'),".format(
                                            url, view, name), 'white')
                            )
                    sleep(0.07)
        
        print("\n]")
        #sleep(1)
                    
    def expand_UP(self, up_fuzz_scope = False):
       
        self.exp_mode = True
        up_c = 1
        
        # when this method is called via vimana_engine
        if up_fuzz_scope:
            self.fuzz_mode = True
            self.expanded_patterns = [] 
            self.root_url_patterns = up_fuzz_scope
            target  = self.vmnf_handler['single_target']
            port    = self.vmnf_handler['single_port']
            
            try: 
                self.dmt_start_base_r  = ('http://{}:{}'.format(target,port))
            except TypeError:
                print('[dmt().expandup()] Failure to validate target, check it and try again')
                return False

        try:
            n_up = len(self.root_url_patterns)
        except AttributeError:
            print('[dmt().expandup()]: Missing root URL patterns')
            return False

        url_model = {}
        trick_name = colors.bn_c + 'NoReverseMatch' + colors.D_c

        for x_pattern in self.root_url_patterns: 
            self.x_pattern = x_pattern
            if x_pattern.endswith('/'):
                x_pattern = x_pattern[:-1].strip()

            app_name = ("app_name = '" + x_pattern + "'")
            expanded_pattern = '{}/{}/_._x'.format(self.dmt_start_base_r, x_pattern)
            
            sys.stdout.write("\r{0} Mapping URL pattern via {1} ({2}/{3}) -> {4}".format(
                    colors.Gn_c + "⠿⠥" + colors.C_c,
                    trick_name,
                    up_c, n_up, 
                    colors.Y_c + x_pattern + colors.D_c,
                    colors.Y_c + app_name + colors.D_c
                    )
            )
            sys.stdout.flush()
            sleep(self.vmnf_handler['wait']) 
            up_c += 1
           
            # up request
            self.vmnf_handler['target_url'] = expanded_pattern
            response = createSession(**self.vmnf_handler)
            self.expanded_response = self.get_unescape_html(response.text)
            response_status = response.status_code

            if self.expanded_response:
                if response_status == 404:
                    self.get_url_patterns()
                    
                    if self.vmnf_handler['debug']: 
                        self.djmimic()
                elif response_status == 500:
                    self.dxt_parser(self.expanded_response, False, True)
        
        print()
        print(self.xlp_tbl_x)
        
        return self.expanded_patterns
    
    def parse_args(self):
        ''' ~ siddhi needs only shared arguments from VimanaSharedArgs() ~'''
        parser = argparse.ArgumentParser(
                add_help=False,
                parents=[VimanaSharedArgs().args()]
        )
        return parser

    def issues_presentation(self):
        # create instance of dmt reporter
        result = resultParser(
            self.xlp_tbl_x,
            self.mu_patterns,
            self.fuzz_result,
            **self.vmnf_handler
        )
        # call reporter
        result.show_issues()

    def start(self):

        _scope_   = {}
        target_list = []
        port_list   = []
        invalid_targets = []
        port_step = ''

        dmt_handler= argparse.Namespace(
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
        dmt_handler.args = options.parse_known_args(
            namespace=dmt_handler)[1]
        
        if not self.vmnf_handler['scope']:
            print(VimanaSharedArgs().shared_help.__doc__)
            sys.exit(1)

        # here we just need to get a list of valid scope
        targets_ports_set = get_tool_scope(**self.vmnf_handler)
        self.tps = targets_ports_set

        ports = []
        for p in targets_ports_set:
            ports.append(p.split(':')[1].strip())

        self.last_step  = False
        self.debug      = dmt_handler.debug
        self.exp_mode = False
        start = True 
        last_step = False
        server_flag_found = False
        request_fail = 0

        for entry in targets_ports_set:
            ''' have to change this to auto choose the right scheme'''
            self.target = 'http://' + entry
            port   = entry.split(':')[1].strip()
        
            dmt_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c_target = colored(self.target,'green')
            cprint("[{0}] Starting DMT against {1}...".format(datetime.now(),c_target), 'cyan')
            sleep(1)

            xvals = ['_','.','','^','~','-']
            fakefile = "/{}{}".format(
                random.choice(xvals), 
                self.random_value(random.choice(range(1,6)))
            )
            base_r = self.target
            payload_ = base_r + fakefile  

            self.vmnf_handler['target_url'] = payload_
            response = createSession(**self.vmnf_handler)
            
            if response is None:
                # because with target --port will be just one port, doesnt need such control like request_fail
                
                if not self.vmnf_handler['single_port']:
                    # control request fails to improve consistence of module
                    request_fail += 1
                    if request_fail > 3:
                        request_fail = 0	
                        print("\nHi, sadhu! Too many fails in this process, try to discovery host before!")
                
                cprint('''[{}] DMT did not receive a valid response from the target, nothing to do.
                '''.format(datetime.now()), 'red', attrs=[])
               
                # to continue testing other ports
                if (len(targets_ports_set) > 1):
                    continue
                else:
                    break
           
            current_response = self.get_unescape_html(response.text)
            response_status = response.status_code
            found_exception_flag = True if 'Exception Type' \
                in current_response else False

            if start or not server_flag_found:
                '''just to check if there is any known django/python keyword in response headers'''

                start = False
                # just a test to blackbox fingerprint...
                flags = [
		    'Python','WSGIServer', 'CPython', 
                    'Django', 'CherryPy', 'gunicorn', 
                    'Flask','web2py', 'mod_wsgi', 'APACHE'
                ]
                   
                for header in response.headers:
                    for flag in flags:
                        flag = flag.lower()
                        try:	
                            value = (response.headers[header])
                        except KeyError:
                            continue 
                        
                        if flag in header.lower() or flag in value.lower():
                            server_flag_found = True
                            header = str('   → ' + header + ":    ")
                            print("\n")
                            self.print_it(header, value)

            self.expanded_response  = current_response
            self.dmt_start_request  = current_response
            self.dmt_start_base_r   = base_r
            self.dmt_start_port     = port 
            self.dmt_start_last_step= last_step

            if response_status == 400:
                if found_exception_flag:
                    self.handle_discovery_xt()
                else:
                    print('''\n[dmt: {}]: The target does not appear to be vulnerable.
                            \rMake sure that the analysis settings are correct:\n'''.format(
                        datetime.now()
                        )
                    )
                    for set_k, set_v in (self.vmnf_handler.items()):
                        if set_k != 'scope' and set_v:
                            print('{}{}:\t{}'.format(
                                (' ' * int(5-len(set_k) + 10)),set_k,
                                colored(set_v, 'blue')
                                )
                            )
                    sys.exit(1)
            
            if response_status == 404:
                # Check if last step 
                if (targets_ports_set.index(entry) + 1) == (len(targets_ports_set)):
                    last_step = True 
                      
                if self.debug_is_true():
                    '''status is 404 and DEBUG is True so run another tests'''

                    # Basic DMT actions
                    self.get_url_patterns()
                    self.expand_UP()
                    self.check_api_auth_points()
                    self.check_django_adm()
                    
                    # extending DMT: Call DJunch fuzzer and create instances of object result
                    # this result, a list of dictionaries (2) will be used to resultParser 
                    self.fuzz_result = Djunch(
                        base_r, self.expanded_patterns,
                        **self.vmnf_handler).start()
                    
                    # Parse siddhis results
                    ''' ~ [ DMT result parser ] ~ 
                    
                        Consolidates the results of the DMT and the modules invoked by it 
                        for the presentation of a final report in the terminal.
                        
                        Basically DMT will consolidate the results of the tests 
                        themselves and the following siddhis:

                        * Djonga:     Brute force utility
                        * Djunch:     Django application fuzzer
                        * TicTrac:    Django security ticket tracker
                        * Prana:      Django CVE search utility 
                             
                        In this first version, DMT integrates with a limited number 
                        of other modules, but as other modules for Django appear, 
                        its functionality can be integrated with DMT to extend the 
                        available resources.

                    '''
                    # create instance of dmt reporter
                    self.issues_presentation()
                    break  # removing this break the dmt will continue testing target in other ports
                else:
                    cprint('\n[{}] => Nothing to do: {}'.format(datetime.now(),entry), 'cyan')
                    if last_step:
                        cprint('[{}] => the target does not appear to be vulnerable: {}'.format(
                            datetime.now(),entry), 'cyan')
            
            elif response_status == 500:
                '''This control will serve to define assertive points in the fuzzer stage, 
                since it is making an exception during the discovery phase.'''
                if not found_exception_flag:
                    continue
                self.handle_discovery_xt()                
            elif response_status == 503: 
                continue
            elif response_status == 200: 
                pass
    
    def handle_discovery_xt(self):
        status = False
        while not status:
            signal = colored('█', 'red',attrs=['bold', 'blink'])
            s_msg = colored('''DMT identified an exception during the discovery phase,
                        \r  Would you like to forward it for analysis? (Y/n) > ''','cyan')

            status = input(colored('\n{} {}'.format(signal, s_msg)))
            if status.lower() == 'y':
                dmt_trigger = {
                    'html': self.dmt_start_request,
                    'rtxc_mode': False,
                    'trigger_start': True,
                    'context_filter': False
                }

                patterns=[]
                self.vmnf_handler['verbose'] = True
                self.vmnf_handler['debug'] = True

                # in this case call just Djunch.parser method (because its not fuzzer step yet)
                self.fuzz_result = Djunch(
                    self.dmt_start_base_r, patterns,
                    **self.vmnf_handler).dxt_parser(**dmt_trigger)

                # create instance of dmt reporter and show analysis report
                ipress = self.issues_presentation()

                return ipress
            
            return False

