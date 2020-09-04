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

        self.socks_ip = socks_ip
        self.socks_port = socks_port
        
        socks.set_default_proxy(
            socks.SOCKS5, 
            str(socks_ip), 
            int(socks_port)
        )
        socket.socket = socks.socksocket

    def test_conn(self):
        try:
            conn_test = requests.get('https://ifconfig.me/ip')
            return conn_test
        except requests.exceptions.ConnectionError as _ce_:
            return None

