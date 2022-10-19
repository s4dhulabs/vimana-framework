
import re
import requests
from time import sleep
from res.colors import *
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from neotermcolor import cprint, colored
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import pygments
import collections
from res.colors import *
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter


def flamebann():
        
        print(f'''{Rn_c}
         (     (                *          
         )\ )  )\ )    (      (  `         
        (()/( (()/(    )\     )\))(   (    
         /(_)) /(_))((((_)(  ((_)()\  )\   
        (_))_|(_))   )\ _ )\ (_()((_)((_)  
        | |_  | |    (_)_\(_)|  \/  || __|  Flask 
        | __| | |__   / _ \  | |\/| || _|   Misconfigurations
        |_|   |____| /_/ \_\ |_|  |_||___|  Explorer
        {D_c} 

        ''')
        
def test_target_connection(address):

    print('\n[+] Testing target connection...')
    sleep(1)

    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        conn_response = (
            session.get(
                address,
                verify=False,
                timeout=10
            )
        )
    except ConnectTimeout:
        return False
    except ConnectionError:
        return False

    return conn_response


def get_html_content(response):
    try:
        html = response.content
    except AttributeError:
        return False

    html_content = BeautifulSoup(html, 'lxml')
    page_title = html_content.title.text
    head = get_head(html_content)

    return (
        html_content,
        page_title, 
        head
    )

def get_head(html_content):
    head = {}
    page_head  = (html_content).head.text

    for _hl_ in (page_head.split('\n')[3:]):
        if _hl_:
            _hl_ = (_hl_.strip().replace('var ','').strip('\n'))
            data = _hl_.split('=')

            try:
                head[data[0].strip()] = data[1].replace('"','').strip(";").strip(',').strip()
            except IndexError:
                pass
            
    return head


