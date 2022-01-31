# -*- coding: utf-8 -*-

from pygments.formatters import TerminalFormatter
import sys, re, os, random, string, platform
from lxml.html.soupparser import fromstring
from pygments.lexers import PythonLexer
from neotermcolor import cprint, colored
from prettytable import PrettyTable
from collections import OrderedDict 
from pygments import highlight
from bs4 import BeautifulSoup
from netaddr import IPNetwork
from datetime import datetime
from time import sleep
import pygments
import argparse
import hashlib
import yaml


from settings.siddhis_shared_settings import django_envvars as djev
from settings.siddhis_shared_settings import csrf_table as csrf
from settings.siddhis_shared_settings import set_header 
from settings.siddhis_shared_settings import api_auth
from settings.siddhis_shared_settings import payloads
from core.vmnf_shared_args import VimanaSharedArgs
from core.vmnf_thread_handler import ThreadPool
import settings.vmnf_settings as settings
from core.vmnf_pshell import vmnfshell

from res.session.vmnf_sessions import createSession
from res.vmnf_text_utils import format_text
from res.vmnf_pxh import exception_hierarchy
from res import vmnf_banners
from res import colors

from requests import exceptions
from random import choice
import collections
import requests

from . _dju_settings import table_models
from siddhis.tictrac import tictrac
from . _dju_utils import DJUtils
from siddhis.prana import prana


