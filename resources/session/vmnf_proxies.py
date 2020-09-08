
import settings.vmnf_settings as settings
import random
import requests
import socket
import socks
import sys


class _set_socks_:
    ''' This class implements proxy options for Vimana. 
    For now, only PySocks is available (https://pypi.org/project/PySocks/). Soon new options.
    '''

    def __init__(self,**vmnf_handler):
        
        self.vmnf_handler = vmnf_handler
        self.set_proxy = vmnf_handler['set_proxy']
        self.proxy = vmnf_handler['proxy']
        self.proxy_type = vmnf_handler['proxy_type']
        
        self.use_proxy = True if self.set_proxy \
            or self.proxy else False

        self.proxy_types = settings.proxy_types
        self.proxy_ports = settings.proxy_ports
        self.check_pub_ip= settings.check_pub_ip

        '''
        self.proxy_types = {
            'SOCKS5':socks.SOCKS5,
            'SOCKS4':socks.SOCKS4,
            'HTTP'  :socks.HTTP
        }
        self.proxy_ports = {
            'SOCKS5':'9050',
            'SOCKS4':'9050',
            'HTTP'  :'9080'
        }
        
        self.cpips = [
            'https://ifconfig.me/ip',
            'https://api.ipify.org/',
            'https://ident.me'
        ]
        '''
    def test_conn(self):
        # parse proxy

        if self.use_proxy: 
            if not (self.parse_proxy()):
                proxy_resp = False
                while not proxy_resp:
                    try:
                        proxy_resp = input('[proxy_validate] Proxy validation failed, do you want to proceed anyway? (y/N): ')
                        proxy_resp = proxy_resp.rstrip().lower()
                    except KeyboardInterrupt:
                        pass

                if proxy_resp == 'n':
                    sys.exit(1)
                elif proxy_resp == 'y':
                    return False

            if self.proxy_ip and self.proxy_port:
                socks.set_default_proxy(
                    self.proxy_type, 
                    str(self.proxy_ip), 
                    int(self.proxy_port)
                )
                socket.socket = socks.socksocket
                
                try:
                    conn_test = requests.get(random.choice(self.check_pub_ip))
                    if conn_test and conn_test is not None:
                        if conn_test.status_code == 200:
                            set_proxy_status={
                                'proxy_ip'  : self.proxy_ip,
                                'proxy_port': self.proxy_port,
                                'proxy_type': self._p2_,
                                'response'  : conn_test,
                                'socket'    : socket.socket
                            }
                            return set_proxy_status
                except requests.exceptions.ConnectionError as _ce_:
                    return False
        else:
            return False
        
    def parse_proxy(self):
        
        self.proxy_ip = False
        self.proxy_port = False
        
        # set default SOCKS5 proxy 
        if self.set_proxy:
            self.proxy_ip   = settings.proxy_settings['default_proxy_ip']
            self.proxy_type = self.proxy_types[settings.proxy_settings['default_proxy_type']]
            self.proxy_port = settings.proxy_settings['default_proxy_port']
            self._p2_       = settings.proxy_settings['default_proxy_type']
            
            return True

        # --proxy
        elif self.proxy:
            self.proxy = self.proxy.rstrip().lower()
            if ':' in self.proxy:
                self.proxy_ip, self.proxy_port = self.proxy.split(':')

                if not self.proxy_ip:
                    print('\n[proxy_validate] Missing host or port for proxy value. Enter as follows: --proxy ip:port')
                    return False

                # socks5, socks4, http
                if self.proxy_type:
                    self.proxy_type = self.proxy_type.rstrip().upper()

                    if self.proxy_type not in self.proxy_types.keys():
                        print('\n[proxy_validate] Invalid proxy type. Supported options:')
                        
                        print()
                        for k in self.proxy_types.keys():
                            print(' + {}\t{}'.format(k,self.proxy_ports[k]))
                        print()
                        return False

                    # pick proxy type port, ex: --proxy 127.0.0.1:9871 --proxy-type SOCKS
                    if not self.proxy_port:
                        self.proxy_port = self.proxy_ports[self.proxy_type]
                else:
                    self.proxy_type = 'SOCKS5'
                
                self._p2_ = self.proxy_type
                self.proxy_type = self.proxy_types[self.proxy_type]
                
                try: 
                    int(self.proxy_port)  
                except ValueError:
                    if not self.vmnf_handler['auto']:
                        print('\n[proxy_validate] Invalid port format: "{}". Enter as follows: --proxy 127.0.0.1:9050'.format(self.proxy_port))
                        return False

                    print('\n[proxy_validate] Auto correction, setting default port for the proxy: 9050'.format(self.proxy_port))
                    self.proxy_port = '9050'
                    return True
                    

                return True
            else:
                print('\n[proxy_validate] Invalid proxy format. Enter as follows: --proxy ip:port')
                return False

