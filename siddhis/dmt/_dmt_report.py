# -*- coding: utf-8 -*-

from pygments.formatters import TerminalFormatter
import sys, re, os, random, string, platform
from lxml.html.soupparser import fromstring
from pygments.lexers import PythonLexer
from termcolor import cprint, colored
from prettytable import PrettyTable
from collections import OrderedDict 
#from resources.core.colors import *
from pygments import highlight
from bs4 import BeautifulSoup
from netaddr import IPNetwork
from datetime import datetime
from time import sleep
import argparse
import hashlib
import pygments

from .. _shared_settings_.__settings import django_envvars as djev
from .. _shared_settings_.__settings import csrf_table as csrf
from .. _shared_settings_.__settings import set_header 
from .. _shared_settings_.__settings import api_auth
from .. _shared_settings_.__settings import payloads

from core.vmnf_pshell import vmnfshell
from core.vmnf_shared_args import VimanaSharedArgs
from core.vmnf_thread_handler import ThreadPool

from resources.session.vmn_session import createSession
from resources.vmnf_text_utils import format_text
from resources.vmnf_pxh import exception_hierarchy
from resources import vmnf_banners
from resources import colors

from requests import exceptions
from random import choice
import collections
import requests

from siddhis.prana import prana
from siddhis.tictrac import tictrac




