""" [[[V1M4N4FR4M3W0RK]]]   """


from __future__ import unicode_literals

from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from core._dbops_.models.siddhis import Siddhis as VFSD
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from neotermcolor import cprint, colored as cl
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit import PromptSession
from pygments.lexers.sql import SqlLexer
from pygments.lexers import PythonLexer
from prompt_toolkit.styles import Style
from prettytable import PrettyTable
from time import sleep
from res.colors import *
import itertools
import textwrap
import getpass
import sys
import os
import re


class describe:
    def __init__(self, **handler:dict):
        self.handler = handler

    def siddhi(self, siddhi:VFSD):
        print("\033c", end="")
        print()

        print(f"""
        {cl('Name','blue'):>20} {siddhi.name:>3}
        {cl('Author','blue'):>20} {siddhi.author:>3}
        {cl('Info','blue'):>20} {siddhi.info:>3}
        {cl('Category','blue'):>20} {siddhi.category:>3}
        {cl('Framework','blue'):>20} {siddhi.framework:>3}
        {cl('Package','blue'):>20} {siddhi.package:>3}
        {cl('Type','blue'):>20} {siddhi.type:>3}
        {cl('Tags','blue'):>20} {','.join(siddhi.tags):>3}""")

        if siddhi.references.get('cwe'):
            print(f"""{cl('CWE', 'blue'):>28} {','.join([c.split(' - ')[0].split('-')[1]
                    for c in siddhi.references.get('cwe')]):>3}""")
        print()
        for i in siddhi.description.split('\n'):
            print(f"\t\t{cl(i,'cyan')}")

        print(f"{cl('References', 'blue'):>28}")

        if siddhi.references['links']:
            for link in siddhi.references['links']:
                print(f"\t\t{cl(link,'cyan')}")
            print()

class pshell_set:
    def __init__(self, **handler):
        self.handler = handler

        self.vmnf_commands = [
            'abduct',
            'inspect', 
            'show', 
            'search',
            'exit', 
            'options',
            'run',
            '?',
            'help'
        ]

        self.siddhi =handler.get('module_run')

        # to invoke help 
        self.help_cmds = ['?', 'options', 'help']

        self.cmdcompleter = WordCompleter(
            self.vmnf_commands, 
            ignore_case=True
        )
        
        self.p_style = Style.from_dict({
            '':         '#92bfaa',
            'username': '#884444',
            'at':       '#1dff96',
            'colon':    '#1d86ff',
            'pound':    '#1d86ff',
            'host':     '#ff4b03',
            'path':     'ansicyan underline',
        })
        
        #prompt = ()
        self.session = PromptSession(
            lexer=PygmentsLexer(PythonLexer), 
            completer=self.cmdcompleter, 
            complete_in_thread=True,
            auto_suggest=AutoSuggestFromHistory(),
            complete_while_typing=True,
            style=self.p_style
        )
        self.message = [
            ('class:username', getpass.getuser()),
            ('class:at',       '@'),
            ('class:host',     'vimana'),
            ('class:colon',    ':'),
            ('class:path',     '{}'.format(self.siddhi)),
            ('class:pound',    ' ⠶ '),
        ]

        self.issue_categories = {
            'ST': "Security Tickets",
            'CV': "CVE ID's",
            'UX': "Exceptions",
            'CI': "Configuration Issues",
            'LC': "EnvLeak Contexts",
            'UP': "URL Patterns",
            'SM': "Security Middleware",
            '??': "Issues"
        }

        # show cmd options 
        self.valid_show_options = {
            0:'summary      |show issues summary',
            1:'exceptions   |show identified exceptions',
            2:'tickets      |show security tickets',
            3:'cves         |show related cve ids',
            4:'contexts     |show env leak contexts',
            5:'patterns     |show mapped url patterns',
            6:'config       |show configuration issues',
            7:'applications |show installed applications',
            8:'middlewares  |show installed middlewares',
            9:'databases    |show available databases',
            10:'objects     |show traceback objects',
            11:'variables   |show leaked app variables',
            12:'log         |show fuzzer logs',
            13:'references  |show related cwe entries'
        }

        self.valid_run_utils = {
            'wc|web_crawler': 'run crawler plugin against the pre-collected scope (dmt)',
            'qx|query_extractor': 'run extractor utility looking for SQL metadata on exception leaks',
            'cx|creds_extractor': 'run extractor utility looking for credentials on exception leaks',
            'ss|secret_scan': 'run scan utility looking for secret patterns on metadata',
            'bf|brute_force': 'run bruteforce plugin against Django admin portal',
            'it|issues_tracker': 'run issues tracker plugins against framework version'
        }

        self.sec_midd_tbl = PrettyTable()
        self.sec_midd_tbl.field_names = [
            'iid',
            'resource',
            'value',
            'status'
        ]

        self.sec_midd_tbl.align = "l"
        self.sec_midd_tbl.title = cl(
            "~ django.middleware.security.SecurityMiddleware ~",
            "white",attrs=['bold']
        )

    def valid_run_option(self,arg):
        if arg not in (
            list(itertools.chain(*[p.split('|') \
                for p in self.valid_run_utils.keys()]))):
            
            cprint('\n[run] → Utilities:\n','cyan')
        
            for k,v in self.valid_run_utils.items():
                print('{:>25} {:>10}   {}'.format(
                    cl(k.split('|')[1], 'red'),
                    cl(k.split('|')[0], 'green'),
                    cl(v, 44,841)
                    )
                )
            print()
            return False
        return True

    def handle_inspect_msg(self, _type_, _reason_, _category_):
        '''handle inspect messages'''

        print('[{}:{}] {}. Make sure that the issue id (iid) is correct in the "{}" table.'.format(
            self.siddhi,
            _type_.lower(),
            _reason_,
            _category_
            )
        )

        return False

    def vmnf_mng_cmds(self):
        '''management commands'''

        print('''\nBasic commands for interacting with the analysis result:

        \r  abduct      evaluate exploitable scenarios (not available yet)
        \r  inspect     inspect a given issue id (iid)
        \r  run         run plugins against current findings
        \r  show        show analysis items by category
        \r  search      search environment variables by keyword
        \r  options     this help
        \r  exit        exit framework
        ''')

    def handle_show_options(self):
        print("\nMissing issue category argument. Supported options:\n")
        
        for k,v in self.valid_show_options.items():
            cat,desc = v.split('|')

            print('  {:15s}{:25s}{:25s}'.format(
                cl(str(k) + ': ','blue'),
                cl(cat.strip(), 'green'),
                cl("\x1B[3m{}\x1B[0m".format(desc.strip()),'white')
                )
            )
        print()
    
    def list_env_vars(self,arg,cmd, keyenv_contexts):

        print('[{}] Available keywords:\n'.format(cmd))
        evars=[str(key) for key in keyenv_contexts.keys()]
        cprint(str(evars).replace(
            '[','').replace(
            ']','').replace(
            '"','').replace(
            "'",''), 'green')
        print()
        '''
        num_vars = cl(str(len(self.keyenv_contexts.get(arg))), 'white')
        cprint("[{}]→ Found {} variables for keyword \"{}\"\n".format(cmd, num_vars, arg),"cyan")

        for env_match in self.keyenv_contexts.get(arg):
            print('\t+ {}'.format(env_match))
        print()
        '''
