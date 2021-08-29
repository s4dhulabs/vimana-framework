import os
import random
import secrets
from datetime import datetime
from random import randint, choice
import mimesis
import base64


class VMNFPayloads:
    def __init__(self, **settings):
        '''VMNF Payloads'''

        self.settings = settings
        self.patterns = settings['patterns']
    
    def get_random_int(self):
        return randint(0, 
            choice(range(datetime.now().minute + datetime.now().second + len(self.patterns) * choice(bytes(range(256))))))
    def get_random_unicode(self):
        return choice(''.join(tuple(chr(i) for i in range(32, 0x110000) if chr(i).isprintable())))
    def get_os_urandom(self):
        return os.urandom(choice(range(18)))
    def get_secure_random_string(self):
        return secrets.token_urlsafe(choice(range(33)))
    def get_random_float(self):
        return random.random()
    def get_random_credential(self):
        gen = mimesis.Generic(choice([loc for loc in mimesis.locales.LIST_OF_LOCALES]))
        return {'username':gen.person.username(),'password':gen.person.password()}
    def get_ssti_payloads(self):
        with open('resources/attack/payloads/ssti.txt') as f:
            return [p.strip() for p in f.readlines()[1:]]
    def get_xss_payloads(self):
        with open('resources/attack/payloads/xss.txt') as f:
            return [p.strip() for p in f.readlines()[1:]]
    def get_sqli_payloads(self):
        with open('resources/attack/payloads/sqli.txt') as f:
            return [p.strip() for p in f.readlines()[1:]]
