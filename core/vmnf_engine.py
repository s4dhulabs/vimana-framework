# -*- coding: utf-8 -*-
''' ~ Vimana Engine ~ '''

import sys
sys.path.insert(0, '../../../')

from core.vmnf_smng import VFManager as vfmng

from res.vmnf_validators import get_tool_scope as get_scope
from neotermcolor import cprint, colored as cl
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
from core.vmnf_engine_exceptions import engineExceptions
from core.vmnf_fuzz_scope import handle_fuzz_scope
from core.vmnf_utils import pshell_set as vfutils
from core.vmnf_scope_parser import ScopeParser
from core.vmnf_urls_parser import digest_scope
from core.vmnf_arg_parser import VimanaParser
from core.vmnf_payloads import  VMNFPayloads 
from core.vmnf_dscan import DockerDiscovery
from core.vmnf_sessions import VFSession
from core.vmnf_cases import CasManager
from core.vmnf_scans import VFScan
from core.vmnf_rrunner import *

# vimana helpers 
import res.vmnf_validators as validator

# vimana resources
from core.vmnf_asserts import vmnf_cmds,require_module
from helpers.vmnf_helpers import VimanaHelp
from .vmnf_asserts import vfasserts
from res.vmnf_banners import vmn05
from res import vmnf_banners 
from res.colors import *


def abduct():
    arg_len = len(sys.argv[1:]) 
    cmd = str(sys.argv[1]).strip() if arg_len >= 1 else False
    aux = str(sys.argv[2]).strip() if arg_len >= 2 else False
    
    if not cmd:
        VimanaHelp().basic_help()
        sys.exit(1)

    elif arg_len == 1:
        if cmd in vmnf_cmds.keys():
            if cmd != 'about':
                vmn05()

            print(vmnf_cmds[cmd])
            sys.exit(1)
        else:
            pass

        if cmd != '--help':
            VimanaHelp().basic_help()
            sys.exit(1)
    
    elif arg_len > 1:
        if cmd not in vmnf_cmds:
            VimanaHelp().basic_help()
            sys.exit(1)
        else:
            if aux and aux in ['-h', '--help']:
                vmn05()
                print(vmnf_cmds[cmd])
                sys.exit(1)
            else:
                # vimana run --help     shows help about the command run itself
                pass

    elif arg_len > 1 \
        and cmd in require_module \
        and len(sys.argv[2:]) == 1 \
        and sys.argv[2] == '--module':

        print(vmnf_cmds[cmd])
        sys.exit(1)
    
    vmn_parser = VimanaParser()
    
    try:
        handler_ns = vmn_parser.start_handler()
    except TypeError as ArgError:
        engineExceptions(sys.argv, ArgError).unexpected_keyword()
        sys.exit(1)

    # runner doesn't require validations 
    if handler_ns.runner_mode:
        vfmng(**vars(handler_ns)).run_siddhi()
        
        return True

    if (handler_ns.module_run)\
        and handler_ns.module_run \
        not in _siddhis_.get("list"):

        print(f"\n  Plugin {cl(handler_ns.module_run, 'red')} doesn't exist. Available plugins:\n")

        [cprint('   ' + s, 'blue') \
                for s in _siddhis_.get("list")]
        print()
        sys.exit(1)

    # set case load flag
    run_from_case = False
    case_args = sys.argv

    if len(sys.argv[1:]) == 2:
        if cmd == 'run' \
            and sys.argv[2] \
            not in ['--module','--flush-cases']:
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
        return False

    #~ load session
    elif handler_ns.load_session:
        VFSession(**vars(handler_ns)).load_session(handler_ns.load_session)
    
    #~ load siddhis (inital vf setup)
    elif handler_ns.load_plugins:
        vfmng(**vars(handler_ns)).load_siddhis()
        
    #~ list sessions
    elif handler_ns.list_sessions:
        VFSession(**vars(handler_ns)).list_sessions()

    #~ flush session
    elif handler_ns.flush_session:
        VFSession(**vars(handler_ns)).flush_session()
    
    #~ flush all sessions
    elif handler_ns.flush_sessions:
        VFSession(**vars(handler_ns)).flush_all_sessions()

    #~ list siddhis
    elif handler_ns.module_list:            
        vfmng(**vars(handler_ns)).list_siddhis()
    
    #~ retrieve siddhi information
    elif handler_ns.module_info:
        vfmng(**vars(handler_ns)).show_siddhi_info()
   
    #~ show siddhi guide
    elif handler_ns.module_guide:
        vfmng(**vars(handler_ns)).get_siddhi_guide()

    #~ start only fuzzer directly
    elif handler_ns.fuzzer:
        scope = handle_fuzz_scope(**vars(handler_ns))
    
    #~ start discovery
    elif handler_ns.discovery:
        print('Wait future releases for this feature. [:')

    #~ list payloads
    elif handler_ns.list_payloads:
        VMNFPayloads()._vmnfp_payload_types_(False,True)

    #~ list all cases
    elif handler_ns.list_cases:
        CasManager(False,handler_ns).list_cases()
 
    #~ list all scans
    elif handler_ns.list_scans:
        VFScan(**vars(handler_ns)).list_scans()

    #~ flush cases
    elif handler_ns.flush_cases:
        CasManager(False,handler_ns).flush_cases()
    
    # ~ run
    elif handler_ns.module_run:
        vfmng(**vars(handler_ns)).run_siddhi()



