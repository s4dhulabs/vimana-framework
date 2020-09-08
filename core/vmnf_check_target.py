#!/usr/bin/env python



import os
import sys
from datetime import datetime
import socks
import socket
from time import sleep
from resources import colors
from resources.session.vmnf_proxies import _set_socks_
from settings.siddhis_shared_settings import common
from termcolor import colored,cprint

class CheckTargetScope:

    def __init__(self,target=False,ports=False,**vmnf_handler):
        
        self.vmnf_handler = vmnf_handler
        if not ports:
            ports = common().homolog_ports
        
        self.target = target
        self.port_list  = ports
        self.t = []
        self.p = []
        self.s = []

    def check_port_status(self):
        result = ''
        
        try:
            socket_obj = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            socket_obj.settimeout(10)
            result = socket_obj.connect_ex((self.target, int(self.port)))    
            socket_obj.close()
            service = '*'
        except socks.SOCKS5Error as _se_:
            pass
        except socket.timeout:
            pass
        except socks.HTTPError:
            pass
        except socks.GeneralProxyError:
            pass

        _target_ = colored(self.target.strip(), 'yellow')
        _port_   = colored(self.port.strip(), 'yellow')
        
        if result == 0:
            _status_ = colored('Open', 'green', attrs=['bold'])

            try:
                service = socket.getservbyport(int(self.port))
            except socket.error:
                pass
            
            result = self.port
        else:
            _status_ = colored('Closed', 'red', attrs=['bold'])
            result = None

        self.t.append(_target_)
        self.p.append(_port_)
        self.s.append(_status_)

        return result 

    def start_scan(self):
        open_ports = []
        valid_scope = []
        closed_ports = []
        
        '''It is certainly not the most elegant way to do this, but for now its enough.'''
        proxy_set = _set_socks_(**self.vmnf_handler).test_conn()
        
        if proxy_set:
            exit_ip = str(proxy_set['response'].content).replace("b",'').replace("'",'')
            status = colored('OK','green', attrs=['bold'])
            eip = colored(exit_ip, 'green')
            msg = colored('Connection going out {}'.format(eip),'cyan')
            proxy_type = colored(proxy_set['proxy_type'].rstrip() + ' proxy', 'white')
            _s_ = colored('{}: {} → {}'.format(proxy_type, status, msg ,'cyan'))
            
            print('{} {}'.format(colored('⡯⠥','green', attrs=['bold']),_s_))
            sleep(1)
        
        print("{} Validating port status for target {}{}{}...\n".format(
            colors.Gn_c + "⠿⠥" + colors.C_c,
            colors.G_c,
            self.target,
            colors.D_c
            )
        )
        sleep(0.25)

        for port in self.port_list:
            self.port = str(port).rstrip()
            port_status = self.check_port_status()
            if not port_status or port_status is None:
                closed_ports.append(port)
                continue
            else:
                valid_scope.append(str(self.target + ':' + port_status))

        gen_status = list(zip(self.p,self.s))

        for i, d in enumerate(gen_status):
            line = ' '.join(str(x).ljust(17) for x in d)
            print('     {}'.format(line))
            if line == 0:
                print('-' * len(line))
            sleep(0.25)
        print()
        sleep(1)

        return valid_scope
