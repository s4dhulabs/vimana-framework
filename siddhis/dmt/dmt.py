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

from resources.session.vmn_session import createSession
from resources.vmnf_validators import get_tool_scope

from .. djunch.djunch import siddhi as Djunch 
from .. _shared_settings_.__settings import api_auth as APIAuth
from resources import colors

from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from pygments import highlight

import sys, re, os, random, string, platform
from lxml.html.soupparser import fromstring
from termcolor import colored, cprint
from prettytable import PrettyTable
from collections import OrderedDict 
from urllib.parse import urlsplit
from resources.colors import *
from tldextract import extract
from bs4 import BeautifulSoup
from netaddr import IPNetwork
from datetime import datetime
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
        global plugin_information
        global trigger_start 
        
        self.fuzz_mode = False

        datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        fmwk_ = "Django"
        version_ = "1.0"
        
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

    def random_value(self,stringLength=6):
        extensions = ['.txt','.html','.php','.js', '.css']
        ext = str(random.choice(extensions))
        lettersAndDigits = string.ascii_letters + string.digits
        return ''.join(random.choice(lettersAndDigits) for i in range(stringLength)) + ext

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
        '''

        '''
        
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
               self.print_it('   → ROOT_URLCONF:', URLConf)  

               return True

            else:
                if not_debug_status and self.last_step:
                   print("{}-{} Django {}DEBUG{} seems to be disabled".format(
                       Pn_c, D_c, Rn_c, D_c
                       )
                    )
                   return False 	

        #|---> AttributeError: 'NoneType' object has no attribute 'find'  [status,info] 
        except AttributeError:
            if not_debug_status and self.last_step:
               print("{}-{} Django {}DEBUG{} seems to be disabled".format(
                   Pn_c, D_c, Rn_c, D_c
                   )
                ) 
               return False 	
        #|---> TypeError: object of type 'bool' has no len() [soup]
        except TypeError: 
            pass

    def check_api_auth_points(self):
        '''

        '''
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
           
        #self.print_it('\nAPI Auth:', len(APIAuthUrls))
        count = 1
        for path in APIAuthUrls:
            auth_path = self.dmt_start_base_r + '/' + path
            current_request = createSession(auth_path, False, False, True)
            if not current_request:
               pass

            else:
               from resources.session.vmn_session import status, request

               if status == 405:
                  ef = True
                  methods   = str(request.headers['Allow'])
                  methods_c = colored(methods, 'green')
                  status_c  = colored(status, 'yellow')
                  
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
                print("   {0} Django Administration: no-default path...").format(vrf)
                django_adm_path = "/" + found_admin_pattern + rel_path
            else:
                print("   {0} Django Admin path not found").format(fail)
                return False
        else:
            django_adm_path = "/admin" + rel_path
	    #/api/admin/login/?next=/api/admin/
	    #/admin/login
	
        adm_path = (self.dmt_start_base_r + django_adm_path)  	
        #|---> createSession(target_url, random_ua = False, debug = False, d2t_mode = False):
        djadmin_response = createSession(adm_path, False, False, True)
        
        if not djadmin_response:
            print("  {0} Django administration interface seems to be disabled".format(fail))
            return False
        else: 
            from resources.session.vmn_session import status
             
            if status == 200:

                print("   {0} Django administration: seems to be available...".format(ok))
                sleep(0.25)
                print("   {0} Django administration: Checking...".format(ok))
                sleep(0.50)
              
                soup = BeautifulSoup(djadmin_response, 'lxml')
                try:
                    r_check = ''	
                    check = str((soup.find("h1", {"id": "site-name"})).find("a"))
                    adm_pattern = (check[check.find("<a"):check.find("</a>")]).split(">")[1]
                except AttributeError as AE:
                    print("[+] Fail: {}".format(AE))
                    return False
             
                if adm_pattern == "Django administration":
                    print("   {0} Django administration: {1}".format(ok, str(P_c + adm_path + D_c)))
                    sleep(0.50)
                    return True
	      
	        # Django 管理 
                elif (adm_pattern.split()[0]) == fmwk_:
                    print("   {0} Django administration: abducting {1}...".format(ok, adm_pattern.split()[1]))
                    sleep(0.50)
                    print("   {0} Django administration: {1}".format(ok, str(Gn_c + adm_path + D_c)))
                elif (soup.title.string).find('Django') > -1:
                    print("   {0} Django administration: {1}".format(ok, str(Gn_c + adm_path + D_c)))
                else: 
                    return False		

            elif status == 404:
                print('[+] DMTSTATUS {}:{}'.format(len(dadmp_request),status))
            elif status == 500:
                self.dxt_parser(dadmp_request, True)
            else: return False  		      
    
    def get_url_patterns(self):

        login_flags =['login', 'auth', 'logout',' loggedin', 'signup']            
        login_flag_count = 0

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
    
    def djmimic(
        
        self, 
        x_pattern=None, 
        expanded_patterns=None
        ):

        if not expanded_patterns:
            return 

        # Django setting files mimic: urls.py
        # Should be a separated function
        print("\n\n{}/urls.py".format(x_pattern))
        print("app_name= '{0}'\n".format(colored(x_pattern, 'yellow')))
        print('urlpatterns = [')
        for pattern in expanded_patterns:
            if pattern.startswith(x_pattern): 
                url = pattern[pattern.find('/')+1:]
                if len(url) > 0 and url[-1] == '/':
                    url = url[:-1]
                view = url
                name = view
                if len(url) == 0:
                    view = x_pattern
                    name = view
                if url != x_pattern:
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
            self.expanded_response = createSession(expanded_pattern, False, False, True)
    
            if self.expanded_response:
                from resources.session.vmn_session import status
                if status == 404:
                    self.get_url_patterns()
                    
                    if self.vmnf_handler['debug']: # esse handler foi adicionado por conta do parser do urls.py 010420 
                        self.djmimic(x_pattern, self.expanded_patterns)
                elif status == 500:
	            #print "500 during expassion...";raw_input()
                    self.dxt_parser(self.expanded_response, False, True)
        
        #self.print_it(' \nURL Patterns:', xp_count)  
        sleep(1)
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
        
            dmt_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c_target = colored(self.target,'green', attrs=['bold'])
            cprint("[{0}] Starting DMT against {1}...".format(datetime.now(),c_target), 'green')
            sleep(1)

            fakefile = "/_" + (self.random_value(10))
            base_r = self.target
            payload_ = base_r + fakefile  

            #|---> createSession(target_url, random_ua = False, debug = False, d2t_mode = False):
            current_request = createSession(payload_, False, False, True)

            if not current_request:
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

            else: 
                ''' 
                    if there is a response from request could be indicate
                    check it better 

                '''
                from resources.session.vmn_session import status, request
            
            if start or not server_flag_found:
                '''
                    just to check if there is any known django/python keyword
                    in response headers
                '''
                start = False
                # just a test to blackbox fingerprint...
                flags = [
		    'Python','WSGIServer', 'CPython', 
                    'Django', 'CherryPy', 'gunicorn', 
                    'Flask','web2py', 'mod_wsgi', 'APACHE'
                ]
                   
                for header in request.headers:
                    for flag in flags:
                        flag = flag.lower()
                        try:	
                            value = (request.headers[header])
                        except KeyError:
                            continue 
                        
                        if flag in header.lower() or flag in value.lower():
                            server_flag_found = True
                            header = str('   → ' + header + ":    ")
                            print("\n")
                            self.print_it(header, value)
            
            if status == 400:
                print('[dmt: {}]: The target does not appear to be vulnerable. Make sure that the analysis settings are correct:'.format(
                    datetime.now()
                    )
                )

                print(self.target)
                
                sys.exit(1)

            if status == 404:
                # Check if last step 
                if (targets_ports_set.index(entry) + 1) == (len(targets_ports_set)):
                    last_step = True 
                      
                self.expanded_response  = current_request
                self.dmt_start_request  = current_request
                self.dmt_start_base_r   = base_r
                self.dmt_start_port     = entry.split(':')[1].strip()
                self.dmt_start_last_step= last_step

                if self.debug_is_true():
                    '''status is 404 and DEBUG is True so run another tests'''

                    # Basic DMT actions
                    self.get_url_patterns()
                    self.expand_UP()
                    self.check_api_auth_points()
                    self.check_django_adm()
                    
                    # extending DMT: Call DJunch fuzzer and create instances of object result
                    # this result, a list of dictionaries (2) will be used to resultParser 
                    fuzz_result = Djunch(
                        base_r, self.expanded_patterns,**self.vmnf_handler).start()
                    
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
                    result = resultParser(
                        self.xlp_tbl_x, 
                        self.mu_patterns, 
                        fuzz_result,
                        **self.vmnf_handler
                    )
                    
                    # call reporter
                    result.show_issues()
 
                    break  # removing this break the dmt will continue testing target in other ports
                else:
                    cprint('\n[{}] => Nothing to do: {}'.format(datetime.now(),entry), 'cyan')
                    if last_step:
                        cprint('[{}] => the target does not appear to be vulnerable: {}'.format(datetime.now(),entry), 'cyan')
            
            elif status == 500:
                '''This control will serve to define assertive points in the fuzzer stage, 
                since it is making an exception during the discovery phase.'''
                
                # if found some exception during this step
		#self.dxt_parser(current_request, True)
                continue
            elif status == 503: 
                pass
            elif status == 200: 
                pass

