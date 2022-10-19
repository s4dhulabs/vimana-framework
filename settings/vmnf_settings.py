import socks

common_secrets_re='res/regex/secrets.txt'
common_credskw = 'res/keywords/creds.txt'
common_sqlkw = 'res/keywords/sql.txt'
common_pyvars = 'res/pyvars/common_vars.txt'
ssti_p = 'res/attack/payloads/ssti.txt'
xss_p  = 'res/attack/payloads/xss.txt'
sqli_p = 'res/attack/payloads/sqli.txt'
issues_ref = 'res/issues_dref.yaml' 

proxy_settings = {
    'default_proxy_type': 'SOCKS5',
    'default_proxy_ip': '127.0.0.1',
    'default_proxy_port': '9050',
    'default_http_proxy_port': '9080',
    'supported_proxy_types': [
        'SOCKS5',
        'SOCKS4',
        'HTTP'
    ]
}
proxy_types = {
    'SOCKS5':socks.SOCKS5,
    'SOCKS4':socks.SOCKS4,
    'HTTP'  :socks.HTTP
}
proxy_ports = {
    'SOCKS5': proxy_settings['default_proxy_port'],
    'SOCKS4': proxy_settings['default_proxy_port'],
    'HTTP'  : proxy_settings['default_http_proxy_port']
}
check_pub_ip = [
    'https://ifconfig.me/ip',
    'https://api.ipify.org/',
    'http://icanhazip.com',
    'https://ident.me',
    'http://ipecho.net/plain'
]



 
