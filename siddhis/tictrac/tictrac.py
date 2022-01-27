# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                    - TICTRACK -


    Django security tickets tracker for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch

"""



from neotermcolor import colored, cprint
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from pygments import highlight

import requests
import json
from bs4 import BeautifulSoup
import collections
from time import sleep


class siddhi:
    module_information = collections.OrderedDict()
    module_information = {
        "Name":         "TicTrack",
        "Acronym":      "Ticket Tracker",  
        "Category":     "Framework",
        "Framework":    "Django",
        "Type":         "Tracker",
        "Module":       "siddhis/tictrac",
        "Author":       "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":        "Track bug tickets in Django ticket system",
        "Description":
        """

        \r  This module implements methods for querying bug ticket details using 
        \r  official Django ticket system. The tool can be used in isolated mode, 
        \r  although it is generally used as a resource for other modules. 
        \r  For example, after performing the target analysis, the DMT module 
        \r  (Django Misconfiguration Tracker) will instantiate tictrac to consult 
        \r  bug tickets for a identified framework version.

        """

    }
    

    def __init__(self, query):
        ''' Initialize endpoints '''

        self.Django_releases = [
            '3.0', '2.2', '2.1',
            '2.0', '1.11', '1.10',
            '1.9', '1.8', '1.7',
            '1.6', '1.5', '1.4',
            '1.3', '1.2', '1.1',
            '1.0', '0.96', '0.95'
        ]

        self.query = str(query)
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

    def get_ticket_ids(self, django_version):
        ''' Retrieve all tickets (type:bug) for a given Django version '''

        response = requests.get(self.django_query_url.format(django_version, self.columns))
        soup = BeautifulSoup(response.content, "lxml")

        ticket_entry = 1
        for tag in soup.find_all('a', href=True):
            if '/ticket/' in str(tag) \
                and not 'class=' in str(tag):

                link = (tag['href'])
                title = str(tag)
                ticket_title = title[title.find('>') +1: title.find('</a>')]
                ticket_id = str(link.split('/')[-1]).strip()
        
                if ticket_title != "#{}".format(ticket_id):
                    #print('+ {}: {}'.format(ticket_id, ticket_title))
        
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

    def get_ticket(self, ticket_id):
        ''' Retrieve details about a given ticket '''
        response = requests.post(url=self.rpc_url, json=self.ticket_get_method)
        json_ = json.loads(response.text)
        
        for entry in json_['result']:
            if 'dict' in str(type(entry)): 
                for k,v in entry.items():
                    # technical details in description

                    if k == 'description' and '{{{' in str(v):
                        tech = str(v)[str(v).find('{{{'):str(v).find('}}}')]
                        hl_tech = highlight(str(tech),PythonLexer(),TerminalFormatter(),)
                        v = v.replace(tech,hl_tech)

                    print('→ {}: {}'.format(colored(k,'cyan'),v))
            else:
                    print('→ {}'.format(entry))

    def start(self):
        if self.query.find('.') != -1:
            self.get_ticket_ids(self.query)
            
            return self.ticket_register
        else:
            self.get_ticket(self.query)

