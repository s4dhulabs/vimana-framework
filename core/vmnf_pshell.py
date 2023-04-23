# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.


from __future__ import unicode_literals
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from siddhis.viwec.viwec import siddhi as crawler
from siddhis.jungle.jungle import siddhi as bruteforce
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit import PromptSession
from pygments.lexers.sql import SqlLexer
from pygments.lexers import PythonLexer
from prompt_toolkit.styles import Style
from neotermcolor import colored, cprint
from prettytable import PrettyTable
from res.vmnf_banners import case_header
from res.colors import *
from time import sleep
import itertools
import textwrap
import getpass
import sys
import os
import re

from settings.siddhis_shared_settings import django_envvars as djev
from siddhis.djunch.engines._dju_utils import DJUtils
from core.vmnf_utils import pshell_set 
from scrapy.exceptions import CloseSpider
from res.vmnf_text_utils import text_wrap
from siddhis.tictrac import tictrac
from siddhis.prana import prana



class vmnfshell:
    def __init__(self,**_vmnf_session_):
       
        # general configuration and helpers
        _pset_ = pshell_set(**_vmnf_session_)
        
        # forward session `vimana run --module [module]`
        self._vmnf_session_ = _vmnf_session_

        self.siddhi   = _vmnf_session_.get('module_run')
        self._issues_ = _vmnf_session_.get('djunch_result',False)
        self.sampler  = self._issues_.get('EXCEPTIONS')[0]
        self.fuzz_scope = self.sampler.get('FUZZ_URLS_SCOPE',False)
        self._vmnf_session_['scope'] = self.fuzz_scope.get('RAW_URLS',False)

        self.contexts = self.sampler.get('CONTEXTS',False)
        self.keyenv_contexts = self.sampler.get('KEY_ENV_CONTEXTS',False)
        self.report_items = _vmnf_session_.get('report_tables',False)

        self.security_tickets = _vmnf_session_.get('security_tickets',False)
        self.installed_items = self.sampler.get('INSTALLED_ITEMS',False)
        self.cves = _vmnf_session_.get('_cves_',False)
        
        # instance of settings and helpers
        vmnf_commands = _pset_.vmnf_commands
        self.valid_show_options = _pset_.valid_show_options
        self.handle_show_options = _pset_.handle_show_options
        self.vmnf_mng_cmds = _pset_.vmnf_mng_cmds
        help_cmds = _pset_.help_cmds
        self.list_env_vars = _pset_.list_env_vars
        cmdcompleter = _pset_.cmdcompleter
        session = _pset_.session
        message = _pset_.message
        self.issue_categories = _pset_.issue_categories
        self.valid_run_utils = _pset_.valid_run_utils
        self.sec_midd_tbl = _pset_.sec_midd_tbl
        found_ticket = False
        found_exception = False
        found_config_issue = False
        secmid_tbl = False

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
                    r_cmd = r_cmd.strip()

                    if r_cmd == 'exit':
                        cprint('↓↓↓ Exiting Vimana...','blue')
                        sleep(1)
                        os._exit(os.EX_OK)
                    
                    elif r_cmd == 'run':
                        case_header()
                        _pset_.valid_run_option('?')
                        continue

                    elif r_cmd == 'search':
                        self.list_env_vars(r_cmd, '?', self.keyenv_contexts)
                    elif r_cmd == 'show' or r_cmd == 'show ':
                        self.handle_show_options()
                    elif r_cmd == 'inspect':
                        print('''[{}:inspect] Missing issue id (iid)'''.format(
                            self.siddhi
                            )
                        )
                    elif r_cmd == 'abduct':
                        print('''
                        \rThis command will analyze the different information obtained by all the siddhis
                        \rexecuted during the target assessment to try to infer exploitable scenarios.

                        \tNot available in this version yet [:.
                        ''')
                    else:
                        self.vmnf_mng_cmds()
                    continue

                # command, argument: inspect ST901819 / show exceptions
                elif cmd_len == 2:
                    cmd,arg = r_cmd.lower().split()     # cmd, arg
                    cmd = cmd.rstrip().strip()
                    arg = arg.rstrip()
                    arg_len = len(str(arg))

                    if cmd not in vmnf_commands:
                        print('[vmnfpshell] Invalid command, use options')
                        continue
                
                    ###########
                    # ~ run ~ #
                    ########### 
                    if cmd == 'run':
                        if not _pset_.valid_run_option(arg):
                            continue
                        
                        # set callback signals to siddhi
                        self._vmnf_session_['callback_session'] = True
                     
                        if arg in [
                            'ss',
                            'qx', 
                            'cx',
                            'query_extractor', 
                            'creds_extractor',
                            'secret_scan'
                            ]:

                            extractors = {
                                'qx': 'SQL query patterns',
                                'query_extractor': 'SQL query patterns',
                                'cx': 'Credential patterns',
                                'creds_extractor': 'Credential patterns',
                                'secret_scan': 'Secrets',
                                'ss': 'Secrets'
                            }

                            hl_xtype = colored(extractors[arg],44, 867)

                            for exception in self._issues_.get('EXCEPTIONS'):
                                exception_type = exception['EXCEPTION_SUMMARY'].get('Exception Type')
                                exception_type = colored(exception_type, 'red', attrs=['bold'])
                                   
                                cprint(f"\n➥ Looking for {hl_xtype} on {exception_type} exception metadata...\n")
                                sleep(0.40)
                                
                                DJUtils(False,False).extract_metadata(
                                    arg,*exception['EXCEPTION_TRACEBACK']
                                )

                            print()

                        elif arg in ['wc', 'web_crawler', 'crawler']:
                            self._vmnf_session_['siddhi_run'] = 'viwec'
                            crawler(**self._vmnf_session_).start()
                        
                        elif arg in ['bf', 'brute_force', 'bruteforce']:
                            self._vmnf_session_['siddhi_run'] = 'jungle'
                            bruteforce(**self._vmnf_session_).start()

                        elif arg in ['it', 'issues_tracker', 'itracker']:
                            '''
                                if len(self.report_items['cves']._rows) > 0\
                                AttributeError: 'str' object has no attribute '_rows'

                                somehow ptable change during acquisition
                            '''
                            
                            if self.cves is not None\
                                and self.cves != '?':
                                    
                                cprint('→ Issues already collected. Use show command instead.', 'cyan')
                                continue
                            
                            try:
                                issues_found = DJUtils(False,False).get_version_issues(**self.sampler)
                            except KeyboardInterrupt:
                                continue

                            if not issues_found or issues_found is None:
                                print('>> Was not possible to retrieve issues')
                                continue
                            
                            #print(issues_found.get('cves'))

                            security_tickets = issues_found.get('tickets')
                            cves = issues_found.get('cves')
                            self.tickets_tbl = issues_found.get('tickets_tbl')
                            self.cves_tbl = issues_found.get('cves_tbl')

                            self.report_items['tickets'] = self.tickets_tbl
                            self.report_items['cves'] = self.cves_tbl
                            self.security_tickets = security_tickets
                            self.cves = cves

                            print(self.cves_tbl)
                            print(self.tickets_tbl)

                        continue

                    ##############
                    # ~ search ~ #
                    ############## 
                    elif cmd == 'search':
                        arg = arg.upper().strip("'").strip('"').strip(',')
                        if not arg or arg not in self.keyenv_contexts:
                            self.list_env_vars(cmd,arg,self.keyenv_contexts)
                            continue
            
                        num_vars = colored(str(len(self.keyenv_contexts.get(arg))), 'white')
                        cprint("[{}]→ Found {} variables for keyword \"{}\"\n".format(cmd, num_vars, arg),"cyan")

                        for env_match in self.keyenv_contexts.get(arg):
                            print('\t+ {}'.format(colored(env_match,'green')))
                        print()
                        continue

                    ############
                    # ~ show ~ #
                    ############ 
                    # (exceptions, tickets, config issues, url patterns, etc, all tables available)
                    elif cmd.strip() == 'show':
                        # to handler issue category by id 
                        if arg_len >= 1 and arg_len <=2:
                            vsol = len(self.valid_show_options) - 1

                            if arg == '?' or arg == ' ':
                                self.handle_show_options()
                                continue

                            try:
                                cat_id = int(arg)
                            except ValueError:
                                print('[{}:show] Invalid category type. Id must be an one digit number between 0 and {}.'.format(
                                    self.siddhi,
                                    vsol 
                                    )
                                )
                                continue
                                
                            if cat_id in self.valid_show_options.keys(): 
                                # get the right category value by id 
                                arg = str(self.valid_show_options[cat_id]).split('|')[0].rstrip()
                            else:
                                print('[{}:show] Invalid issue category id. Id should be between 0 and {}'.format(
                                        self.siddhi,
                                        vsol
                                    )
                                )
                                continue
                        
                        # if a valid show option
                        show_cats = [val.split('|')[0].strip() for val in self.valid_show_options.values()]

                        #if arg not in self.valid_show_options.values():
                        if arg not in show_cats:
                            opt = colored("show ?", 'green')
                            print('[{}:show] Invalid argument: {}. Use {} for more information.'.format(
                                    self.siddhi,arg,opt
                                )
                            )
                            continue

                        if arg == 'summary':
                            cprint('\n→ Issues summary', 'cyan')
                            print(self.report_items['summary'])

                        elif arg == 'exceptions':
                            cprint('\n→ Triggered unhandled exceptions', 'cyan')
                            print(self.report_items['exceptions'])

                        elif arg == 'tickets':
                            if self._vmnf_session_.get('sample')\
                                and self.security_tickets is None:
                                print(colored('\n--| Sample mode doesnt search for version issues in runtime. Use: ', 'cyan'), colored('run itracker\n', 'green'))
                                continue

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
                            print(self.report_items['raw_patterns'])

                        elif arg == 'cves':
                            if self._vmnf_session_.get('sample')\
                                and self.cves is None:
                                print(colored('\n--| Sample mode doesnt search for version issues in runtime. Use: ', 'cyan'), colored('run itracker\n', 'green'))
                                continue
                            
                            cprint("\n→ CVE ID's (by framework version)", 'cyan')
                            print(self.report_items['cves'])

                        elif arg == 'applications':
                            cprint("\n→ Applications enabled in this Django installation", 'cyan')
                            print()
                            for app in self.installed_items['Installed Applications']:
                                print(f'   {app}')
                            print()

                        elif arg == 'middlewares':
                            cprint("\n→ Enabled Django middlewares", 'cyan')
                            print()
                            for mid in self.installed_items['Installed Middlewares']:
                                print(f'   {mid}')
                            print()

                        elif arg == 'databases':
                            cprint("\n→ Available databases", 'cyan')
                            print()
                            for k,v in self.sampler['DB_SETTINGS'].items():
                                print(f'   {k}: {v}')
                            print()

                        elif arg == 'objects':
                            cprint("\n→ Parsed traceback objects", 'cyan')
                            print(self.report_items['objects'])
                            print()

                        elif arg == 'variables':
                            print()
                            for exception in self._issues_.get('EXCEPTIONS'):
                                
                                cprint('\t  ' + exception['EXCEPTION_SUMMARY'].get('Exception Type') + '   ', 
                                        'white', 'on_red', attrs=['bold'])
                                print()
                                sleep(0.1)

                                DJUtils(False,False).show_module_args(
                                    *exception['EXCEPTION_TRACEBACK']
                                )

                        elif arg == 'log':
                            for entry in self._issues_.get('FUZZ_STATUS_LOG'):
                                for k,v in entry.items():
                                    print(f"\t + {k}: {colored(v,'blue')}")
                                    sleep(0.01)
                                cprint('-'*100,'magenta',attrs=['dark'])
                        
                        elif arg in ['ref','refs','references'] or arg.startswith('ref'):
                            DJUtils().consolidate_issues(self._issues_,self.report_items)
                            
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
                    elif cmd.rstrip() == 'inspect':
                        self._reason_ = False
                        _iid_ = r_cmd.split()[1].strip()
                        #_iid_ = arg                    # raw cmd arg
                        _type_ = _iid_[:2].strip()      # type identifier
                        _issue_ = _iid_[2:].strip()     # issue id without type identifier ST/UX/CI/LC
                        self._type_ = _type_            # for handler

                        if _type_ not in self.issue_categories.keys():
                            self._type_ = '??'
                            self._reason_ = 'Invalid issue identifier'
                            _pset_.handle_inspect_msg(
                                self._type_.lower(),
                                self._reason_,
                                self.issue_categories[self._type_]
                            )
                            continue
                        
                        # to handle inspect iid 'without' number identifier
                        if not _issue_:
                            self._reason_ = 'Invalid iid format'
                            _pset_.handle_inspect_msg(
                                self._type_.lower(),
                                self._reason_,
                                self.issue_categories[self._type_]
                            )
                            continue 
                        
                        # inspect security tickets
                        if _type_ == 'ST':
                            # if a choosen iid in current tickets pool
                            if _issue_ in str(self.security_tickets):
                                for ticket in self.security_tickets:
                                    if ticket['id'] == _issue_: 
                                        found_ticket = True
                                        cprint('\nRetrieving results for issue {}...\n'.format(ticket['id']),'cyan')
                                        sleep(1)
                                        
                                        cprint(ticket['title'], 'cyan')
                                        print()

                                        # get ticket details
                                        tictrac.siddhi(_issue_).start()
                            else:  
                                self._reason_ = 'Ticket not found'
                                _pset_.handle_inspect_msg(
                                    self._type_.lower(),
                                    self._reason_,
                                    self.issue_categories[self._type_]
                                )
                            print()
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
                            if _iid_ in str(self._issues_['EXCEPTIONS']):
                                for exception in self._issues_['EXCEPTIONS']:
                                    # show exception details
                                    if exception['IID'] == _iid_:
                                        found_exception = True
                                        print()

                                        DJUtils(False,False).show_exception(**exception)
                                        break
                                continue
                            else:
                                self._reason_ = 'Exception not found'
                                _pset_.handle_inspect_msg(
                                    self._type_.lower(),
                                    self._reason_,
                                    self.issue_categories[self._type_]
                                )
                                continue
                        
                        # inspect leaked [env] contexts 
                        elif _type_ == 'LC':
                            lc_not_found = True
                            i_count = 1

                            for env_ctx in self.contexts:
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
                                _pset_.handle_inspect_msg(
                                    self._type_.lower(),
                                    self._reason_,
                                    self.issue_categories[self._type_]
                                )
                                continue
                        
                        elif _type_ == 'SM': 
                            if not secmid_tbl:
                                print('\n[{}:inspect] You need to inspect the security middleware context before inspecting an SM issue.\n'.format(
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
                                _pset_.handle_inspect_msg(
                                    self._type_.lower(),
                                    self._reason_,
                                    self.issue_categories[self._type_]
                                )
                                continue

                            if _iid_ not in str(self.cves):
                                self._reason_ = 'Unrelated CVE Id'
                                _pset_.handle_inspect_msg(
                                    self._type_.lower(),
                                    self._reason_,
                                    self.issue_categories[self._type_]
                                )
                                continue

                            cprint('\nRetrieving details for CVE ID {}...\n'.format(_iid_), 'cyan')   
                            
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
                            print()
                            continue 

                        # inspect configuration issues
                        elif _type_ == 'CI':
                            # if a choosen exception in exceptions pool
                            if _iid_ in str(self._issues_['CONFIGURATION']):
                                for c_issue in self._issues_['CONFIGURATION']:
                                    # show exception details
                                    if c_issue['IID'] == _iid_:
                                        found_issue = True
                                        print()

                                        # basic exception information
                                        for k,v in c_issue.items():
                                            print('→ {}: {}'.format(colored(k,'cyan'),v))
                                        print()
                            else:
                                self._reason_ = 'Configuration issue not found'
                                _pset_.handle_inspect_msg(
                                    self._type_.lower(),
                                    self._reason_,
                                    self.issue_categories[self._type_]
                                )

                            continue

