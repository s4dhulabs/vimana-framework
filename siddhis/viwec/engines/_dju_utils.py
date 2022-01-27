# DJunch utils 

from settings.siddhis_shared_settings import django_envvars as djev
from pygments.formatters import TerminalFormatter
from . exceptions._items import FuzzURLsPool
from res.vmnf_fuzz_data import VMNFPayloads
from urllib.parse import urlparse, urljoin
import settings.vmnf_settings as settings
from pygments.lexers import PythonLexer
from neotermcolor import colored, cprint
from prettytable import PrettyTable
from pygments import highlight
from res import vmnf_banners
from mimesis import Generic
from itertools import chain
from random import choice
from res.colors import *
from time import sleep
import yaml
import os



class DJUtils:
    def __init__(self, raw_traceback=False, items=False):
        self.traceback = raw_traceback
        self.items = items

    def parse_raw_tb(self):
        p_t = self.traceback

        env_traceback_dict  = {}
        apps_traceback_list = []
        mids_traceback_list = []

        pb_traceback_env    = self.strip_blank_entries(
            p_t[p_t.find('Environment:'):p_t.find('Installed Applications:')]
        )
        pb_traceback_apps   = self.strip_blank_entries(
            p_t[p_t.find('Installed Applications:'):p_t.find('Installed Middleware:')]
        )
        pb_traceback_mids   = self.strip_blank_entries(
            p_t[p_t.find('Installed Middleware:'):p_t.find('Traceback:')]
        )

        for line in pb_traceback_env:
            k,v = line.split(": ")
            env_traceback_dict[k] = v

        for app in pb_traceback_apps:
            app = self.clean_entry(app)
            apps_traceback_list.append(app)

        for mid in pb_traceback_mids:
            mid = self.clean_entry(mid)
            mids_traceback_list.append(mid)

        installed_items = {
            'Environment': env_traceback_dict,
            'Installed Applications': apps_traceback_list,
            'Installed Middlewares': mids_traceback_list
        }

        return installed_items

    def strip_blank_entries(self,_tcb_):
        return [line for line in _tcb_.split('\n') if line.strip()][1:]

    def clean_entry(self,item):
        return item.replace("['",'').replace("']",'').replace("'",'').replace(",",'').strip()

    def parse_db_settings(self):
        db_settings = {}
        k_list = []

        if not self.items.get('DATABASES'):
            print('[djunch.db_parser] Database settings not found')
            #self.RAWP_TRACEBACK['Databases'] = False
            return False
        
        for entry in (self.items['DATABASES'][0]).split('\n')[1:]:
            entry = str(entry).rstrip().strip().replace('}','').replace('{','').replace(',','').split(':')
            k = entry[0]
            v = entry[1]
            if k.rstrip().strip() == 'TEST':
                dbt_dict = {}
                t = str(self.items['DATABASES']).strip().rstrip()
                t = t[t.find('TEST: ') + 7:]
                db_test_values = (t[:t.find('}')]).split('\n')
                for i in db_test_values:
                    i = i.rstrip().strip().replace(',','')
                    tk,tv = i.split(':')
                    dbt_dict[tk.strip()]=tv.strip()
                v=dbt_dict

            if k not in k_list:
                k_list.append(k)
                db_settings[k]=v

        return db_settings
    
    def parse_contexts(self,**environment):
        ''' dummy trick to save exception data in right context and feed traceback object'''
        
        env_contexts = {
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
        
        for env, value in environment.items():
            if env in djev().SECURITY_MIDDLEWARE.keys():
                env_contexts['security_middleware'][env] = value
            elif env in djev().SERVER_:
                env_contexts['server'][env] = value
            elif env in djev().ENVIRONMENT_:
                env_contexts['environment'][env] = value
            elif env in djev().EXCEPTIONS_:
                env_contexts['exception'][env] = value
            elif env in djev().SESSION_:
                env_contexts['session'][env] = value
            elif env in djev().AUTHENTICATION_:
                env_contexts['authentication'][env] = value
            elif env in djev().CREDENTIALS_:
                env_contexts['credential'][env] = value
            elif env in djev().CSRF_:
                env_contexts['csrf'][env] = value
            elif env in djev().EMAIL_:
                env_contexts['email'][env] = value
            elif env in djev().FILE_UPLOAD_:
                env_contexts['upload'][env] = value
            elif env in djev().COMMUNICATION_:
                env_contexts['communication'][env] = value
            elif env in djev().SERVICES_:
                env_contexts['services'][env] = value

        return env_contexts
   
    def get_random_data_list(self):
        g = Generic()
        return [
            g.person.password(),
            g.person.locale,
            g.person.username(),
            g.person.title(),
            g.person.blood_type(),
            g.person.age(),
            g.person.height(),
            g.hardware.resolution(),
            g.hardware.cpu_frequency(),
            g.business.cryptocurrency_symbol(),
            g.food.vegetable()
        ]

    def get_scope(self, target, payloads, **handler):
        self._FuzzURLsPool_ = FuzzURLsPool()
        self._vmnfp_ = payloads
        patterns = handler.get('patterns')
        regex_patterns = handler.get('fuzz_regex_flags',False)

        self.target = 'http://' + target \
            if not target.startswith('http') else target
         
        status = colored('building scope from', 'green')
        hl_pattern = colored('{} patterns'.format(len(patterns)), 'white')
        
        print('\n{} Starting DJunch | {} {}'.format(
            (Gn_c  + "⠿" + C_c),
            status,
            hl_pattern
            )
        )
        sleep(1)

        self.full_scope=[]
        self.raw_urls=[]
        self.unicode_urls=[]
        self.int_type_urls=[]
        self.float_type_urls=[]
        self.random_xss_payloads=[]
        self.random_param_values=[]
        self.sec_random_type_urls=[]
        self.random_path_traversal=[]
        self.random_ssti_payloads=[]
        self.random_sqli_payloads=[]
        self.regex_patterns_payloads=[]
        
        if patterns is not None:
            # build scope from clean patterns
            self.raw_urls = [urljoin(self.target, pattern) \
                for pattern in patterns \
                    if patterns is not None
            ]

            self.raw_urls.insert(0,self.target)
           
            random_types = self.get_random_data_list()
            ssti_payloads= self._vmnfp_.get_ssti_payloads()
            xss_payloads= self._vmnfp_.get_xss_payloads()
            sqli_payloads= self._vmnfp_.get_sqli_payloads()
            
            common_params= [
                'add','cmd','alterar',
                'consultar','remove','delete', 
                'config','edit','set','change'
            ]

            
            count = 1
            # build scope from initial raw patterns (dmt input)
            for url in self.raw_urls[1:]:
                url_path = urlparse(url).path
                for url_p in (url_path.split('/')):
                    if not url_p:
                        continue

                    self.unicode_urls.append(
                        urljoin(self.target,url_path.replace(url_p, str(self._vmnfp_.get_random_unicode()))
                        )
                    )
                    self.int_type_urls.append(
                        url.replace(url_p, str(self._vmnfp_.get_random_int()))
                    )
                    self.float_type_urls.append(
                        url.replace(url_p, str(self._vmnfp_.get_random_float()))
                    )
                    self.random_xss_payloads.append(
                        url.replace(url_p, str(choice(xss_payloads)))
                    )
                    self.sec_random_type_urls.append(
                        url.replace(url_p, str(self._vmnfp_.get_secure_random_string()))
                    )
                    self.random_path_traversal.append(
                        urljoin(self.target, 
                            str('/' + url_p + '/' + '%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd'))
                    )
                    self.random_param_values.append(
                        urljoin(self.target, 
                            str(url_p + '?{}={}'.format(
                                choice(common_params), 
                                choice(random_types))
                            )
                        )
                    )
                    self.random_ssti_payloads.append(
                        urljoin(self.target,url_path.replace(url_p, str(choice(ssti_payloads)))
                        )
                    )
                    self.random_sqli_payloads.append(
                        urljoin(self.target,url_path.replace(url_p, str(choice(sqli_payloads)))
                        )
                    )

                    count +=1
        
        # altough the main idea here is to set contextual fuzzer according to regex (oposite)
        # at this time we're just playing a little bit with this to enrich fuzzer scope
        if regex_patterns:
            for view,rgx_patterns in regex_patterns.items():
                hl_view = colored(view,'red') 
                rgx_msg = ('   |- Building scope from fuzz_regex_patterns / view: {} ({} patterns)...'.format(
                    hl_view,len(rgx_patterns)
                    )
                )
                print(rgx_msg.ljust(os.get_terminal_size().columns - 1), end="\r")
                sleep(0.10)

                for pattern in rgx_patterns:
                    self.regex_patterns_payloads.extend(
                        [
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',str(choice(range(9000))))),
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',Generic().text.word())),
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',str(Generic().numbers.float_number())))
                        ]
                    )

        self.full_scope = list(
            chain(
                set(self.raw_urls),
                set(self.unicode_urls),
                set(self.int_type_urls),
                set(self.float_type_urls),
                set(self.random_xss_payloads),
                set(self.sec_random_type_urls),
                set(self.random_path_traversal),
                set(self.random_param_values),
                set(self.random_ssti_payloads),
                set(self.random_sqli_payloads),
                set(self.regex_patterns_payloads)
            )
        )

        # These segmentations and scope types will be used to set fuzzer mode in future versions
        self._FuzzURLsPool_ = {
            'FUZZ_HEADERS': self.raw_urls,
            'RAW_URLS': self.raw_urls,
            'UNICODE_URLS': self.unicode_urls,
            'INT_TYPE_URLS': self.int_type_urls,
            'FLOAT_TYPE_URLS': self.float_type_urls,
            'RANDOM_XSS_PAYLOADS': self.random_xss_payloads,
            'SEC_RANDOM_TYPE_URLS':self.sec_random_type_urls,
            'RANDOM_PATH_TRAVERSAL':self.random_path_traversal,
            'RANDOM_PARAM_VALUES':self.random_param_values,
            'RANDOM_SSTI_PAYLOADS':self.random_ssti_payloads,
            'RANDOM_SQLI_PAYLOADS':self.random_sqli_payloads,
            'REGEX_PATTERNS_URLS': self.regex_patterns_payloads,
            'FULL_SCOPE':self.full_scope
        }
        
        return self._FuzzURLsPool_
    
    def get_pretty_table(self, **config):
        
        tbl_title = config.get('title') 
        title_color = config.get('color')
        attrs = config.get('attrs')
        fields = config.get('fields')
        title_position = config.get("align")

        _tbl_ = PrettyTable()
        _tbl_.field_names = fields
        _tbl_.align = title_position
        _tbl_.title = colored(
            tbl_title,
            title_color,
            attrs=attrs
        )

        return _tbl_

    def get_report_tables(self):
        from . _dju_settings import table_models
        
        return {
            'exceptions': self.get_pretty_table(**table_models().exception_tbl_set),
            'configuration': self.get_pretty_table(**table_models().config_tbl_set),
            'summary': self.get_pretty_table(**table_models().summary_tbl_set),
            'tickets': self.get_pretty_table(**table_models().tickets_tbl_set),
            'envleak': self.get_pretty_table(**table_models().envleak_tbl_set),
            'cves': self.get_pretty_table(**table_models().cves_tbl_set),
            'objects': self.get_pretty_table(**table_models().traceback_tbl_set)
        }

    def show_module_args(self,*except_objs):
        for module_trigger_info in except_objs:
            for key, value in module_trigger_info['MODULE_TRIGGERS'].items():
                print('{}{}:\t   {}'.format((' ' + ' ' * int(5-len(key) + 14)),
                    colored(key, 'blue', attrs=['bold']),
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )

            print()
            for key,value in module_trigger_info['MODULE_ARGS'].items():
                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),
                    colored(key, 'magenta'),
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )
                sleep(0.05)

            print('-'*100)
            sleep(0.10)

    def consolidate_issues(self, _issues_, report_items):
        issues_count = _issues_.get('_count_issues_')

        t_x = (R_c + issues_count.get('total_exceptions') + g_c)
        u_x = (R_c + str(len(_issues_.get('EXCEPTIONS')))  + g_c)
        t_l = (R_c + issues_count.get('total_lines') + g_c)
        t_v = (R_c + issues_count.get('total_vars')  + g_c)
        t_e = (R_c + issues_count.get('total_env')   + g_c)
        t_c = (R_c + str(len(_issues_.get('CONFIGURATION')))  + g_c)
        f_v = (Y_c + 'CSRF_FAILURE_VIEW' + g_c)

        print("\033c", end="")
        vmnf_banners.audit_report_banner('issues references')

        print('''{}
        \r   Were identified {} exception occurrences related to {} unique
        \r   exception types.
        \r'''.format(g_c,t_x,u_x))
        
        print(report_items['exceptions'])

        print('''{}
        \r   This unhandled exceptions issue led to exposure of {} lines of
        \r   source code, {} application variables, and also server environment
        \r   with {} variables.

        \r   In addition was identified {} occurrences of {},
        \r   which doesn't depend on DEBUG enabled, and led to information leakage
        \r   that could allow identification of technologies and versions.

        \r   These issues are related to the following CWE IDs, described in
        \r   detail below:{}
        '''.format(g_c,t_l,t_v,t_e,t_c,f_v,D_c))

        self.get_cwe_references(mode='full')

    def get_cwe_references(self, quiet=False, mode='brief'):
        # load related cwe references: exceptions/configuration issues

        with open(settings.issues_ref) as f:
            issues_ref = yaml.load(f, Loader=yaml.FullLoader)

        if quiet:
            return issues_ref

        if mode == 'brief':
            for ref in issues_ref.get('_issues__'):
                print(' {}: {}'.format(
                    colored(ref['id'],'white'),
                    colored(ref['title'], 'blue')
                    )
                )
            
                sleep(0.10)
            return 
        
        # full details
        for item in issues_ref.get('_issues__'):
            print('\n   {} {}: {}\n'.format(
                colored('+', 'red', attrs=['bold']), 
                colored(item['id'],'white', attrs=['bold']),
                colored(item['title'], 'cyan', attrs=['bold'])
                )
            )
            
            for line in item['desc'].split('\n'):
                cprint("     \x1B[3m{}\x1B[0m".format(line), 'white')

            if item['x_desc']:
                for line in item['x_desc'].split('\n'):
                    cprint('     ' + line, 'blue')

            cprint('     ' + item['ref'], 'blue', attrs=['bold'])

            if item['rel']:
                cprint('\n     related vulnerabilities:', 'cyan')

                for link in item['rel']:
                    print('\t + {}'.format(link))        
            
            print()
            sleep(0.20)
    
    def show_exception(self, **exception):

        request_headers = exception['REQUEST_HEADERS']
        environment = exception['ENVIRONMENT']
        summary = exception['EXCEPTION_SUMMARY']
        hl_x_type = colored(summary.get('Exception Type'), 'red', attrs=['bold'])
        traceback = exception['EXCEPTION_TRACEBACK']
        environment = exception['ENVIRONMENT']
        traceback_objects = exception['OBJECTS']

        print()
        print('\n      {}'.format(colored('    REQUEST   ', 'white', 'on_red', attrs=['bold'])))
        print()
        for k,v in (request_headers.items()):
            k = k.decode()
            v = v[0].decode()
            print('{}{}:\t   {}'.format((' ' * int(5-len(k) + 14)),k,colored(v, 'green')))
        print()
        sleep(1)

        print('\n      {}'.format(colored('    SERVER    ', 'white', 'on_red', attrs=['bold'])))
        print()
        for key,value in environment.items():
            if key.strip() in djev().SERVER_:
                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,colored(value, 'green')))

        print()
        sleep(1)
        print('\n     {}'.format(colored('    SUMMARY    ', 'white', 'on_red', attrs=['bold'])))
        print()

        values = []
        for key, value in summary.items():
            hl_color = 'green'
            attr=[]
            if isinstance(value, (list)):
                print('{}{}:'.format((' ' * int(5-len(key) + 14)),key))
                for v in value:
                    cprint('\t\t\t   {}'.format(v),'green')
                print()
                continue

            if key == 'Exception Type':
                hl_color = 'red'
                attr=['bold']

            print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,colored(value, hl_color,attrs=attr)))

        sleep(1)

        if exception.get('EXCEPTION_REASON') is not None:
            print('{}{}:\t   {}'.format(
                (' ' * int(5-len('Exception reason') + 14)),
                ' Exception reason',colored(exception['EXCEPTION_REASON'], 'green')
                )
            )
        print()
        sleep(0.30)
        
        print('\n   {}'.format(colored('    TRACEBACK    ', 'white', 'on_red', attrs=['bold'])))
        print()
        
        mark = colored(' ⠶ ', 'green', attrs=['bold'])
        #print()

        tp_count = 0
        total_triggers = len(traceback)
        for entry in traceback:
            tp_count +=1
            hl_tpc = colored(tp_count, 'white', attrs=['bold'])

            print('   {} {}'.format(
                mark, colored('Trigger Point {}/{}: {}'.format(
                    hl_tpc,
                    total_triggers,
                    hl_x_type), 'cyan')
                )
            )
             
            print()
            for key,value in entry['MODULE_TRIGGERS'].items():
                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )
            print('\n')

            for line in entry['HL_CODE_SNIPPET']:
                print(line)
                sleep(0.10)
            sleep(0.20)

            print('\n\n')
            print('   {} {}'.format(mark,colored('Local variables', 'cyan')))
            print()
            
            for key,value in entry['MODULE_ARGS'].items():
                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )

            print("-" * 100)
            #print()

        #print('\n\n')
        print('   {} {}'.format(mark,colored('Traceback Objects', 'cyan')))
        print()
        for tb_object in traceback_objects:
            for k,v in tb_object.items():
                print('{}{}:\t   {}'.format((' ' * int(5-len(k) + 14)),
                    k,highlight(v,PythonLexer(),TerminalFormatter()).strip()
                    )
                )
            print('\t' + '-' * 80)

        print()
        sleep(1)

        print('\n\t{}'.format(colored('    ENVIRONMENT    ', 'white', 'on_red', attrs=['bold'])))
        print()
        for key,value in environment.items():
            if isinstance(value, (list)):
                for v in value:
                    cprint('\t\t\t   {}'.format(v),'green')
                print()
                print()
                continue

            print('{}{}:\t      {}'.format((' ' * int(5-len(key) + 22)),key,colored(value, 'green')))
        print()

