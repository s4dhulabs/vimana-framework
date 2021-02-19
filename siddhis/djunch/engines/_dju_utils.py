# DJunch utils 

from time import sleep
from urllib.parse import urlparse, urljoin
from settings.siddhis_shared_settings import django_envvars as djev
from . exceptions._items import FuzzURLsPool
from resources.vmnf_fuzz_data import VMNFPayloads
from termcolor import colored, cprint
from resources.colors import *
from itertools import chain

from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from termcolor import colored,cprint
from pygments import highlight

from prettytable import PrettyTable



class DJUtils:
    def __init__(self, raw_traceback, items):
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
    
    def get_scope(self, target, patterns, payloads):
        self._FuzzURLsPool_ = FuzzURLsPool()
        self._vmnfp_ = payloads
        self.target = target

        status = colored('building scope from', 'green')
        hl_pattern = colored('{} patterns'.format(len(patterns)), 'white')
        print('\n{} Starting DJunch | {} {}'.format(
            (Gn_c  + "⠿" + C_c),
            status,
            hl_pattern
            )
        )
        sleep(1)

        self.full_scope = []
        self.raw_urls = []
        self.unicode_urls = []
        self.int_type_urls = []
        self.float_type_urls = []
        self.os_random_type_urls = []
        self.sec_random_type_urls = []

        if patterns is not None:
            self.raw_urls = [urljoin(self.target, pattern) \
                for pattern in patterns \
                    if patterns is not None
            ]

            self.raw_urls.insert(0,self.target)
            count = 1
            for url in self.raw_urls[1:]:
                url_path = urlparse(url).path
                for url_p in (url_path.split('/')):
                    if not url_p:
                        continue

                    self.unicode_urls.append(
                        urljoin(self.target,url_path.replace(url_p, str(self._vmnfp_.get_random_unicode()))
                        )
                    )
                    self.int_type_urls.append(url.replace(url_p, str(self._vmnfp_.get_random_int())))
                    #self.float_type_urls.append(url.replace(url_p, str(self._vmnfp_.get_random_float())))
                    self.os_random_type_urls.append(url.replace(url_p, str(self._vmnfp_.get_os_urandom())))
                    #self.sec_random_type_urls.append(url.replace(url_p, str(self._vmnfp_.get_secure_random_string())))
                    count +=1

        self.full_scope = list(
            chain(
                self.raw_urls,
                self.unicode_urls,
                self.int_type_urls,
                self.float_type_urls,
                self.os_random_type_urls,
                self.sec_random_type_urls
            )
        )

        # These segmentations and scope types will be worked on in future versions of engine
        self._FuzzURLsPool_ = {
            #'FUZZ_HEADERS': self.raw_urls,
            #'RAW_URLS': self.raw_urls,
            #'UNICODE_URLS': self.unicode_urls,
            #'INT_TYPE_URLS': self.int_type_urls,
            #'FLOAT_TYPE_URLS': self.float_type_urls,
            #'OS_RANDOM_TYPE_URLS': self.os_random_type_urls,
            #'SEC_RANDOM_TYPE_URLS':self.sec_random_type_urls,
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


    def show_exception(self, **exception):

        request_headers = exception['REQUEST_HEADERS']
        environment = exception['ENVIRONMENT']
        summary = exception['EXCEPTION_SUMMARY']
        traceback = exception['EXCEPTION_TRACEBACK']
        environment = exception['ENVIRONMENT']
        traceback_objects = exception['OBJECTS']
        #module_args = exception_items['EXCEPTION_TRACEBACK']
        

        print()
        print('\n      {}'.format(colored('    REQUEST   ', 'red', 'on_white', attrs=['bold'])))
        print()
        for k,v in (request_headers.items()):
            k = k.decode()
            v = v[0].decode()
            print('{}{}:\t   {}'.format((' ' * int(5-len(k) + 14)),k,colored(v, 'green')))
        print()
        sleep(1)

        print('\n      {}'.format(colored('    SERVER    ', 'red', 'on_white', attrs=['bold'])))
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
            if isinstance(value, (list)):
                print('{}{}:'.format((' ' * int(5-len(key) + 14)),key))
                for v in value:
                    cprint('\t\t\t   {}'.format(v),'green')
                print()
                continue

            if key == 'Exception Type':
                hl_color = 'magenta'

            print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,colored(value, hl_color)))

        sleep(1)

        if exception.get('EXCEPTION_REASON') is not None:
            print('{}{}:\t   {}'.format(
                (' ' * int(5-len('Exception reason') + 14)),
                ' Exception reason',colored(exception['EXCEPTION_REASON'], 'green')
                )
            )
 

        print()
        sleep(1)
        
        print('\n   {}'.format(colored('    TRACEBACK    ', 'white', 'on_red', attrs=['bold'])))
        print()
        
        mark = colored(' ⠶ ', 'green', attrs=['bold'])
        print()
        for entry in traceback:
            print('   {} {}'.format(mark, colored('Trigger point', 'cyan')))
            print()
            for key,value in entry['MODULE_TRIGGERS'].items():
                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )
            print('\n\n')

            for line in entry['HL_CODE_SNIPPET']:
                print(line)


            print('\n\n')
            print('   {} {}'.format(mark,colored('Local variables', 'cyan')))
            print()
            
            for key,value in entry['MODULE_ARGS'].items():
                print('{}{}:\t   {}'.format((' ' * int(5-len(key) + 14)),key,
                    highlight(value,PythonLexer(),TerminalFormatter()).strip()
                    )
                )

            print("=" * 100)
            print()

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

