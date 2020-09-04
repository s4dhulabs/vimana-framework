#!/usr/bin/env python



import os
import sys
from datetime import datetime
import socket
from time import sleep
from resources import colors
from resources.session.vmnf_proxies import _set_socks_
from siddhis._shared_settings_.__settings import common


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
        '''
        '''
        socket_obj = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        socket_obj.settimeout(0.3)
        result = socket_obj.connect_ex((self.target,int(self.port)))    # socks.SOCKS5Error - socket.timeout: timed out
        socket_obj.close()
        service = '*'

        _target_ = colors.Y_c  + self.target.strip() + colors.D_c
        _port_   = colors.Y_c  + self.port.strip() + colors.D_c
        
        if result == 0:
            _status_ = str(colors.Gn_c + "Open" + colors.D_c)

            try:
                service = socket.getservbyport(int(self.port))
            except socket.error:
                pass
            
            result = self.port
        else:
            _status_ = colors.Rn_c + "Closed" + colors.D_c
            result = None

        self.t.append(_target_)
        self.p.append(_port_)
        self.s.append(_status_)

        return result 

    def start_scan(self):
        open_ports = []
        valid_scope = []
        closed_ports = []
        
        print("{} Validating port state for target {}{}{}...\n".format(
            colors.Gn_c + "⠿⠥" + colors.C_c,
            colors.Y_c, 
            self.target, 
            colors.D_c
            )
        )
        sleep(1) 

        for port in self.port_list:
            self.port = str(port).strip()
            port_status = self.check_port_status()
            if port_status is None:
                closed_ports.append(port)
                continue
            else:
                valid_scope.append(str(self.target + ':' + port_status))

        gen_status = list(zip(self.p,self.s))

        for i, d in enumerate(gen_status):
            #line = ' '.join(str(x).ljust(25) for x in d)
            line = ' '.join(str(x).ljust(17) for x in d)
            print('     {}'.format(line))
            if line == 0:
                print('-' * len(line))
            sleep(0.25)
        print()
        sleep(1)

        return valid_scope