class ex2tract:
    def __init__(self, **kwargs):
        exception_table = PrettyTable()
        exception_table.field_names = (
            [
                'ID',
                'Exception',
                'Class',
                'Erro message',
                'Traceback paths',
                'Modules',
                'Functions',
                'Lines'
            ]
        )

        exception_table.title = colored("Exceptions", 'yellow', attrs=['bold'])
        exception_table.align = 'l'
        exception_table.align["Traceback paths"] = "c"
        exception_table.align["Modules"] = "c"
        exception_table.align["Functions"] = "c"
        exception_table.align["Lines"] = "c"

        traceback_schema = PrettyTable()
        traceback_schema.field_names = ['ID','Module', 'Type', 'Line', 'Function Call', 'Lines']
        traceback_schema.title = colored("Traceback schema", 'yellow', attrs=['bold'])
        traceback_schema.align = 'l'

        current_module = PrettyTable()
        current_module.field_names = ['Module', 'Line', 'Function Call', 'Lines']
        current_module.title = colored("Traceback Module", 'yellow', attrs=['bold'])
        current_module.align = 'l'

        self.exception_table = exception_table
        self.traceback_schema = traceback_schema
        self.current_module = current_module

        self.args = kwargs

    def get_source(self, html,_mode_=False):

        source_modes = ['traceback', 'frame', 'source']

        if _mode_ in source_modes:
            return(html.find_all('div',{'class':_mode_}))

        return False

    def get_exception_details(self, html):

        return {
            'name'  : (html.find(['h1']).text).strip(),
            'value' : (html.find('p',{'class':'errormsg'}).text).strip()
        }

    def show_exception_details(self, target, **exception_item):

        color = D_c
        x_register = {}
        exception = exception_item['exception']
        frame = exception_item['exception_frame']
        response = exception_item['response']

        python_version = '*'
        python_version_path = False
        python_version_server = False
        modules_cache = []
        paths_cache = []
        py_modules = []
        functions = []

        server = response.headers['Server']
        x_name = exception['name']
        x_value= exception['value']
        exception_name = x_name   
        exception_class = '*'

        if len(server.split()) >= 1:
            target_server = server.split()[0]
        
            if len(server.split()[1:]) >= 1 \
                and 'python' in str(server.split()[1:]).lower():
                python_version_server = server.split()[1]

        if x_name.find('.') != -1:
            try:
                exception_class, exception_name = x_name.split('.')
            except ValueError:
                exception_name  = x_name.split('.')[-1]
                exception_class = x_name[:x_name.find(exception_name)-1]
    
        if x_value.find(':') != -1:
            exception_value = x_value.split(':')[1]
   
        if len(exception_value) > 38:
            exception_value = exception_value[:38] + " [snip]..."

        lines_count = 0
        module_count = 1
        exception_count = 1

        for entry in frame:

            clean_source = entry.find_all('div',{'class':'source'})
            lines = str(len(str(clean_source).split('\n')))
            full_path = (entry.cite.text).strip('"')
            line = (entry.em.text).strip()
            function = (entry.code.text).strip()
            lines_count = lines_count + int(lines)
            py_script = (full_path.split('/')[-1]).strip().strip('\n')
            path = full_path
            path_type = 'lib'
            p_color = Y_c

            if function not in functions:
                functions.append(function)

            if py_script not in py_modules:
                py_modules.append(py_script)
        
            if full_path not in paths_cache:
                paths_cache.append(full_path)

            x_register = {
                'exception_name': exception_name,
                'exception_class': exception_class,
                'module': full_path,
                'line': line,
                'function': function,
                'exception_value': exception_value,
                'lines': lines
            }
    
            debug_mode = True

            # if debug mode
            if debug_mode:
                color = Y_c 

                if modules_cache:
                    self.current_module.clear_rows()

                    for entry in modules_cache: 
                        self.current_module.add_row(
                            [
                                entry['module'], 
                                entry['line'],
                                entry['function'],
                                entry['lines']
                            ]
                        )
                
            # show one entry on traceback
            if not debug_mode:
                self.current_module.clear_rows()

            # current module in traceback
            self.current_module.add_row(
                [
                    str(color + full_path + D_c), 
                    str(color + line      + D_c), 
                    str(color + function  + D_c),
                    str(color + lines     + D_c),
                ]
            )
        
            # get python version [via lib path]
            python_match = re.search('.*[\\|\\\|\/](python\d\.\d).*',full_path)
            if python_match:
                python_version_path = python_match.group(1)

            if not full_path.startswith('/usr/'):
                path_type = 'app' 
                p_color = R_c
        
            if python_version_server:
                python_version = python_version_server
            elif python_version_path:
                python_version = python_version_path
            
            if '/' in python_version: 
                python_version = python_version.split('/')[1]

            self.traceback_schema.add_row(
                [
                    p_color + str(module_count) + D_c,
                    p_color + full_path + D_c,
                    p_color + path_type + D_c,
                    p_color + line + D_c,  
                    p_color + function + D_c, 
                    p_color + lines + D_c
                ]
            )
        
            print("\033c", end="")
            print(self.current_module)
            print()

            modules_cache.append(x_register)

            for line in clean_source:
                code = highlight(
                    line.text,
                    PythonLexer(),
                    TerminalFormatter(),
                )
                print(code.strip('\n'))
                sleep(0.10)
        
            sleep(0.50)

            module_count +=1

        unique_modules = len(py_modules)
        all_paths = len(modules_cache)
        unique_paths = len(paths_cache)    

        # all exceptions identified
        self.exception_table.add_row(
            [
                exception_count,
                exception_name, 
                exception_class, 
                exception_value, 
                all_paths, 
                unique_paths, 
                len(functions), 
                lines_count
            ]
        )
    
        exception_count +=1
        print("\033c", end="")
        print('---------------------------')
        print(f'{C_c}  Target Information {D_c}   ')
        print('---------------------------')
    
        print(f"+ Target: {target}\n+ Server: {target_server}\n+ Python Version: {python_version}")

        print(f"\n{Gn_c}*{C_c} Bellow are the exceptions identified during analysis:{D_c}")
        print(self.exception_table)
        print()
        print(f"\n{Gn_c}*{C_c} Bellow are all paths identified in Flask traceback schema:{D_c}")
        print(self.traceback_schema)
    
        return True