class resultParser:   

    def __init__(
            self,
            xp_tbl,
            mapped_patterns,
            results, 
            **vmnf_handler
        ):
    
        # siddhi name
        self.siddhi = vmnf_handler['module_run'].lower()

        # dmt mapped url patterns
        self.xp_tbl = xp_tbl

        # results from djunch fuzzer 
        if results:
            self.djunch_result = results 
            self.contexts = results[0]
            self._issues_ = results[1]
        else:
            ''' In which cases would we not have the result of the fuzzer 
                at this point in the result parser? I don't know exactly yet, 
                but it is good to leave it mapped for future treatments. '''
                
            print('[result_parser: {}] Missing fuzzing result after {} execution'.format(
                datetime.now(),
                self.siddhi
                )
            )
            
            return False
        
        # mapped (expanded url patterns from DMT)
        self.mu_patterns = mapped_patterns

        # dmt handler (argparser namespace) 
        self.vmnf_handler = vmnf_handler
        self.catched_exceptions = []

        # ==[ UX - EXCEPTIONS ]==
        self.exceptions_tbl = PrettyTable()
        self.exceptions_tbl.field_names = [
            'iid', 
            'type', 
            'function', 
            'location', 
            'line', 
            'lines',
            'triggers',
            'reference',
            'occurrences'
        ]
        self.exceptions_tbl.align = "l"
        self.exceptions_tbl.title = colored(
            "Exceptions", 
            "white", 
            attrs=['bold']
        )       

        # ==[ CI - CONFIGURATION issues ]==
        self.config_issues_tbl = PrettyTable()
        self.config_issues_tbl.field_names = [
            'iid',
            'status', 
            'pattern', 
            'method', 
            'issue', 
            'reference', 
        ]
        self.config_issues_tbl.align = "l"
        self.config_issues_tbl.title = colored(
            "Configuration issues", 
            "white", 
            attrs=['bold']
        )       

        # ==[ SUMMARY tbl (not used in this version) ]==
        self.summary_tbl = PrettyTable()
        self.summary_tbl.field_names = [
            'Issues',
            'Security Tickets',
            'CVEs'
        ]
        self.summary_tbl.align = "l"
        self.summary_tbl.title = colored(
            "Summary",
            "white",
            attrs=['bold']
        )

        # ==[ TICKETS Table ]==
        self.tickets_tbl = PrettyTable()
        self.tickets_tbl.field_names = [
            'iid',
            'title'
        ]
        self.tickets_tbl.align = "c"
        '''
        self.tickets_tbl.title = colored(
            "Security Tickets",
            "white",
            attrs=['bold']
        )
        '''
        # ==[ ENV leak contexts table ]==
        self.envleak_tbl = PrettyTable()
        self.envleak_tbl.field_names = [
            'iid',
            'context',
            'variables'
        ]
        self.envleak_tbl.align = "c"
        self.envleak_tbl.title = colored(
            "Envleak Contexts",
            "white",
            attrs=['bold']
        )

        # ==[ CVE Table ]==
        self.cves_tbl = PrettyTable()
        self.cves_tbl.field_names = [
            'iid',
            'title',
            'date'
        ]
        self.cves_tbl.align = "c"
        '''
        self.cves_tbl.title = colored(
            "CVE IDs for Django {}",
            "white",
            attrs=['bold']
        )
        '''

    def show_issues(self):
        
        print("\033c", end="")
        vmnf_banners.audit_report_banner()

        mark_status = colored('●', 'green', attrs=['bold', 'blink'])
        status_msg = colored('Consolidating analysis result...', 'blue')
        print('\n {} {}'.format(mark_status, status_msg))
        sleep(1)

        found_exceptions = []
        for exception in self._issues_['exceptions']:
            found_exceptions.append(exception['type'].rstrip())

        pxh = exception_hierarchy()
        for x in pxh.split('\n'):
            x_ref = (x.split('- ')[-1])
            if x_ref in found_exceptions:
                x_c = colored(x_ref,'red',attrs=['bold','blink'])
                x = x.replace(x_ref,x_c)
            print(x)
            sleep(0.10)


        _prana_ = []
        cve_siddhi = colored('prana', 'green')
        tickets_siddhi = colored('tictrac', 'green') 

        if 'django version' or 'django_version' \
            in str(self.contexts['environment'].keys()).lower():

            django_version = self.contexts['environment'].get('DJANGO_VERSION')
            
            if not django_version or django_version is None:
                django_version = self.contexts['environment'].get('Django Version')

            # if Django Versions is found in Djunch 'environment_context'
            if django_version and django_version is not None:
                if len(django_version.split('.')) >= 3:
                    django_version = '.'.join(django_version.split('.')[:-1])

                # **** fakefortests *** 
                django_version = '2.2'

                # - Get CVEs and security tickets for abducted framework version-
                security_tickets = tictrac.siddhi(django_version).start()
                cves = prana.siddhi(django_version).start()
                _prana_.append(cves)
               
                # Security Tickets table
                for ticket in security_tickets:
                    title = ticket['title']
                    
                    # max text len to pretty result
                    if len(title) > 100:
                        title = str(title[:100]) + '...'
                    
                    # >> load security tickets 
                    self.tickets_tbl.title = colored(
                        "Security tickets for Django {}".format(django_version),
                        "white", attrs=['bold']
                    )

                    self.tickets_tbl.add_row(
                        [
                            colored('ST{}'.format(ticket['id']),'green'),
                            title
                        ]
                    )
        
                # CVE table
                if cves:
                    for entry in cves:
                        # >> load cve ids
                        self.cves_tbl.title = colored(
                            "CVE IDs for Django {}".format(django_version),
                            "white",attrs=['bold']
                        )
                    
                        self.cves_tbl.add_row(
                            [
                                colored(entry['id'],'green'),
                                entry['title'].rstrip(),
                                entry['date'].rstrip()

                            ]
                        )
        
        # issues overview
        self.issues_overview = {
            'total_issues': (
                len(self._issues_['exceptions']) + \
                len(self._issues_['configuration'])),
            'security_tickets': len(security_tickets),
            'cve_ids': len(cves) if cves else 0,
            'url_patterns': len(self.mu_patterns)
        }

        i_count = 1
        # >> load contexts 
        for k,v in self.contexts.items():
                self.envleak_tbl.add_row(
                    [
                        colored('LC{}'.format(str(i_count)), 'green'),
                        k.strip(),
                        str(len(self.contexts[k]))
                    ]
                )

                i_count +=1

        # dmt isnot using this table yet
        # >> load issues summary
        self.summary_tbl.add_row(
            [
                self.issues_overview['total_issues'],
                self.issues_overview['security_tickets'],
                self.issues_overview['cve_ids']
            ]
        )

        i_count = 1
        # >> load exceptions into table 
        for exception in self._issues_['exceptions']:
            self.exceptions_tbl.add_row(
                [ 
                    #colored('UX' + str(i_count),'green'),
                    colored(exception['iid'], 'green'),
                    exception['type'],
                    exception['function'],
                    exception['lmodule'],
                    exception['line'],
                    exception['lines'],
                    len(exception['triggers']),
                    exception['reference'],
                    exception['occ']
                ]
            )    
            i_count +=1
        
        i_count = 1
        # >> load configuration issues into table 
        for issue in self._issues_['configuration']:
            self.config_issues_tbl.add_row(
                [
                    #colored('CI' + str(i_count), 'green'),
                    colored(issue['iid'], 'green'),
                    issue['status'],
                    issue['pattern'],
                    issue['method'],
                    issue['issue'],
                    issue['reference']
                ]
            )
            i_count +=1 

            
        ########################
        ########################
        ## DMT PROMPT REPORT  ##
        ########################
        ########################
        ''' s4dhu notes: I am already drafting some alternatives for reporting and presenting results 
        for the next versions (or next commits), however, this presentation via terminal 
        will always exist, it is the standard way of summarizing the results. '''

        print("\033c", end="")
        vmnf_banners.audit_report_banner('DMT')

        ### Abudct analysis ###
        cprint("\n⣆⣇      Scan settings                          \n", "white", "on_red", attrs=['bold'])        
        cprint("\tGeneral settings and siddhis called during analysis.\n",
                'cyan', attrs=[]
        )
        
        hl_color = 'green'
        sg = colored('→', hl_color, attrs=['bold'])
        
        # 'abduct' is a set of command and options specified to run the chosen module
        for _abd_k, _abd_v in (self.vmnf_handler.items()):
            if _abd_v:
                print('{}{}:\t   {}'.format(
                    (' ' * int(5-len(_abd_k) + 15)), 
                    _abd_k, 
                    colored(_abd_v, hl_color)
                    )
                )
        print()
        sleep(1)
        

        ###########################
        ### target environment ####
        ###########################
        cprint("\n⣠⣾      Target Environment              ", "white", "on_red", attrs=['bold'])        
        print()
        cprint("\tDetails about target application environment.\n",
                'cyan', attrs=[]
        )

        #for k,v in self._server_context_.items():
        for k,v in self.contexts['server'].items():
            k = (k.replace('_',' ')).capitalize()
            print('{}{}:\t   {}'.format(
                (' ' * int(5-len(k) + 15)),
                k,
                colored(v, hl_color)
                )
            )
            sleep(0.10)

        #for k,v in self._environment_context_.items():
        for k,v in self.contexts['environment'].items():
            k = (k.replace('_',' ')).capitalize()

            # fakefortests
            # if v == '1.11.21': v = '2.2.0'

            print('{}{}:\t   {}'.format(
                (' ' * int(5-len(k) + 15)),
                k,
                colored(v, hl_color)
                )
            )
            sleep(0.10)

        print()
        sleep(0.20)


        ##########################
        ### env leak contexts ####
        ##########################
        cprint("\n⣛⣓\tEnvLeak Contexts              ", "white", "on_red", attrs=['bold'])        
        print()
        cprint("\tEnvironment variables leaked by context.\n",
                'cyan', attrs=[]
        )

        print(self.envleak_tbl)
        '''
        for k,v in self.contexts.items():
            if v:
                print('{}{}:\t   {}'.format(
                    (' ' * int(5-len(k) + 15)),
                    k,colored(str(len(self.contexts[k])),hl_color)
                    )
                )
                sleep(0.10)
        print()
        sleep(1)
        '''

        ##########################
        ### Application Issues ###
        ##########################
        cprint("\n⡯⠥\tApplication Issues                ", "white", "on_red", attrs=['bold'])        
        print()
        cprint("\tSecurity weaknesses identified during {} analysis.\n".format(
                self.vmnf_handler['module_run']),
                'cyan', attrs=[]
        )
        
        for k,v in self.issues_overview.items():
            k = (k.replace('_',' ')).capitalize()
            print('{}{}:\t   {}'.format(
                (' ' * int(5-len(k) + 15)),
                k,
                colored(v, hl_color)
                )
            )

        #cprint("\t{} Critical: {}".format(sg,len(self._issues_['exceptions'])), 'red')
        #cprint("\t{} Low: {}".format(sg,len(self._issues_['configuration'])), 'red')
        #print()
        sleep(1)

        ###################
        ### URL patterns ##
        ###################
        cprint('\nWere identified {} URL patterns that served as initial scope for fuzzing step'.format(
            len(self.mu_patterns)),'cyan')

        # mapped URL patterns (reusing dmt construted table here)
        print(self.xp_tbl)
        
        ##################
        ### exceptions ###
        ##################
        cprint('\nWere triggered {} exceptions that lead to CWE-215 allowing information ex1posure'.format(
            len(self._issues_['exceptions'])),'cyan')

        #cprint(status, 'cyan', attrs=[])
        
        print(self.exceptions_tbl)
        cwe = colored('CWE-215','blue',attrs=['bold'])
        cwe_title = colored(": Insertion of Sensitive Information Into Debugging Code           ", "blue",  attrs=[])
        print('\n {}{}'.format(cwe,cwe_title))
        print('''
        \r When debugging, it may be necessary to report detailed information
        \r to the programmer. However, if the debugging code is not disabled
        \r when the application is operating in a production environment,
        \r then this sensitive information may be exposed to attackers.
        
        \r https://cwe.mitre.org/data/definitions/215.html
        ''')
        sleep(1)

        # basic vuln reference
        cprint('\n\rRelated vulnerabilities:', 'blue')
        print('''
        \r  https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-1999007
        \r  https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2015-5306
        \r  https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-2006

        ''')


        ############################
        ### configuration issues ###
        ############################
        status = ('\nWere identified {} configuration issues that make it possible to infer configurations and identify technologies.'.format(
            len(self._issues_['configuration'])
            )
        )
        cprint(status, 'cyan', attrs=[])
        print(self.config_issues_tbl)
        
        cwe = colored('CWE-209','blue',attrs=['bold'])
        cwe_title = colored(": Generation of Error Message Containing Sensitive Information     ", "blue", attrs=[])
        print('\n {}{}'.format(cwe,cwe_title))
        print(''' 
        \r The sensitive information may be valuable information on its own
        \r (such as a password), or it may be useful for launching other, more
        \r serious attacks. The error message may be created in different ways:

        \r    * self-generated: the source code explicitly constructs the
        \r      error message and delivers it 

        \r    * externally-generated: the external environment, such as a 
        \r      language interpreter, handles the error and constructs its own message, 
        \r      whose contents are not under direct control by the programmer. 
        
        \r An attacker may use the contents of error messages to help launch another. 
        
        \r https://cwe.mitre.org/data/definitions/209.html
        ''')
        sleep(1)


        ################################
        ### Framework version issues ###
        ################################
        cprint("\n⣾\tFramework Issues                  ", "white", "on_red", attrs=['bold'])        
        print()
        cprint("\tSecurity tickets and CVEs associated with the Framework version\n",'cyan', attrs=[])
        
        # Security Tickets
        cprint(']]- Security Tickets ({})'.format(tickets_siddhi), 'magenta')
        if security_tickets:
            print(self.tickets_tbl)
            print()
        else:
            print('No security tickets identified for Django {}'.format(django_version))


        # CVE IDs 
        cprint(']]- CVE IDs ({})'.format(cve_siddhi), 'magenta')
        if cves:
            print(self.cves_tbl)
        else: 
            print('No cves identified for Django {}'.format(django_version))
       
        ''' s4dhu notes: There is some conceptual confusion here. 
        At this time I dont know exactly where to invoke vimana prompt, 
        because there are many result objects to parse and link to 
        vimana main commands and with specific siddhi commands.'''

        # + djunch_result: list of [2] dicts
        # |- self.contexts 
        # |- self._issues_  
             #|- _issues_['configuration']
             #|- _issues_['exception']

        report_tables = {
            'summary': self.summary_tbl,
            'tickets': self.tickets_tbl,
            'cves': self.cves_tbl,
            'exceptions': self.exceptions_tbl,
            'configuration': self.config_issues_tbl,
            'contexts': self.envleak_tbl,
            'patterns': self.xp_tbl

        }

        # + security_tickets: collected security tickets [list of dicts]
        vmnfshell(
            self.siddhi,
            self.djunch_result,
            security_tickets,
            _prana_,
            **report_tables
        )

       



