# DJunch utils 

from settings.siddhis_shared_settings import django_envvars as djev
from pygments.formatters import TerminalFormatter
from . exceptions._items import FuzzURLsPool
from res.vmnf_fuzz_data import VMNFPayloads
from urllib.parse import urlparse, urljoin
import settings.vmnf_settings as settings
from pygments.lexers import PythonLexer
from neotermcolor import colored, cprint
from neotermcolor import colored,cprint
from core.load_settings import _utils_ 
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
import re

from res.regex.secrets import secrets as secrets_regex
from siddhis.prana import prana



class DJUtils:
    def __init__(self, raw_traceback=False, items=False):
        self.vfp = VMNFPayloads(**{'patterns':1})
        self.traceback = raw_traceback
        self.items = items
        self.fuzz_handler = {
            'module_run': 'djunch',
        }

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

    def get_wrmail(self):

        return (    
            Generic('fr').person.surname()[:3]\
            + Generic('fr').person.title()\
            + Generic('fr').person.name()\
            + Generic('fr').person.email()
        )

    def set_form_fuzz(self, **base_form):
       
        fuzz_all = {}
        fuzz_scope = {
            'nullf':[],
            'rawin':[],
            'allin':[],
            'useri':[],
            'iauth':[],
            'payfv':[],
            'ptpay':[],
            'sstip_values':[],
            'sstip_headers':[],
            'sstip_all':[],
            'authfuzz':[]
        }

        base_form = base_form
        vfp = VMNFPayloads(**{'patterns':1})
        ssti_payloads   = vfp.get_ssti_payloads()
        xss_payloads    = vfp.get_xss_payloads()
        sqli_payloads   = vfp.get_sqli_payloads()

        all_payloads = list(
            set(
                chain(
                    ssti_payloads,
                    xss_payloads,
                    sqli_payloads,
                )

            )
        )    
        
        # fuzz with empty form / step 0
        fuzz_scope['nullf'].append({})
        fuzz_scope['rawin'].append(base_form)

        # fuzz all inputs / step 2
        for field, value in base_form.items():
            fuzz_scope['sstip_headers'].append({field:"{{ messages.storages.0.signer.key }}"})
            fuzz_scope['sstip_values'].append({"{{ messages.storages.0.signer.key }}": value})
            fuzz_scope['sstip_all'].append({"{% debug %}":"{{ messages.storages.0.signer.key }}"})

            fuzz_scope['allin'].append({field: choice(all_payloads)})
            fuzz_scope['ptpay'].append({field:"%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd"})
            
            # fuzz usercontrolled inputs [no actions] / step 3
            if field not in ['next', 'submit','csrfmiddlewaretoken']:
                fuzz_scope['useri'].append({choice(all_payloads): choice(all_payloads)})
                fuzz_scope['payfv'].append({choice(all_payloads): choice(all_payloads)})
            
            # fuzz auth endpoints - with valid values / invalid creds
            if field in ['username', 'user', 'usuário', 'usuario']:
                creds = vfp.get_random_credential()

                fuzz_scope['iauth'].append({field: creds.get('username')})
                fuzz_scope['authfuzz'].append({field:"{{ messages.storages.0.signer.key}}"})
                fuzz_scope['authfuzz'].append({"{% debug %}":creds.get('username')})

            elif field in ['password', 'senha', 'secret', 'passwd']:
                fuzz_scope['iauth'].append({field: creds.get('password')})
                fuzz_scope['authfuzz'].append({field:"{{ messages.storages.0.signer.key }}"})
                fuzz_scope['authfuzz'].append({"{{ messages.storages.0.signer.key }}":creds.get('password')})

            elif field in ['email', 'user_email', 'emailaddress', 'mail']:
                fuzz_scope['iauth'].append({field: self.get_wrmail()}) 

                fuzz_scope['authfuzz'].append({"{% debug %}":"{{ messages.storages.0.signer.key }}@{% debug %}"})
                fuzz_scope['authfuzz'].append({field:"{{ messages.storages.0.signer.key }}@{% debug %}"})
                fuzz_scope['authfuzz'].append({"{{ messages.storages.0.signer.key }}":self.get_wrmail()})


        return fuzz_scope

    def get_random_headers(self):
        with open(_utils_['random_headers']) as f:
            return yaml.load(f,Loader=yaml.FullLoader)

    def get_scope(self, target, payloads, **handler):
        self._FuzzURLsPool_ = FuzzURLsPool()
        self._vmnfp_ = payloads
        patterns = handler.get('patterns')
        regex_patterns = handler.get('fuzz_regex_flags',False)
        sample_mode = handler.get('sample') 

        _xscope_ = True if sample_mode \
            and handler.get('xscope') \
            or handler.get('extended-scope')\
            else False

        self.target = 'http://' + target \
            if not target.startswith('http') else target
         
        status = colored('building scope from', 'green')
        hl_pattern = colored('{} patterns'.format(len(patterns)), 'white')
        
        if not handler.get('sample'):
            print()
            print(f"\n{Gn_c  + '⠿' + C_c} Starting DJunch | {status} {hl_pattern}")
            sleep(0.40)

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
        self.random_pyvars_payloads=[]
        
        if patterns is not None:
            self.target_zero = self.target 

            # build scope from clean patterns
            self.raw_urls = [urljoin(self.target, pattern) \
                for pattern in patterns \
                    if patterns is not None
            ]

            if not self.target_zero.endswith('/'):
                self.target_zero = self.target_zero + '/'

            self.raw_urls.insert(0,self.target)
            self.raw_urls.insert(1,self.target_zero)
           
            random_types = self.get_random_data_list()

            # we're not gonna need attack payloads in sample mode
            # but xscope forces it extending scope during sample mode
            # --sample --xscope/--extended-scope || sample_mode == False

            if _xscope_ or not sample_mode:
                ssti_payloads = self._vmnfp_.get_ssti_payloads()
                xss_payloads = self._vmnfp_.get_xss_payloads()
                sqli_payloads = self._vmnfp_.get_sqli_payloads()
                pyvars_payloads = self._vmnfp_.get_pyvars()
            
            common_params= [
                'add','cmd','alterar','account',
                'consultar','remove','delete', 
                'config','edit','set','change',
                'update', 'download','settings'
            ]
            
            pathtr_vals = [ 
                'etc/passwd',
                'db.sqlite3',
                '*.sqlite3',
                'urls.py',
                'models.py',
                'settings.py',
                '__init__.py',
                '.gitignore',
                '__pycache__',
                'settings.yaml',
                'etc/shadow',
                '../app/../urls.py'
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
                    self.sec_random_type_urls.append(
                        url.replace(url_p, str(self._vmnfp_.get_secure_random_string()))
                    )

                    # because --sample its an optmized mode to trigger just one exception
                    # attack payloads like these are more like a redundance from this perspective
                    # they're not intended to really trigger the relative vulnerability, it may happen
                    # but its not the focus here, and its another story. [:'
                    
                    if _xscope_ or not sample_mode:
                        self.random_param_values.append(
                            urljoin(self.target, 
                                str(url_p + '?{}={}'.format(
                                    choice(common_params), 
                                    choice(random_types))
                                )
                            )
                        )
                        self.random_path_traversal.append(
                            urljoin(self.target, 
                                str('/' + url_p + '/' + f'%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/{choice(pathtr_vals)}'))
                        )
                        self.random_xss_payloads.append(
                            url.replace(url_p, str(choice(xss_payloads)))
                        )
                        self.random_ssti_payloads.append(
                            urljoin(self.target,url_path.replace(url_p, str(choice(ssti_payloads)))
                            )
                        )
                        self.random_ssti_payloads.append(
                            urljoin(self.target,url_path.replace(url_p, "{% include 'admin/base.html' %}")
                            )
                        )
                        self.random_sqli_payloads.append(
                            urljoin(self.target,url_path.replace(url_p, str(choice(sqli_payloads)))
                            )
                        )
                        self.random_pyvars_payloads.append(
                            urljoin(self.target,url_path.replace(url_p, '{{' + str(choice(pyvars_payloads)) + '}}')
                            )
                        )

                    count +=1
        
        # altough the main idea here is to set contextual fuzzer according to regex (oposite)
        # at this time we're just playing a little bit with this to enrich fuzzer scope
        if regex_patterns and not sample_mode:
            for view,rgx_patterns in regex_patterns.items():
                hl_view = colored(view,'red') 
                rgx_msg = ('   |- Building scope from fuzz_regex_patterns / view: {} ({} patterns)...'.format(
                    hl_view,len(rgx_patterns)
                    )
                )
                print(rgx_msg.ljust(os.get_terminal_size().columns - 1), end="\r")
                sleep(0.02)

                for pattern in rgx_patterns:
                    self.regex_patterns_payloads.extend(
                        [
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',str(choice(range(9000))))),
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',Generic().text.word())),
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',str(Generic().numbers.float_number()))),
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',"""${{<%[%'"}}%\.""")),
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',"{% csrf_token %}")),
                            urljoin(self.target, pattern.replace('{{fuzz_flag}}',"{% include 'admin/base.html' %}"))
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
                set(self.regex_patterns_payloads),
                set(self.random_pyvars_payloads)
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
            'RANDOM_PYVARS_PAYLOAD': self.random_pyvars_payloads,
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

    def generate_exceptions_table(self, EXCEPTIONS):
        exceptions_tbl = self.get_report_tables().get('exceptions')
        #exceptions_tbl = tables['exceptions']

        i_count = 1
        # >> load exceptions into table
        env_pool = []
        count_lines = False
        count_vars  = False
        count_triggers = False
        total_xocc = False

        for exception in EXCEPTIONS:
            x_traceback = exception['EXCEPTION_TRACEBACK']
            env_count = len(exception['ENVIRONMENT'])
            occ_count = exception['EXCEPTION_COUNT']

            env_pool.append(env_count)
            total_xocc = total_xocc + occ_count

            x_summary = exception['EXCEPTION_SUMMARY']
            x_loc_items = x_summary['Exception Location'].split()
            x_line_number = x_loc_items[x_loc_items.index('line') + 1]
            x_function = x_loc_items[x_loc_items.index('in') + 1]
            x_location = '/'+'/'.join(x_loc_items[0].split('/')[-3:]).replace(',','').strip()
            x_function = x_function.replace(',','').strip()
            x_line_number = x_line_number.replace(',','').strip()
 
            installed_items = exception['INSTALLED_ITEMS']

            lines_count = 0
            triggers_count = 0
            vars_count = 0

            for item in x_traceback:
                lines_count = lines_count + len(item['RAW_CODE_SNIPPET'])
                triggers_count = triggers_count + len(item['MODULE_TRIGGERS'])
                vars_count = vars_count + len(item['MODULE_ARGS'])

            count_lines = count_lines + lines_count
            count_vars  = count_vars + vars_count
            count_triggers = count_triggers + triggers_count

            exceptions_tbl.add_row(
                [
                    colored(exception['IID'], 'green'),
                    exception['EXCEPTION_TYPE'],
                    x_function,
                    x_location,
                    x_line_number,
                    lines_count,
                    triggers_count,
                    env_count,
                    vars_count,
                    occ_count
                ]
            )
            i_count +=1

        return {
            'exceptions_tbl': exceptions_tbl,
            'total_xocc': total_xocc,
            'env_pool': env_pool,
            'count_lines':count_lines,
            'count_vars':count_vars,
            'count_triggers':count_triggers
     
        }

    def get_tickets_table(self, django_version, tickets=False):

        tickets_tbl = self.get_report_tables().get('tickets')

        if not tickets:

            from siddhis.tictrac import tictrac

            self.fuzz_handler['django_version'] = django_version
            self.tickets = tictrac.siddhi(**self.fuzz_handler).get_ticket_ids()

        else:
            self.tickets = tickets

        if self.tickets and self.tickets is not None:
            
            tickets_tbl.title = colored(
                f"Security tickets for Django {django_version}",
                "white", attrs=['bold']
            )

            for ticket in self.tickets:
                title = ticket['title']

                if len(title) > 100:
                    title = str(title[:100]) + '...'

                tickets_tbl.add_row(
                    [
                        colored(f"ST{ticket['id']}",'green'),
                        title
                    ]
                )

            return tickets_tbl

        return False

    def get_version_issues(self,**sample):
        
        #tickets_tbl = self.get_report_tables().get('tickets')
        cves_tbl = self.get_report_tables().get('cves')
        tickets = None
        cves = None

        sttinger_data = sample.get('fingerprint',False)

        if sample['EXCEPTION_SUMMARY'].get('Django Version'):
            django_version = sample['EXCEPTION_SUMMARY'].get('Django Version').strip()
            
            installed_items = sample['INSTALLED_ITEMS']
            
            # if Django Versions is found in Djunch 'environment_context'
            if django_version and django_version is not None:

                if len(django_version.split('.')) >= 3:
                    django_version = '.'.join(django_version.split('.')[:-1])

                # if dmt already retrieve sec issues through passive fingerprint
                if sttinger_data\
                    and django_version == sttinger_data.get('flag_version',False):

                    if sttinger_data.get('cves',False):
                        cves = sttinger_data.get('cves')
                    
                    if sttinger_data.get('tickets',False):
                        tickets = sttinger_data.get('tickets')

                    if sttinger_data.get('tickets_tbl'):
                        tickets_tbl = sttinger_data.get('tickets_tbl')
                else:
                    # - Get CVEs and security tickets for abducted framework version-
                    #tickets = tictrac.siddhi(django_version).start()
                    cves = prana.siddhi(**{'django_version':django_version}).get_cves()
                    tickets_tbl = self.get_tickets_table(django_version)

                # CVE table
                if cves and cves is not None:
                    cves_tbl.title = colored(
                        "CVE IDs for Django {}".format(django_version),
                        "white",attrs=['bold']
                    )
                    for entry in cves:
                        cves_tbl.add_row(
                            [
                                colored(entry['id'],'green'),
                                entry['title'].rstrip(),
                                entry['date'].rstrip()

                            ]
                        )
                else: 
                    pass

        return {
            'tickets_tbl': tickets_tbl.get_string(),
            'cves_tbl': cves_tbl.get_string(),
            'tickets': self.tickets,
            'cves':cves
        }

    def show_scan_settings(self,**vmnf_handler):
        print("\033c", end="")
        vmnf_banners.audit_report_banner('DMT')

        ### Abudct analysis ###
        cprint("\n⣆⣇      Scan settings                          \n", "white", "on_red", attrs=['bold'])
        cprint("\tGeneral settings and siddhis called during analysis.\n",
                'cyan', attrs=[]
        )

        hl_color = 'green'
        sg = colored('→', hl_color, attrs=['bold'])

        pass_flags = ['patterns_table', 'patterns_views', 'fuzz_settings',
            'meta','download_timeout','method','headers','cookie']

        for _abd_k, _abd_v in (vmnf_handler.items()):
            if _abd_v and _abd_k not in pass_flags:
                if isinstance(_abd_v,(list,dict)):
                    _abd_v = len(_abd_v)

                print('{}{}:\t   {}'.format(
                    (' ' * int(5-len(_abd_k) + 15)),
                    _abd_k,
                    colored(_abd_v, hl_color)
                    )
                )
        print()
        sleep(1)
    
    def show_server_env(self,contexts):
        cprint("\n⣠⣾      Target Environment              ", "white", "on_red", attrs=['bold'])
        print()
        cprint("\tDetails about target application environment.\n",
                'cyan', attrs=[]
        )

        for k,v in contexts['server'].items():
            k = (k.replace('_',' ')).capitalize()
            print('{}{}:\t   {}'.format(
                (' ' * int(5-len(k) + 15)),
                k,colored(v, 'green'))
            )
            sleep(0.10)

        try:
            contexts['environment']['EXCEPTION_REPORTER'] = \
                contexts['environment'].pop('DEFAULT_EXCEPTION_REPORTER_FILTER')
        except KeyError:
            contexts['environment']['EXCEPTION_REPORTER'] = '?'

        try:
            contexts['environment']['DJANGO_SETTINGS'] = \
                contexts['environment'].pop('DJANGO_SETTINGS_MODULE')\
                if 'DJANGO_SETTINGS_MODULE' in contexts['environment'] \
                    else contexts['environment'].pop('SETTINGS_MODULE')
        except KeyError:
            contexts['environment']['DJANGO_SETTINGS'] = '?'

        for k,v in contexts['environment'].items():
            k = (k.replace('_',' ')).capitalize()

            print('{}{}:\t   {}'.format(
                (' ' * int(5-len(k) + 15)),
                k,colored(v, 'green'))
            )
            sleep(0.10)

        print()
        sleep(0.20)
        
        return contexts

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

    def keyword_match(self): 
        
        for keyword in self.kw_collection:

            if not keyword:
                continue
            if [kv for kv \
                    in self.match_key_vals \
                    if keyword in kv]:
            #if keyword in self.match_key_vals: 
                self.match = True
                return keyword
        
        return False

    def secret_scan(self,exception_response):
        
        for re_type, regex in secrets_regex.items():
            print(f"    + Scanning for {colored(re_type,11,988)}...")
            sleep(0.01)

            rgx_check = re.search(regex,exception_response)

            if rgx_check:
                print(f"              {colored(rgx_check.group(),'red')}")

    def extract_metadata(self,extract_type,*except_objs):
        
        if extract_type in ['ss', 'secret_scan']:
            self.secret_scan(except_objs[0]['APP_RESPONSE'])
            return True

        collections = VMNFPayloads(**{'patterns':1})
        self.match = False

        if extract_type in ['qx', 'query_extractor'] \
                or extract_type is None:
            self.kw_collection = collections.get_sqlkw()
        elif extract_type in ['cx','creds_extractor']:
            self.kw_collection = collections.get_credskw()
        
        for module_trigger_info in except_objs:
            for key,value in module_trigger_info['MODULE_ARGS'].items():               
                
                value = value.replace('khan123khan','h@n1287t4db')
                value = value.replace('reactcrud.cwi8neqkn8vo.us-east-1.rds.amazonaws.com','cruddjref.tuym2.us-east-1.rds.amazonaws.com')
                value = value.replace('crud_django','cruddjref')

                self.match_key_vals = [
                    key,
                    value,
                    key.lower(),
                    value.lower()
                ]
                
                if not self.keyword_match():
                    continue
                
                for mti_key, mti_value in module_trigger_info['MODULE_TRIGGERS'].items():
                    print('{}{}:\t   {}'.format((' ' + ' ' * int(5-len(key) + 14)),
                        colored(mti_key, 'blue', attrs=['bold']),
                        highlight(mti_value,PythonLexer(),TerminalFormatter()).strip()
                        )
                    )

                print()

                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),
                    colored(key, 'magenta'),
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )
                sleep(0.05)

                print('-'*100)
                sleep(0.10)

        if not self.match:
            cprint('\t + Nothing to extract here!', 44, 841)
            sleep(0.20)

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

        x_count = issues_count.get('total_exceptions')
        c_count = len(_issues_.get('CONFIGURATION'))

        t_x = (R_c + x_count + g_c)
        u_x = (R_c + str(len(_issues_.get('EXCEPTIONS')))  + g_c)
        t_l = (R_c + issues_count.get('total_lines') + g_c)
        t_v = (R_c + issues_count.get('total_vars')  + g_c)
        t_e = (R_c + issues_count.get('total_env')   + g_c)
        t_c = (R_c + str(len(_issues_.get('CONFIGURATION')))  + g_c)
        f_v = (Y_c + 'CSRF_FAILURE_VIEW' + g_c)

        print("\033c", end="")
        vmnf_banners.audit_report_banner('issues references')

        print(f"""{g_c}
        \r Vimana has identified {t_x} exception occurrences related to {u_x} unique
        \r exception types.
        """)

        print(report_items['exceptions'])

        print(f'''{g_c}
        \r    This unhandled exceptions issue led to the exposure
        \r    of {t_l} lines of source code, {t_v} application
        \r    variables, and also server environment with {t_e}
        \r    variables.
        ''')
        
        if c_count > 0:
            print(f'''{g_c}
            \r    In addition was identified {t_c} occurrences of
            \r    {f_v}, which doesn't depend on DEBUG enabled and
            \r    leads to information leakage that could allow the
            \r    identification of technologies and versions.

            \r    These issues are related to the following CWE IDs,
            \r    described in detail below:{D_c}
            ''')

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
            
                sleep(0.05)
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
        print(f"\n      {colored('    REQUEST   ', 'white', 'on_red', attrs=['bold'])}")
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
        line_pause = 0.03 if total_triggers > 3 else 0.10
        step_pause  = 0.07 if total_triggers > 3 else 0.20

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
                sleep(line_pause)
            sleep(step_pause)

            print('\n\n')
            print('   {} {}'.format(mark,colored('Local variables', 'cyan')))
            print()
            
            for key,value in entry['MODULE_ARGS'].items():
                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )

            print("-" * 100)

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