class resultParser:   
    def __init__(self, results, **vmnf_handler):
        # dmt handler (argparser namespace) 
        self.vmnf_handler = vmnf_handler
        self.catched_exceptions = []

        self.fuzz_report=False
        tables = DJUtils().get_report_tables()
        
        #self.exceptions_tbl = tables['exceptions']
        self.config_issues_tbl = tables['configuration']
        self.summary_tbl = tables['summary']
        self.tickets_tbl = tables['tickets']
        self.envleak_tbl = tables['envleak']
        self.cves_tbl = tables['cves']
        self.traceback_objects_tbl = tables['objects']

        # siddhi name
        self.vmnf_handler = vmnf_handler 
        self.siddhi = vmnf_handler['module_run'].lower()

        # results from djunch fuzzer 
        if (len(results['EXCEPTIONS'])) == 0:
            return None
        
        # instance of djunch results
        self.fuzz_report = results 
        
        # exception sampler: to use shared information between exceptions
        self.sampler = results['EXCEPTIONS'][0]

        # general analysis objects
        self.general_objects = results['GENERAL_OBJECTS']
        
        # mapped (expanded url patterns from DMT)
        self.raw_patterns = self.vmnf_handler['raw_patterns']
       
        # passive fingerprint results
        self.fingerprint = self.vmnf_handler['fingerprint']

    def show_issues(self):

        print("\033c", end="")
        if not self.vmnf_handler.get('sample'):
            vmnf_banners.audit_report_banner()
        else:
            vmnf_banners.sample_mode(colored('       DMT      ','white', 'on_red', attrs=['bold']),['bold'])
            print('\n\n')
        
        if not self.fuzz_report:
            print('[result_parser: {}] Missing fuzzing result after {} execution'.format(
                datetime.now(),
                self.siddhi
                )
            )
    
            return False

        hl_color = 'green'

        if not self.vmnf_handler.get('sample'):
            mark_status = colored(' ● ', 'green', attrs=['bold', 'blink'])
            status_msg = colored('Consolidating analysis result...', 'blue')
            print('\n {} {}'.format(mark_status, status_msg))
            sleep(1)
        
        security_tickets=None
        cves=None
        found_exceptions= [] 

        for exception in self.fuzz_report['EXCEPTIONS']:
            found_exceptions.append(exception['EXCEPTION_TYPE'].rstrip())
        
        if not self.vmnf_handler.get('sample'):
            pxh = exception_hierarchy()

            for x in pxh.split('\n'):
                x_ref = (x.split('- ')[-1])
                if x_ref in found_exceptions:
                    x_c = colored(x_ref,'red',attrs=['bold','blink'])
                    x = x.replace(x_ref,x_c)
                print(x)
                sleep(0.04)
            sleep(0.14)

        _prana_ = []
        cve_siddhi = colored('prana', 'green')
        tickets_siddhi = colored('tictrac', 'green') 
        

        django_version = self.sampler['EXCEPTION_SUMMARY'].get('Django Version').strip()
        self.sampler['FINGERPRINT'] = self.fingerprint
        
        # get well known framework issues by identified version [exception fuzzer]
        fmk_version_issues = False
        
        if not self.vmnf_handler.get('sample'):
            fmk_version_issues = DJUtils().get_version_issues(**self.sampler)
        
        if fmk_version_issues:
            security_tickets = fmk_version_issues.get('tickets')
            cves = fmk_version_issues.get('cves')
            self.tickets_tbl = fmk_version_issues.get('tickets_tbl')
            self.cves_tbl = fmk_version_issues.get('cves_tbl')

        # issues overview
        installed_items = self.sampler['INSTALLED_ITEMS']
        self.issues_overview = {
            'total_issues': (
                len(self.fuzz_report['EXCEPTIONS']) + \
                len(self.fuzz_report['CONFIGURATION'])),
            'objects': len(self.general_objects),
            'security_tickets': len(security_tickets) if security_tickets else 0,
            'cve_ids': len(cves) if cves else 0,
            'url_patterns': len(self.raw_patterns) if self.raw_patterns else 0,   
            'applications': len(installed_items.get('Installed Applications')),
            'middlewares' : len(installed_items.get('Installed Middlewares'))
        }

        for tb_object in self.general_objects:
            self.traceback_objects_tbl.add_row(
                [
                    tb_object['variable'],
                    tb_object['object'],
                    colored(tb_object['address'], 'blue')
                ]
            )


        i_count = 1
        # >> load contexts 
        self.contexts = self.sampler['CONTEXTS']
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

        # build exception items with fuzzer results
        exceptions_items = DJUtils().generate_exceptions_table(self.fuzz_report['EXCEPTIONS'])
        
        self.exceptions_tbl = exceptions_items['exceptions_tbl']
        total_xocc = exceptions_items['total_xocc']
        env_pool = exceptions_items['env_pool']
        count_lines = exceptions_items['count_lines']
        count_vars = exceptions_items['count_vars']
        count_triggers = exceptions_items['count_triggers']

        i_count = 1
        # >> load configuration issues into table 
        for issue in self.fuzz_report['CONFIGURATION']:
            self.config_issues_tbl.add_row(
                [
                    #colored('CI' + str(i_count), 'green'),
                    colored(issue['IID'], 'green'),
                    issue['STATUS'],
                    issue['METHOD'],
                    issue['ISSUE']
                ]
            )
            i_count +=1 
            
        ########################
        ########################
        ## DMT PROMPT REPORT  ##
        ########################
        ########################
        if not self.vmnf_handler.get('sample'):
            DJUtils().show_scan_settings(**self.vmnf_handler)
        
        ###########################
        ### target environment ####
        ###########################
        if not self.vmnf_handler.get('sample'):
            self.contexts = DJUtils().show_server_env(self.contexts)

        ##########################
        ### env leak contexts ####
        ##########################
        if not self.vmnf_handler.get('sample'):
            cprint("\n⣛⣓\tEnvLeak Contexts              ", "white", "on_red", attrs=['bold'])        
            print()
            cprint("\tEnvironment variables leaked by context.\n",'cyan', attrs=[])
            print(self.envleak_tbl)

        ##########################
        ### Application Issues ###
        ##########################
        if not self.vmnf_handler.get('sample'):
            cprint("\n⡯⠥\tApplication Issues                ", "white", "on_red", attrs=['bold'])        
            print()
            cprint("\tSecurity weaknesses identified during {} analysis.\n".format(
                self.vmnf_handler['module_run']),
                'cyan', attrs=[]
            )
        
            for k,v in self.issues_overview.items():
                k = (k.replace('_',' ')).capitalize()
                print('{}{}:\t   {}'.format(
                    (' ' * int(5-len(k) + 15)),k,
                    colored(v, hl_color)
                    )
                )
            sleep(1)

        ###################
        ### URL patterns ##
        ###################
        if not self.vmnf_handler.get('sample'):
            if self.raw_patterns:
                cprint('\nWere identified {} URL patterns that served as initial scope for fuzzing step\n'.format(
                    len(self.raw_patterns)),'cyan')
            
                # mapped URL patterns (reusing dmt construted table here)
                for pattern in self.raw_patterns:
                    print('   + {}'.format(pattern))
                    sleep(0.03)
        
        ##################
        ### exceptions ###
        ##################
        if not self.vmnf_handler.get('sample'):
            cprint('\nWere triggered {} exceptions that lead to CWE-215 allowing information exposure'.format(
                len(self.fuzz_report['EXCEPTIONS'])),'cyan')
        
            print(self.exceptions_tbl)
        
        if not self.vmnf_handler.get('sample'):
            # get external issues references
            DJUtils().get_cwe_references()
        
        if not self.vmnf_handler.get('sample'):
            ############################
            ### configuration issues ###
            ############################
            if self.fuzz_report['CONFIGURATION']: 
                status = ('\nWere identified {} configuration issues that make it possible to infer configurations and identify technologies.'.format(
                    len(self.fuzz_report['CONFIGURATION'])
                    )
                )
                cprint(status, 'cyan', attrs=[])
                print(self.config_issues_tbl)
            
        if not self.vmnf_handler.get('sample'):
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
            if cves:
                cprint(']]- CVE IDs ({})'.format(cve_siddhi), 'magenta')
                print(self.cves_tbl)

        report_tables = {
            'summary': self.summary_tbl,
            'tickets': self.tickets_tbl,
            'cves': self.cves_tbl,
            'exceptions': self.exceptions_tbl,
            'configuration': self.config_issues_tbl,
            'contexts': self.envleak_tbl,
            'raw_patterns': self.raw_patterns,
            'objects': self.traceback_objects_tbl
        }

        # + security_tickets: collected security tickets [list of dicts]
        self.fuzz_report['_count_issues_'] = {
            'total_lines': str(count_lines),
            'total_vars': str(count_vars),
            'total_triggers': str(count_triggers),
            'total_exceptions': str(total_xocc),
            'total_env': str(max(env_pool))
        } 

        #if we need command line arguments [after siddhis execution] inside vmnfsheel  we can set _vmnf_session_ as a new key to vmnf_handler
        # and pass the handler itself to vmnfshell, but at this time we're going to use just target_url, what was passed as argument to dmt with `run`
        #self.vmnf_handler['_vmnf_session_']
        
        self.vmnf_handler.update(
            {
                'module_run':self.siddhi,
                'djunch_result':self.fuzz_report,
                'security_tickets':security_tickets,
                '_cves_':cves,
                'report_tables':report_tables,
                'prompt': vmnfshell
            }
        )
        vmnfshell(**self.vmnf_handler)

        '''
        vmnfshell(
            **{
                'target_url':self.vmnf_handler.get('target_url'),
                'module_run':self.siddhi,
                'djunch_result':self.fuzz_report,
                'security_tickets':security_tickets,
                '_cves_':cves,
                'report_tables':report_tables,
                'prompt': vmnfshell
            }
        )
        '''
