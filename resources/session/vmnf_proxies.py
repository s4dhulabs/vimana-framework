import requests
import socket
import socks
import sys


class _set_socks_:
    ''' This class implements proxy options for Vimana. 
    For now, only PySocks is available (https://pypi.org/project/PySocks/). Soon new options.
    '''

    def __init__(
        self,
        socks_ip=False,
        socks_port=False):

        if socks_ip and socks_port:
            socks.set_default_proxy(
                socks.SOCKS5, 
                str(socks_ip), 
                int(socks_port)
            )
            socket.socket = socks.socksocket

    def test_conn(self):
        try:
            conn_test = requests.get('https://ifconfig.me/ip')
            if conn_test is not None:
                return conn_test #print('[SOCKS5 OK] Exiting with IP {}'.format(str(conn_test.content)))
        except requests.exceptions.ConnectionError as _ce_:
            return None
        
    def parse_proxy(self, **vmnf_handler):
        
        # testing socks proxy support
        ip = ''
        port = ''
        proxy_set = False

        proxy_set = vmnf_handler['proxy']

        if proxy_set:
            proxy_set = proxy_set.rstrip().lower()
            if ':' in proxy_set:
                ip, port = proxy.set.split(':')

                if not ip and not port:
                    print('[scope_validate] Invalid proxy format. Enter as follows: --proxy ip:port')
                    return False

            elif proxy_set.lower() == 'default':
                ip = '127.0.0.1'
                port = '9050'

            elif proxy_set \
                and not ':' in proxy_set \
                and proxy_set.count('.') == 3:
                ip = proxy_set
                port = '9050'
                # also have to check it better - if a valid ip format
        else:
            return False

        return (ip + ':' + port) 




