# -*- coding: utf-8 -*-

''' ~ Vimana Engine ~ '''

import sys
sys.path.insert(0, '../../../')


from res.vmnf_validators import get_tool_scope as get_scope
from neotermcolor import colored,cprint
from datetime import datetime
from pathlib import Path
from time import sleep
import subprocess
import argparse
import pathlib
import yaml
import os

# vimana core modules
from siddhis.dmt.dmt import siddhi as dmt_siddhi
from siddhis.djunch.djunch import siddhi as Djunch

from core.load_settings import _version_, _siddhis_, _cs_
from core.vmnf_fuzz_scope import handle_fuzz_scope
from core.vmnf_utils import pshell_set as vfutils
from core.vmnf_scope_parser import ScopeParser
from core.vmnf_urls_parser import digest_scope
from core.vmnf_arg_parser import VimanaParser
from core.vmnf_payloads import  VMNFPayloads 
from core.vmnf_dscan import DockerDiscovery
from core.vmnf_sessions import VFSession
from core.vmnf_cases import CasManager
from core.vmnf_manager import vmng
from core.vmnf_rrunner import *



# vimana helpers 
from helpers.vmnf_helpers import VimanaHelp
import res.vmnf_validators as validator

# vimana resources
from res import vmnf_banners 
from res.vmnf_banners import s4dhu0nv1m4n4,vmn05
from res.colors import *



def abduct():

    # commands that require --module argument
    require_module = [
        'args', 'run', 'info' 
    ]

    # main commands help object
    vmnf_cmds = {
        'about':  s4dhu0nv1m4n4(True),
        'args' :  VimanaHelp.args.__doc__,
        'flush':  VimanaHelp.flush.__doc__,
        'info' :  VimanaHelp.info.__doc__,
        'list' :  VimanaHelp.list.__doc__, 
        'load' :  VimanaHelp.list.__doc__, 
        'run'  :  VimanaHelp.run.__doc__, 
        'start':  VimanaHelp.start.__doc__
    }

    arg_len = len(sys.argv[1:]) 
    cmd = str(sys.argv[1]).strip() if arg_len >= 1 else False

    # basic pre argparser validation (because thins started to get complex)
    if not cmd:
        VimanaHelp().basic_help()
        sys.exit(1)
    
    elif arg_len == 1:
        if cmd in vmnf_cmds.keys():
            if cmd != 'about':
                vmn05()

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
    
    # runner doesn't require validations 
    if handler_ns.runner_mode:
        vmng(**vars(handler_ns))
        return 

    if (handler_ns.module_run)\
        and handler_ns.module_run \
        not in _siddhis_.get("list"):

        print(f"\n  Plugin {colored(handler_ns.module_run, 'red')} doesn't exist. Available plugins:\n")

        [cprint('   ' + s, 'blue') for s in _siddhis_.get("list")]
        print()
        sys.exit(1)

    # set case load flag
    run_from_case = False
    case_args = sys.argv
    if len(sys.argv[1:]) == 2:
        if cmd == 'run' \
            and sys.argv[2] \
            not in [
                '--module',
                '--flush-cases'
            ]:
            run_from_case = True

    elif len(sys.argv[1:]) == 3:
        if cmd == 'run' \
            and handler_ns.case_file:
            run_from_case = True
            case_args[2] = case_args[3]
            
    # running plugin/arguments from a saved case
    if run_from_case:
        exec_case = CasManager(False,handler_ns).get_exec_case(case_args)
        handler_ns = CasManager(exec_case,handler_ns).load_case()

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
    elif handler_ns.module_run\
        or handler_ns.abduct_file:

        if handler_ns.docker_scope:
            targets_ports_set = []

            handler_ns.docker_scope = DockerDiscovery()

            [targets_ports_set.extend(y) \
                for y in [x['target_list'] \
                    for x in handler_ns.docker_scope]
            ]

        if sys.argv[-1] != handler_ns.module_run:

            # save command line to a yaml
            if handler_ns.save_case:
                CasManager(False,handler_ns).save_case()

            # sample agile mode 
            if handler_ns.sample:
                print("\033c", end="")
                vmnf_banners.sample_mode(
                    colored('  sample mode   ','red', 'on_white', attrs=['bold'])
                )

            # when module arguments (main vimana argparser namespace) will be loaded by stager
            if not handler_ns.session_mode\
                and not handler_ns.sample:

                vmnf_banners.load(handler_ns.module_run,20)
                vmnf_banners.default_vmn_banner()
        
        # loading settings from abduct file
        if handler_ns.abduct_file:
            if not validator.check_file(handler_ns.abduct_file):
                return False

            with open(handler_ns.abduct_file) as file:
                abd_set = yaml.load(file, Loader=yaml.FullLoader)
                
                try:
                    vars(handler_ns).update(abd_set.get('abduct'))
                except TypeError:
                    print('\n[abduct]→ Malformed abd file: {}. Check it out and try again.\n'.format(
                        handler_ns.abduct_file
                        )
                    )
                    sys.exit(1)
        
        if not handler_ns.docker_scope:
            handler_ns.scope = ScopeParser(**vars(handler_ns)).parse_scope()
            targets_ports_set = get_scope(**vars(handler_ns))

        len_tps = len(targets_ports_set)
        handler_ns.multi_target = True if len_tps > 1 else False
        
        if handler_ns.multi_target:
            #runner_handler=vfutils(**vars(handler_ns)).build_runner_scope(sys.argv)
            
            handler_ns.args = sys.argv
            handler_ns.runner = "python3 vimana.py run"
            handler_ns.runner_mode  = True
            handler_ns.runner_tasks = targets_ports_set

            rudrunner(handler_ns)

            return True 

        try:
            handler_ns.target_url = targets_ports_set[0]
        except IndexError: 
            vmn05()
            cprint("\n\t\t >> Missing scope!\n\n", 'red')

            sys.exit(1)


        vmng(**vars(handler_ns))  


    # load session
    elif handler_ns.load_session:
        VFSession(**vars(handler_ns)).load_session(handler_ns.load_session)

    # list sessions
    elif handler_ns.list_sessions:
        VFSession(**vars(handler_ns)).list_sessions()

    # flush session
    elif handler_ns.flush_session:
        VFSession(**vars(handler_ns)).flush_session()

    elif handler_ns.flush_sessions:
        VFSession(**vars(handler_ns)).flush_all_sessions()

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

    # list available cases
    elif handler_ns.list_cases:
        CasManager(False,handler_ns).list_cases()

    # flush cases
    elif handler_ns.flush_cases:
        CasManager(False,handler_ns).flush_cases()

        
