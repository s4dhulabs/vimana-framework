

from __future__ import unicode_literals
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit import PromptSession
from pygments.lexers.sql import SqlLexer
from pygments.lexers import PythonLexer
from prompt_toolkit.styles import Style
from termcolor import colored, cprint
from prettytable import PrettyTable
from time import sleep
import textwrap
import getpass
import sys
import os
import re

from settings.siddhis_shared_settings import django_envvars as djev
from resources.vmnf_text_utils import text_wrap
from siddhis.tictrac import tictrac
from siddhis.prana import prana



class vmnfshell:
    def __init__(
        self,
        siddhi,
        djunch_result,
        security_tickets,
        _cves_,
        **report_tables
        ):

        self.siddhi = siddhi
        self._fuzz_ = djunch_result
        self.contexts = self._fuzz_[0]
        self._issues_ = self._fuzz_[1]
        self.report_items = report_tables
        self.security_tickets = security_tickets
        self.cves = _cves_[0]

        # general supported options in this alpha version
        vmnf_commands= [
            'abduct',
            'inspect', 
            'show', 
            'exit', 
            'options',
            '?',
            'help'
        ]

        # to invoke help 
        help_cmds = ['?', 'options', 'help']

        cmdcompleter = WordCompleter(
            vmnf_commands, 
            ignore_case=True
        )
        
        p_style = Style.from_dict({
            '':         '#92bfaa',
            'username': '#884444',
            'at':       '#1dff96',
            'colon':    '#1d86ff',
            'pound':    '#1d86ff',
            'host':     '#ff4b03',
            'path':     'ansicyan underline',
        })
        
        prompt = ()
        session = PromptSession(
            lexer=PygmentsLexer(PythonLexer), 
            completer=cmdcompleter, 
            complete_in_thread=True,
            auto_suggest=AutoSuggestFromHistory(),
            complete_while_typing=True,
            style=p_style
        )
        message = [
            ('class:username', getpass.getuser()),
            ('class:at',       '@'),
            ('class:host',     'vimana'),
            ('class:colon',    ':'),
            ('class:path',     '{}'.format(self.siddhi)),
            ('class:pound',    ' ⠶ '),
        ]

        found_ticket = False
        found_exception = False
        found_config_issue = False
        secmid_tbl = False

        self.issue_categories = {
            'ST': "Security Tickets",
            'CV': "CVE ID's",
            'UX': "Exceptions",
            'CI': "Configuration Issues",
            'LC': "EnvLeak Contexts",
            'UP': "URL Patterns",
            'SM': "Security Middleware"
        }

        # show cmd options 
        valid_show_options = {
            0:'summary',
            1:'exceptions',
            2:'tickets',
            3:'cves',
            4:'contexts',
            5:'patterns',
            6:'config'
        }


        # ==[ UX - EXCEPTIONS ]==
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
            "white",
            attrs=['bold']
        )


        while True:
            try:
                r_cmd = session.prompt(message)
                cmd_len = len(r_cmd.split())
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            else:
                # help,options,?

                if cmd_len == 1:
                    if r_cmd == 'exit':
                        cprint('↓ Exiting Vimana...','blue')
                        sleep(1)
                        sys.exit(0)

                    elif r_cmd == 'show':
                        print('''\nMissing issue category argument. Supported options:
                        
                        \r  0:  summary      shows issues summary
                        \r  1:  exceptions   shows identified exceptions
                        \r  2:  tickets      shows security tickets
                        \r  3:  cves         shows related cve ids
                        \r  4:  contexts     shows env leak contexts
                        \r  5:  patterns     shows mapped url patterns
                        \r  6:  config       shows configuration issues

                        ''')
                    elif r_cmd == 'inspect':
                        print('''[{}:inspect] Missing issue id (iid)'''.format(
                            self.siddhi
                            )
                        )
                    else:
                        self.vmnf_mng_cmds()
                    
                    continue

                # command, argument: inspect ST901819 / show exceptions
                elif cmd_len == 2:
                    cmd,arg = r_cmd.lower().split()     # cmd, arg
                    cmd = cmd.rstrip()
                    arg = arg.rstrip()
                    arg_len = len(str(arg))

                    if cmd not in vmnf_commands:
                        print('[vmnfpshell] Invalid command, use options')
                        continue
                    
                    ############
                    # ~ show ~ #
                    ############ 
                    # (exceptions, tickets, config issues, url patterns, etc, all tables available)
                    elif cmd == 'show':
                        # to handler issue category by id 
                        if arg_len == 1:
                            vsol = len(valid_show_options)

                            try:
                                cat_id = int(arg)
                            except ValueError:
                                print('[{}:show] Invalid type. Category id must be an one digit number between 0 and {}.'.format(
                                    self.siddhi,
                                    vsol
                                    )
                                )
                                continue
                                
                            if cat_id in range(vsol):
                                # get the right category value by id 
                                arg = str(valid_show_options[cat_id]).rstrip()
                            else:
                                print('[{}:show] Invalid issue category id. Id should be between 0 and {}'.format(
                                        self.siddhi,
                                        vsol
                                    )
                                )
                                continue
                        
                        # if a valid show option
                        if arg not in valid_show_options.values():
                            opt = colored("show ?", 'green')
                            print('[{}:show] Invalid argument: {}. Use {} for more information.'.format(
                                    self.siddhi,
                                    arg,
                                    opt
                                )
                            )

                            continue

                        elif arg == 'summary':
                            cprint('\n→ Issues summary', 'cyan')
                            print(self.report_items['summary'])
                        elif arg == 'exceptions':
                            cprint('\n→ Triggered unhandled exceptions', 'cyan')
                            print(self.report_items['exceptions'])
                        elif arg == 'tickets':
                            cprint('\n→ Security tickets (by framework version)', 'cyan')
                            print(self.report_items['tickets'])
                        elif arg == 'config':
                            cprint('\n→ Configuration issues', 'cyan')
                            print(self.report_items['configuration'])
                        elif arg == 'contexts':
                            cprint('\n→ ENV leak contexts', 'cyan')
                            print(self.report_items['contexts'])
                        elif arg == 'patterns':
                            cprint('\n→ Mapped URL patterns', 'cyan')
                            print(self.report_items['patterns'])
                        elif arg == 'cves':
                            cprint("\n→ CVE ID's (by framework version)", 'cyan')
                            print(self.report_items['cves'])

                        continue

                    
                    elif cmd == 'abduct':
                        print('''
                        \rThis command will analyze the different information obtained by all the siddhis 
                        \rexecuted during the target assessment to try to infer exploitable scenarios. 
                        
                        \tNot available in this version yet [:.
                        ''')
                        continue

                    ###############
                    # ~ inspect ~ # 
                    ###############

                    # inspect iid (issue id)
                    elif cmd == 'inspect':
                        self._reason_ = False
                        _iid_ = r_cmd.split()[1].strip()
                        #_iid_ = arg                    # raw cmd arg
                        _type_ = _iid_[:2].strip()      # type identifier
                        _issue_ = _iid_[2:].strip()     # issue id without type identifier ST/UX/CI/LC
                        self._type_ = _type_            # for handler

                        # to handle inspect iid 'without' number identifier
                        if not _issue_:
                            self._reason_ = 'Invalid iid format'
                            self.handle_inspect_msg()

                            continue 
                        
                        if _type_ not in self.issue_categories.keys():
                            self._type_ = 'corresponding'
                            self._reason_ = 'Invalid issue identifier'
                            self.handle_inspect_msg()

                            continue

                        # inspect security tickets
                        if _type_ == 'ST':
                            # if a choosen iid in current tickets pool
                            if _issue_ in str(self.security_tickets):
                                for ticket in self.security_tickets:
                                    if ticket['id'] == _issue_: 
                                        found_ticket = True
                                        print('Retrieving results for issue {}...\n'.format(ticket['id']))
                                        sleep(1)
                                        
                                        cprint(ticket['title'], 'cyan')
                                        print()

                                        # get ticket details
                                        tictrac.siddhi(_issue_).start()
                            else:  
                                self._reason_ = 'Ticket not found'
                                self.handle_inspect_msg()
                                
                                continue

                        # inspect unhandled exceptions
                        elif _type_ == 'UX':
                            # traceback related flags
                            trace_flags = [
                                'triggers', 
                                'traceback', 
                                'source_snippet'
                            ]

                            # if a choosen exception in exceptions pool
                            if _iid_ in str(self._issues_['exceptions']):
                                for exception in self._issues_['exceptions']:
                                    # show exception details
                                    if exception['iid'] == _iid_:
                                        found_exception = True
                                        print()

                                        # basica exception information
                                        for k,v in exception.items():
                                            if k not in trace_flags:
                                                print('→ {}: {}'.format(
                                                    colored(k,'cyan'),v
                                                    )
                                                )
                                        print()
    
                                        # traceback items only except source code in this time
                                        for x_entry in exception['traceback']:
                                            for k,v in x_entry.items():
                                                if k not in trace_flags:
                                                    print('→ {}: {}'.format(
                                                        colored(k,'cyan'),v
                                                        )
                                                    )
                                            print()
                                            
                                            # input(colored('█', 'green',attrs=['bold', 'blink']))
                                            sleep(0.10)

                                            # show only source code snipets...
                                            for line in x_entry['source_snippet']:
                                                print(line)
                                                sleep(0.10)
                                            print()

                                continue
                            else:
                                self._reason_ = 'Exception not found'
                                self.handle_inspect_msg()
                                
                                continue
                        
                        # inspect leaked [env] contexts 
                        elif _type_ == 'LC':
                            lc_not_found = True
                            i_count = 1

                            for env_ctx in self.contexts:
                                # inspect LC
                                # ValueError: invalid literal for int() with base 10: ''
                 
                                if i_count == int(_issue_):
                                    lc_not_found = False
                                    context = colored(env_ctx, 'cyan', attrs=['bold'])
                                    cprint('\n Django environment variables in {} context\n'.format(context),'cyan')

                                    i_count = 1
                                    if env_ctx == 'security_middleware':
                                        if not secmid_tbl:
                                            secmid_tbl = True
                                            for ENV,VALUE in self.contexts[env_ctx].items():
                                                if VALUE == 'False' or 'None' or '0' or "[]":
                                                    STATUS = colored('✕', 'red', attrs=['bold'])
                                                else:
                                                    STATUS = colored('✓', 'green', attrs=['bold'])

                                                self.sec_midd_tbl.add_row(
                                                    [
                                                        'SM{}'.format(i_count),
                                                        ENV,
                                                        VALUE,
                                                        STATUS
                                                    ]
                                                )
                                                
                                                i_count +=1
                                            
                                        print(self.sec_midd_tbl)

                                        continue


                                    for k,v in self.contexts[env_ctx].items():
                                        print('→ {}: {}'.format(k,v))
                                    print()
                                    break
                                i_count +=1

                            if lc_not_found:
                                self._reason_ = 'Context not found'
                                self.handle_inspect_msg()

                                continue
                        
                        elif _type_ == 'SM': 
                            if not secmid_tbl:
                                print('[{}:inspect] You need to inspect the security middleware context before inspecting an SM issue.'.format(
                                    self.siddhi
                                    )
                                )
                                continue

                            if _issue_ == '*':
                                for ENV,VALUE in self.contexts['security_middleware'].items():
                                    print()
                                    cprint(' ⠦ ' + str(ENV), 'blue', attrs=['bold'])
                                    print(djev().SECURITY_MIDDLEWARE.get(ENV))
                                    print()

                                continue
                            else:
                                i_count = 1
                                for ENV,VALUE in self.contexts['security_middleware'].items():

                                    if i_count == int(_issue_):
                                        print()
                                        cprint(' ⠦ ' + str(ENV), 'blue', attrs=['bold'])
                                        print(djev().SECURITY_MIDDLEWARE.get(ENV))
                                        print()
                                    i_count +=1

                                continue

                        # inspect a given related cve id / using CVE keyword as identifier of issue CV
                        elif _type_ == 'CV':

                            #self.itype = 'CVE Id'
                            if not (re.search('(CVE-\d{4}-\d{4})',_iid_)):
                                self._reason_ = 'Invalid CVE Id'
                                self.handle_inspect_msg()
                                
                                continue

                            if _iid_ not in str(self.cves):
                                self._reason_ = 'Unrelated CVE Id'
                                self.handle_inspect_msg()

                                continue

                            print('Retrieving details for CVE ID {}...\n'.format(_iid_))   
                            
                            # False = querying for cve id not framework version
                            # _iid_ is full argument because cve doesnt need another identifier 
                            cve_details = prana.siddhi(False).get_cve_details(_iid_)
                            
                            # os.system('clear')
                            for cve in self.cves:
                                if cve['id'].rstrip() == _iid_:
                    
                                    # if cve details, so show a new set of info
                                    if cve_details:
                                        #print()
                                        print(cve['c_date'])
                                        print(cve['c_title'])

                                        cprint('\nDescription: \n\n', 'cyan')
                                        description = text_wrap(cve_details['description'], 70)
                                        for line in description.split('\n'):
                                            print(' {}'.format(line))

                                        cprint('\nHyperlinks: \n', 'cyan')
                                        
                                        for hl in cve_details['hyperlinks']:
                                            print(' {}'.format(hl))

                                        print(' {}'.format(cve['full_description']))
                                        print(' {}'.format(cve['references']))
                                        print()

                                        break
                                    
                                    # else not print default cve info text
                                    print('\n{}'.format(cve['text']))
                                    print('\nFull description:\n{}'.format(cve['full_description']))
                                    print('\nReferences:\n{}\n'.format(cve['references']))
                            
                            continue 


                        # inspect configuration issues
                        elif _type_ == 'CI':
                            # if a choosen exception in exceptions pool
                            if _iid_ in str(self._issues_['configuration']):
                                for c_issue in self._issues_['configuration']:
                                    # show exception details
                                    if c_issue['iid'] == _iid_:
                                        found_issue = True
                                        print()

                                        # basica exception information
                                        for k,v in c_issue.items():
                                            print('→ {}: {}'.format(colored(k,'cyan'),v))
                                        print()
                            else:
                                self._reason_ = 'Configuration issue not found'
                                self.handle_inspect_msg()

                            continue
                    

    def handle_inspect_msg(self):
        '''handle inspect messages'''

        print('[{}:{}] {}. Make sure that the issue id (iid) is correct in the "{}" table.'.format(
            self.siddhi,
            self._type_.lower(),
            self._reason_,
            self.issue_categories[self._type_]
            )
        )

        return False

    def vmnf_mng_cmds(self):
        '''management commands'''

        print('''\nBasic commands for interacting with the analysis result

        \r  abduct      evaluates exploitable scenarios (not available yet)
        \r  inspect     inspects a given issue id (iid)
        \r  show        shows analysis items by category
        \r  options     this help
        \r  exit        exits framework
        ''')

