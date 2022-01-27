""" [[[V1M4N4FR4M3W0RK]]]   """


from __future__ import unicode_literals
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
#from siddhis.viwec.viwec import siddhi as crawler
#from siddhis.jungler.jungler import siddhi as bruteforce
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit import PromptSession
from pygments.lexers.sql import SqlLexer
from pygments.lexers import PythonLexer
from prompt_toolkit.styles import Style
from neotermcolor import colored, cprint
from prettytable import PrettyTable
from time import sleep
from res.colors import *
import itertools
import textwrap
import getpass
import sys
import os
import re


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
            'cs|code_scan': 'run the utility against the code snippets of tracebacks (in progress)',
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
        self.sec_midd_tbl.title = colored(
            "~ django.middleware.security.SecurityMiddleware ~",
            "white",attrs=['bold']
        )

    def valid_run_option(self,arg):
        if arg not in (
            list(itertools.chain(*[p.split('|') \
                for p in self.valid_run_utils.keys()]))):
            
            cprint('\n[run] → Supported plugins:\n','cyan')
        
            for k,v in self.valid_run_utils.items():
                print('{:>25} {:>10}   {}'.format(
                    colored(k.split('|')[1], 'red'),
                    colored(k.split('|')[0], 'green'),
                    colored(v, 'blue')
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
                colored(str(k) + ': ','blue'),
                colored(cat.strip(), 'green'),
                colored("\x1B[3m{}\x1B[0m".format(desc.strip()),'white')
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
        num_vars = colored(str(len(self.keyenv_contexts.get(arg))), 'white')
        cprint("[{}]→ Found {} variables for keyword \"{}\"\n".format(cmd, num_vars, arg),"cyan")

        for env_match in self.keyenv_contexts.get(arg):
            print('\t+ {}'.format(env_match))
        print()
        '''
