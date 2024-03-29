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

import socks



LOCALES = [
    'cs', 'da', 'de', 'de-at', 'de-ch', 'el', 'en', 
    'en-gb', 'en-au', 'en-ca', 'es', 'es-mx', 'et', 
    'fa', 'fi', 'fr', 'hu', 'is', 'it', 'ja', 'kk', 
    'ko', 'nl', 'nl-be', 'no', 'pl', 'pt', 'pt-br', 
    'ru', 'sk', 'sv', 'tr', 'uk', 'zh'
]

common_url_patterns='res/patterns/url/common.txt'
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



 
