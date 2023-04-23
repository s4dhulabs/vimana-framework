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

from neotermcolor import colored, cprint
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

class siddhi:
    def __init__(self, **vmnf_handler:False):
        if not vmnf_handler:
            cprint("Something went wrong. Missing framework handler while calling tictrac!", 'red')
            sys.exit()

        self.vmnf_handler = vmnf_handler
            
        if not vmnf_handler.get('django_version'):
            cprint("Something went wrong. Missing django version!", 'red')
            
            return 

        self.query = str(vmnf_handler.get('django_version'))
        self.rpc_url = 'https://code.djangoproject.com/jsonrpc'

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
        self.ticket_get_method = {
            "method": "ticket.get", 
            "params": [self.query]
        }

        django_version = vmnf_handler.get('django_version')
        issue_type = 'tickets'
        plugin_scope = f'django/{issue_type}'
        self.cache_dir = f'siddhis/__cache__/{plugin_scope}'
        self.issues_path = f"{self.cache_dir}/{django_version}.json"

        self.cache_load_enabled = True \
            if (not self.vmnf_handler['ignore_cache']) else False
        self.cache_enabled = True \
            if (not self.vmnf_handler['disable_cache']) else False

        self.specs = {
            'issues_path': self.issues_path,
            'django_version': django_version,
            'issue_type': issue_type
        }
        self.vmnf_handler.update(self.specs)

    def get_ticket_ids(self, django_version=False):
        ''' Retrieve all tickets (type:bug) for a given Django version '''
    
        if not django_version:
            if not self.query:
                print('Missing Django version')
                return False
            django_version = self.query
       
        if self.cache_load_enabled:
            try:
                tickets, issues_table = load_plugin_cache(self.vmnf_handler)
                return tickets,issues_table
            except TypeError:
                pass

        try:
            response = requests.get(self.django_query_url.format(django_version, self.columns))
            soup = BeautifulSoup(response.content, "lxml")
        except KeyboardInterrupt:
            return False
        except ConnectionError:
            cprint("[tictrac] → Failed to establish a new connection.",'red')
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
       
        if self.vmnf_handler['module_run'].lower() == 'tictrac':
            tickets_table = DJUtils().get_tickets_table(
                django_version,
                self.ticket_register
            )

            print(tickets_table)
            return True
       
        if self.cache_enabled:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)

            if not os.path.exists(self.issues_path):
                with open(self.issues_path, 'w') as f:
                    json.dump(self.ticket_register, f, indent=4)

        issues_table = gen_issues_table(self.ticket_register, 'Tickets')
        return self.ticket_register, issues_table

    def get_ticket(self, ticket_id):
        ''' Retrieve details about a given ticket '''

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
        if self.query.find('.') != -1:
            self.get_ticket_ids(self.query)
        else:
            self.get_ticket(self.query)

