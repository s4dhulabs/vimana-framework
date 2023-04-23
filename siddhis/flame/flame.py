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


import sys
import collections
from time import sleep
from requests.exceptions import *
from neotermcolor import cprint,colored
from res.vmnf_validators import get_tool_scope
from core.vmnf_shared_args import VimanaSharedArgs

from ._flautils import test_target_connection
from ._flautils import get_html_content
from ._flautils import ex2tract 
from ._flautils import flamebann



class siddhi:
    def __init__(self,**vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.debug_msg = 'Werkzeug Debugger'
        self.debug_confirmation = 'friendly Werkzeug powered traceback interpreter.'
        self.pin_test_url = "{}/?__debugger__=yes&cmd=pinauth&pin={}&s={}"
    
    def start(self):
        flamebann()
        """
        print(f'''{Rn_c}
         (     (                *          
         )\ )  )\ )    (      (  `         
        (()/( (()/(    )\     )\))(   (    
         /(_)) /(_))((((_)(  ((_)()\  )\   
        (_))_|(_))   )\ _ )\ (_()((_)((_)  
        | |_  | |    (_)_\(_)|  \/  || __|  Flask 
        | __| | |__   / _ \  | |\/| || _|   Misconfigurations
        |_|   |____| /_/ \_\ |_|  |_||___|  Explorer
        {D_c} 

        ''')
        """

        if not self.vmnf_handler['scope'] \
                and not self.vmnf_handler['target_url']:

            print(VimanaSharedArgs().shared_help.__doc__)
            sys.exit(1)
       
        if self.vmnf_handler['scope']:
            targets_ports_set = get_tool_scope(**self.vmnf_handler)
            target_address = f'http://{targets_ports_set[0]}'
        else:
            target_address = self.vmnf_handler.get('target_url')
            
            if not target_address.startswith('http'):
                target_address = f'http://{target_address}'
        
        response = test_target_connection(target_address)

        if response.status_code == 500:
            _mode_ = 'frame'
        
            html, title, head = get_html_content(response)

            if (self.debug_msg) in title \
                and (self.debug_confirmation) in str(html):

                exception = ex2tract().get_exception_details(html)
                exception_frame = ex2tract().get_source(html,_mode_)
                exception = {
                    'exception': exception,
                    'exception_frame': exception_frame,
                    'response': response
                }

                if exception_frame:
                    ex2tract().show_exception_details(
                        target_address,
                        **exception
                )

