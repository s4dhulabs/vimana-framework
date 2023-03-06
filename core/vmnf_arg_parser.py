# -*- coding: utf-8 -*-


from neotermcolor import colored,cprint
from datetime import datetime
from time import sleep
import argparse
import sys
import os

sys.path.insert(0, '../../../')

from core.load_settings import _ap_
from core.vmnf_engine_exceptions import engineExceptions
from core.vmnf_shared_args import VimanaSharedArgs
from helpers.vmnf_helpers import VimanaHelp
from res.vmnf_banners import vmn05 




class MyParser(argparse.ArgumentParser):
    def format_help(self):
        VimanaHelp().full_help()

class VimanaParser:

    def __init__(self):
        ''' ~ Vimana General Argument Parser ~ '''

    def parse_args(self): 
        parser = MyParser(argparse.ArgumentParser(
            conflict_handler='resolve',
	    argument_default=argparse.SUPPRESS,
	    prog="Vimana", 
            add_help=False,
	    formatter_class=argparse.RawDescriptionHelpFormatter)
        )
        
        for group in parser._action_groups:
            if 'positional' in group.title:
                group.title = 'Vimana Commands'
    
        subparsers = parser.add_subparsers()   
        # -----------------------------------------------------------------
        # Vimana interactive mode 
        # -----------------------------------------------------------------
        # In this mode all required arguments and customizations 
        # will be set step by step, this also allows to configure
        # verbosity, threads, debug, realtime exception catcher etc      	
        # -----------------------------------------------------------------
        start_cmd = subparsers.add_parser('start', 
            help='Start Vimana in a interactive mode'
        )
        start_cmd.add_argument('-s','--start', default=True, action='store_true', 
	    help='Start Vimana in interactive mode (default)'
        )
    
        # -----------------------------------------------------------------
        # `list` command overview 
        # -----------------------------------------------------------------
        # vf list --modules -t/-c/-f [options] 
        # vf list --exploits [same of `vimana list --modules -t exploit`]
        # -----------------------------------------------------------------
        list_cmd = subparsers.add_parser('list', 
            help='List available resources'
        )
        list_cmd.add_argument('--payloads', action='store_true',dest='list_payloads')
        list_cmd.add_argument('--cases', action='store_true',dest='list_cases')
        list_cmd.add_argument('--sessions', action='store_true',dest='list_sessions')
        list_cmd.add_argument('--modules', action='store_true',dest='module_list')
        list_cmd.add_argument('--plugins', action='store_true',dest='module_list')
        list_cmd.add_argument('--siddhis', action='store_true',dest='module_list')
        list_cmd.add_argument('-t', '--type', action='store')
        list_cmd.add_argument('-c', '--category', action='store', dest='category')
        list_cmd.add_argument('-f', '--framework', action='store', dest='framework')
        list_cmd.add_argument('-x', '--exploits', action='store_true')
        list_cmd.add_argument('-p', '--payload',action='store',
	    choices=('reverse-shell', 'bind-port', 'backdoor', 'exfiltration-server')
        )
        # -----------------------------------------------------------------
        # `flush` command overview 
        # -----------------------------------------------------------------
        # vf flush --session <session_id>
        # vf flush --sessions --xray
        # vf flush --case <case_id>
        # vf flush --cases/--sessions
        # -----------------------------------------------------------------
        flush_cmd = subparsers.add_parser('flush', add_help=False)
        flush_cmd.add_argument('--sessions',action='store_true', dest='flush_sessions')
        flush_cmd.add_argument('--cases',action='store_true', dest='flush_cases')
        flush_cmd.add_argument('--session',action='store', dest='flush_session')
        flush_cmd.add_argument('--case',action='store', dest='flush_case')
        flush_cmd.add_argument('--show-details',action='store_true', dest='flush_details')
        flush_cmd.add_argument('--xray',action='store_true', dest='xray_enabled')
        flush_cmd.add_argument('--fastflush',action='store_true', dest='fastflush')
        
        
        # -----------------------------------------------------------------
        # `load` command overview 
        # -----------------------------------------------------------------
        # vf load --plugins
        # vf load --session <session_id>
        # -----------------------------------------------------------------
        load_cmd = subparsers.add_parser('load', add_help=False)
        load_cmd.add_argument('--session', 
            action='store', 
            dest='load_session', 
        ) 
        load_cmd.add_argument('--plugins', 
            action='store_true', 
            dest='load_plugins', 
        ) 

        # -----------------------------------------------------------------
        # `run` command overview 
        # -----------------------------------------------------------------
        # vf run --modules/--fuzzer/--discovery -t https://www.mypyapp.com [-f framewok]
        # -----------------------------------------------------------------
        run_cmd = subparsers.add_parser('run',
            parents=[VimanaSharedArgs().args()],
            add_help=False
        )
        # add aditional arguments to complement shared args
        run_cmd.add_argument('--abduct', action='store', dest='abduct_file')
        run_cmd.add_argument('--save-case', action='store', dest='save_case')
        run_cmd.add_argument('--case', action='store', dest='case_file')
        run_cmd.add_argument('--flush-cases', action='store_true', dest='flush_cases')
        run_cmd.add_argument('-m','--module', action='store', dest='module_run')
        run_cmd.add_argument('--siddhi', action='store', dest='module_run')
        run_cmd.add_argument('--plugin', action='store', dest='module_run')
        run_cmd.add_argument('--fuzzer', action='store_true')
        #run_cmd.add_argument('--discovery', action='store_true')
        run_cmd.add_argument('--fingerprint', action='store_true')
        run_cmd.add_argument('--exec-case', action='store_true', default=False)
        run_cmd.add_argument("--exit-on-trigger", action="store_true", dest='exit_on_trigger')
        run_cmd.add_argument("--disable-external", action="store_true", dest='external_disabled')
        # -----------------------------------------------------------------
        # 'info' command overview 
        # -----------------------------------------------------------------
        # vf info --module <module_name>
        # -----------------------------------------------------------------
        info_cmd = subparsers.add_parser('info',
            help='Show information about Vimana resources'
        )
        info_cmd.add_argument('-m', '--module',action='store',dest='module_info')
        info_cmd.add_argument('-s', '--siddhi',action='store',dest='module_info')
        info_cmd.add_argument('-p', '--plugin',action='store',dest='module_info')
        
        # -----------------------------------------------------------------
        # 'guide' command overview 
        # -----------------------------------------------------------------
        # vf guide --module <module_name> <options>
        # 
        # vf guide -m <module>              
        # vf guide -m <module> --examples
        # vf guide -m <module> --args
        # vf guide -m <module> --labs
        # -----------------------------------------------------------------
        guide_cmd = subparsers.add_parser('guide',
            help='Show usage examples'
        )
        guide_cmd.add_argument('-m', '--module',action='store',dest='module_guide')
        guide_cmd.add_argument('-p', '--plugin',action='store',dest='module_guide')
        guide_cmd.add_argument('-a', '--args',action='store_true',dest='guide_args')
        guide_cmd.add_argument('-e', '--examples',action='store_true',dest='guide_examples')
        guide_cmd.add_argument('-l', '--labs',action='store_true',dest='guide_labs')
        guide_cmd.add_argument('--highlight',action='store_true',dest='highlight_enabled')
        
        guide_cmd = subparsers.add_parser('guides',
            help='Show usage examples'
        )
        guide_cmd.add_argument('-m', '--module',action='store',dest='module_guide')
        guide_cmd.add_argument('-p', '--plugin',action='store',dest='module_guide')
        guide_cmd.add_argument('-a', '--args',action='store_true',dest='guide_args')
        guide_cmd.add_argument('-e', '--examples',action='store_true',dest='guide_examples')
        guide_cmd.add_argument('-l', '--labs',action='store_true',dest='guide_labs')
        # -----------------------------------------------------------------
        # 'arg' command overview / disabled on vimana v0.7 → guide cmd
        # ----------------------
        # vf arg --module <module_name>
        # -----------------------------------------------------------------
        args_cmd = subparsers.add_parser('args',
            help='Show module arguments'
        )
        args_cmd.add_argument('-m', '--module',action='store',dest='module_args')
        
        return parser

    def start_handler(self):
        
        mod_type_by_id = {
            0:'tracker',
            1:'fuzzer',
            2:'attack',
            3:'leaker',
            4:'exploit'
        }
        
        arg_help = {
            '--abduct':     VimanaHelp.abduct.__doc__,
            '--proxy':      VimanaHelp.proxy.__doc__, 
            '--proxy-type': VimanaHelp.proxy.__doc__, 
            '--target':     VimanaHelp.set_scope.__doc__,
            '--save-case':  VimanaHelp.save_case.__doc__
        }
        
        handler_ns  = argparse.Namespace(
            scope           = False,
            file_scope      = False,
            ip_range        = False,
            cidr_range      = False,
            single_target   = False,
            ignore_state    = False,
            port_list       = False,
            port_range      = False,
            single_port     = False,
            start           = False,
            abduct_file     = False,
            interactive     = False,
            type            = False,
            category        = False,
            exploits        = False,
            payload         = False,
            fuzzer          = False,
            discovery       = False,
            debug           = False,
            verbose         = False,
            module          = False,
            modules         = False,
            module_info     = False,
            module_guide    = False,
            guide_args      = False,
            guide_examples  = False,
            guide_labs      = False,
            highlight_enabled = False,
            module_run      = False,
            siddhi_run      = False,
            plugin_run      = False,
            external_disabled = False,
            module_list     = False,
            list_payloads   = False,
            list_cases      = False,
            list_sessions   = False,
            save_case       = False,
            case_file       = False,
            runner_mode     = False,
            runner_tasks    = False,
            docker_scope    = False,
            exit_on_trigger = False,
            vmnf_debugger   = False,
            load_session    = False,
            load_plugins    = False,
            flush_sessions  = False,
            flush_cases     = False,
            flush_session   = False,
            flush_case      = False,
            endpoint_url    = False,
            xray_enabled    = False,
            fastflush       = False,
            module_args     = False,
            framework       = False,
            url_conf        = False,
            view_name       = False,
            proxy           = False,
            proxy_type      = False,
            project_dir     = False
        )

        if len(sys.argv) > 1:
            _cmd_ = sys.argv[1]

        if (sys.argv[-1]) in _ap_['require_args']:
            if sys.argv[-1] in arg_help.keys():
                vmn05()
                print(arg_help[sys.argv[-1]])
            
            print(f"    \n[vmnf_argparser] Missing value for the argument {colored(sys.argv[-1], 'red')}\n\n")
            
            tools = [
                '--fuzzer',
                '--discovery'
            ]

            if sys.argv[-1] in tools:
                print(VimanaHelp().__doc__)
                print(VimanaHelp.fuzzer_args.__doc__)

            sys.exit(1)

        # trick to check some arguments before pass to argparser
        if _cmd_ == 'args' \
            and len(sys.argv[2:]) == 1:
            print(VimanaHelp.args.__doc__)
            sys.exit(1)
        if _cmd_ == 'about':
            VimanaHelp().basic_help()
            sys.exit(1)
        try: 
            vmn_options = self.parse_args()
        except argparse.ArgumentError as ArgError:
            engineExceptions(sys.argv, ArgError).argument_error()

        handler_ns.args = vmn_options.parse_known_args(
            namespace=handler_ns)[1]
        

        return handler_ns






