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

import os
import random
import secrets
from datetime import datetime
from random import randint, choice
import mimesis
import base64
import settings.vmnf_settings as settings


class VMNFPayloads:
    def __init__(self, **vmnf_handler):
        '''VMNF Payloads'''

        self.vmnf_handler = vmnf_handler
        self.patterns = vmnf_handler.get('patterns', 10)
    
    def enon(self):
        return ['None', '[¹→↓?']

    def get_random_int(self):
        return randint(0, 
            choice(range(datetime.now().minute \
            + datetime.now().second \
            + len(self.patterns) \
            * choice(bytes(range(256)))))
        )
    def get_random_unicode(self):
        return choice(''.join(tuple(chr(i)\
            for i in range(32, 0x110000) \
                if chr(i).isprintable()))
        )
    def get_os_urandom(self):
        return os.urandom(choice(range(18)))
    def get_secure_random_string(self):
        return secrets.token_urlsafe(choice(range(33)))
    def get_random_float(self):
        return random.random()
    def get_random_credential(self):
        gen = mimesis.Generic(
            choice([loc for loc in settings.LOCALES])
        )
        return {
            'username':gen.person.username(),
            'password':gen.person.password()
        }
    def get_ssti_payloads(self):
        with open(settings.ssti_p) as f:
            return [p.strip('\n') for p in f.readlines()[1:]]
    def get_xss_payloads(self):
        with open(settings.xss_p) as f:
            return [p.strip('\n') for p in f.readlines()[1:]]
    def get_sqli_payloads(self):
        with open(settings.sqli_p) as f:
            return [p.strip('\n') for p in f.readlines()[1:]]
    def get_pyvars(self):
        with open(settings.common_pyvars) as f:
            return [p.strip('\n') for p in f.readlines()[1:]]
    def get_sqlkw(self):
        with open(settings.common_sqlkw) as f:
            return [p.strip('\n') for p in f.readlines()]
    def get_credskw(self):
        with open(settings.common_credskw) as f:
            return [p.strip('\n') for p in f.readlines()]
    def get_secret_regex(self):
        with open(settings.common_secrets_re) as f:
            return [p.strip('\n') for p in f.readlines()[1:]]
    def get_common_url_patterns(self):
        with open(settings.common_url_patterns) as f:
            return [p.strip('\n') for p in f.readlines() if p]

