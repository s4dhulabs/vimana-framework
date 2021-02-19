# -*- coding: utf-8 -*-
''' ~ Vimana Engine ~ '''

import sys
sys.path.insert(0, '../../../')

from termcolor import colored, cprint
from pathlib import Path
from time import sleep
import pathlib
import argparse
import os

# vimana core modules
from siddhis.dmt.dmt import siddhi as dmt_siddhi
from siddhis.djunch.djunch import siddhi as Djunch

from core.vmnf_fuzz_scope import handle_fuzz_scope
from core.vmnf_scope_parser import ScopeParser
from core.vmnf_urls_parser import digest_scope
from core.vmnf_arg_parser import VimanaParser
from core.vmnf_payloads import  VMNFPayloads 
from core.vmnf_manager import vmng


# vimana helpers 
from helpers.vmnf_helpers import VimanaHelp

# vimana resources
from resources import vmnf_banners 
from resources.vmnf_banners import s4dhu0nv1m4n4
from resources.colors import *

def abduct():
    # commands that require --module argument
    require_module = [
        'args', 'run', 'info' 
    ]

    # main commands help object
    vmnf_cmds = {
        'start':  VimanaHelp.start.__doc__, 
        'list' :  VimanaHelp.list.__doc__, 
        'run'  :  VimanaHelp.run.__doc__, 
        'info' :  VimanaHelp.info.__doc__,
        'args' :  VimanaHelp.args.__doc__,
        'about':  s4dhu0nv1m4n4(True)
    }

    arg_len = len(sys.argv[1:]) 
    cmd = str(sys.argv[1]).strip() if arg_len >= 1 else False

    # basic pre argparser validation (because thins started to get complex)
    if not cmd:
        VimanaHelp().basic_help()
        sys.exit(1)
    
    elif arg_len == 1:
        if cmd in vmnf_cmds.keys():
            print("\033c", end="")
            if cmd != 'about':
                print(VimanaHelp().__doc__)
            print(vmnf_cmds[cmd])
            sys.exit(1)

        if cmd != '--help':
            VimanaHelp().basic_help()
            sys.exit(1)
    
    elif arg_len > 1 \
        and cmd not in vmnf_cmds:
        VimanaHelp().basic_help()
        sys.exit(1)
    
    elif arg_len > 1 \
        and cmd in require_module \
        and len(sys.argv[2:]) == 1 \
        and sys.argv[2] == '--module':
        print(vmnf_cmds[cmd])
        sys.exit(1)
    
    vmn_parser = VimanaParser()
    handler_ns = vmn_parser.start_handler()
    
    if not handler_ns:
        print('[vmnf_engine] Something went wrong during scope validation. Check syntax and try again')
        sys.exit(1)

    # run Vimana in interactive mode (step by step)
    if handler_ns.start:
        print('Wait future releases for this feature. [:')

    # show module args
    elif handler_ns.module_args:
        vmng(**vars(handler_ns))  

    # run module
    elif handler_ns.module_run:
        if sys.argv[-1] != handler_ns.module_run:
            vmnf_banners.load()
            vmnf_banners.default_vmn_banner()
        
        handler_ns.scope = ScopeParser(**vars(handler_ns)).parse_scope()
        vmng(**vars(handler_ns))  

    # list modules
    elif handler_ns.module_list:            
        vmng(**vars(handler_ns))  

    # retrieve module information
    elif handler_ns.module_info:
        vmng(**vars(handler_ns))  
    
    # start only fuzzer directly
    elif handler_ns.fuzzer:
        scope = handle_fuzz_scope(**vars(handler_ns))
    
    # start discovery
    elif handler_ns.discovery:
        print('Wait future releases for this feature. [:')

    # list available payloads
    elif handler_ns.list_payloads:
        VMNFPayloads()._vmnfp_payload_types_(False,True)

        
        """
        vmnf_payloads = {}
        [vmnf_payloads.__setitem__(payload, getattr(_payloads_, payload).__doc__) \
            for payload in [attr for attr in dir(_payloads_) \
                if not attr.startswith('_')
	    ]
        ]
        
        print("\033c", end="") 
        print('\n\t {}'.format(
            colored('⣷⣒⠂    ', 'green')) + colored(' Vimana Payloads (v0.1)', 'magenta', attrs=[]) +\
            colored('    ⣸⣼⡀', 'green') + '\n\n'
        )

        for k,v in vmnf_payloads.items():
            print('{}{}:\t   \x1B[3m{}\x1B[23m'.format(
                    (' ' * int(5-len(k) + 14)),
                    colored(k,'cyan'),colored(v, 'green')
                )
            )
        print('\n\n')
        """
