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
        self.proxy_set = vmnf_handler['proxy']
    
    def test_conn(self):
        # parse proxy

        if self.proxy_set:
            self.parse_proxy()

            if self.proxy_ip and self.proxy_port:
                socks.set_default_proxy(
                    socks.SOCKS5, 
                    str(self.proxy_ip), 
                    int(self.proxy_port)
                )
                socket.socket = socks.socksocket

                try:
                    conn_test = requests.get('https://ifconfig.me/ip')
                    if conn_test and conn_test is not None:
                        return conn_test 
                except requests.exceptions.ConnectionError as _ce_:
                    return False
        else:
            return self.proxy_set
        
    def parse_proxy(self):
        
        self.proxy_ip = False
        self.proxy_port = False

        if self.proxy_set:
            self.proxy_set = self.proxy_set.rstrip().lower()
            if ':' in self.proxy_set:
                self.proxy_ip, self.proxy_port = self.proxy_set.split(':')

                if not self.proxy_ip and not self.proxy_port:
                    print('[scope_validate] Invalid proxy format. Enter as follows: --proxy ip:port')
                    return False

            elif self.proxy_set == 'default':
                self.proxy_ip = '127.0.0.1'
                self.proxy_port = '9050'

            elif self.proxy_set \
                and not ':' in self.proxy_set \
                and self.proxy_set.count('.') == 3:
                self.proxy_ip = self.proxy_set
                self.proxy_port = '9050'
                # also have to check it better - if a valid ip format

