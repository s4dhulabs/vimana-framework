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

from ..djunch.engines._dju_utils import DJUtils

from neotermcolor import cprint,colored as cl
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from pygments import highlight
import textwrap

import os
import sys
import json
import requests
import collections
from time import sleep
from bs4 import BeautifulSoup
from tabulate import tabulate
from requests.exceptions import ConnectionError
from core.vmnf_utils import load_plugin_cache,gen_issues_table

# vflogging
import logging
from core.vmnf_log_utils import configure_logging
configure_logging(os.path.basename(__file__))

class siddhi:
    def __init__(self, **vmnf_handler:False):
        logging.info("Initializing tictrac...")

        if not vmnf_handler:
            status = "Something went wrong. Missing framework handler while calling tictrac!"
            cprint(status, 'red')
            print()
            logging.error(status)
            sys.exit()

        self.vmnf_handler = vmnf_handler
        self.query = str(vmnf_handler.get('django_version'))
        self.django_query_url = '''https://code.djangoproject.com/query?version={}&type=Bug&{}'''
        self.columns = '''
            max=0&\
            col=id&\
            col=summary&\
            col=type&\
            col=owner&\
            col=status&\
            col=component&\
            col=severity&\
            col=reporter&\
            order=priority
        '''

        self.ticket_register = []
        self.tickets = []
        django_version = vmnf_handler.get('django_version')

        issue_type = 'tickets'
        plugin_scope = f'django/{issue_type}'
        self.cache_dir = f'.vimana/cache/{plugin_scope}'
        self.abs_cache_path = os.path.join(os.path.expanduser("~"), self.cache_dir)

        self.issues_path = f"{self.abs_cache_path}/{django_version}.json"
        self.vmnf_handler['issue_type'] = issue_type

        self.cache_load_enabled = not self.vmnf_handler.get('ignore_cache',False)
        self.cache_enabled = not self.vmnf_handler.get('disable_cache',False) 

        self.specs = {
            'issues_path': self.issues_path,
            'django_version': django_version,
            'issue_type': issue_type
        }
        self.caller = vmnf_handler.get('module_run',False)
        self.engineitself = True if (self.caller and self.caller == 'tictrac') else False
        self.vmnf_handler.update(self.specs)
        
        logging.info("Class initialized successfully!")

    def get_ticket_ids(self, django_version=False):
        ''' Retrieve all tickets (type:bug) for a given Django version '''
   
        if not django_version:
            if not self.query:
                print('Missing Django version')
                logging.info('Missing Django version!')
                return False

            django_version = self.query
      
        hl_django_version = cl(django_version,'green')

        if self.cache_load_enabled:
            try:
                tickets, issues_table = load_plugin_cache(self.vmnf_handler)
                if self.engineitself:
                    print(
                        f"[{cl(self.caller,'red')}]→ "
                        f"{cl(len(tickets),'green')} "
                        f"Security Tickets for Django {hl_django_version}"
                    )

                    print(issues_table)
                    input() if self.vmnf_handler.get('pause_steps') else sleep(1)

                return tickets,issues_table

            except TypeError:
                pass
        
        try:
            response = requests.get(
                self.django_query_url.format(django_version, self.columns)
            )
            soup = BeautifulSoup(response.content, "lxml")
        except KeyboardInterrupt:
            return False
        except ConnectionError:
            err_status = "[tictrac] → Failed to establish a new connection."
            cprint(err_status,'red')
            logging.error(err_status)
            sys.exit(1)

        ticket_entry = 1
        for tag in soup.find_all('a', href=True):
            if '/ticket/' in str(tag) \
                and not 'class=' in str(tag):

                link = (tag['href'])
                title = str(tag)
                ticket_title = title[title.find('>') +1: title.find('</a>')]
                ticket_id = str(link.split('/')[-1]).strip()
        
                if ticket_title != "#{}".format(ticket_id):
                    if not ticket_id in self.tickets:
                        self.tickets.append(link.split('/')[-1])
                        ticket = {
                            'entry': ticket_entry,
                            'id': ticket_id,
                            'title': ticket_title
                        }
                        self.ticket_register.append(
                            ticket
                        )
                        
                        ticket_entry +=1
       
        if self.cache_enabled:
            if not os.path.exists(self.abs_cache_path):
                os.makedirs(self.abs_cache_path)

            if not os.path.exists(self.issues_path):

                with open(self.issues_path, 'w') as f:
                    json.dump(self.ticket_register, f, indent=4)

        issues_table = gen_issues_table(self.ticket_register, 'Tickets')

        if self.engineitself:
            print(
                f"[{cl(self.caller,'red')}]→ "
                f"{cl(len(self.ticket_register),'green')} "
                f"Security Tickets for Django {hl_django_version}"
            )

            input() if self.vmnf_handler.get('pause_steps') else sleep(1)
            print(issues_table)
            return True,True

        return self.ticket_register, issues_table

    def get_ticket(self, ticket_id):
        ''' Retrieve details about a given ticket '''

        self.rpc_url = 'https://code.djangoproject.com/jsonrpc'

        self.ticket_get_method = {
            "method": "ticket.get",
            "params": [ticket_id]
        }

        response = requests.post(
            url=self.rpc_url, 
            json=self.ticket_get_method
        )

        json_ = json.loads(response.text)
        
        for entry in json_['result']:
            if 'dict' in str(type(entry)): 
                for k,v in entry.items():
                    # technical details in description

                    if k == 'description' and '{{{' in str(v):
                        tech = str(v)[str(v).find('{{{'):str(v).find('}}}')]
                        hl_tech = highlight(str(tech),PythonLexer(),TerminalFormatter(),)
                        v = v.replace(tech,hl_tech)

                    print(f"→ {colored(k,'cyan')}: {v}")
            else:
                    print(f'→ {entry}')

    def start(self):
        if not self.vmnf_handler.get('django_version'):
            err_status = "Something went wrong. Missing django version!"
            input(cl(err_status, 'red'))
            logging.error(err_status)
            return False

        if self.query.find('.') != -1:
            ti,ta = self.get_ticket_ids(self.query)
            return ti,ta
        else:
            self.get_ticket(self.query)

