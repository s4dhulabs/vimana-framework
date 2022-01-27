# -*- coding: utf-8 -*-

from termcolor import colored,cprint
from datetime import datetime
import argparse
from time import sleep
import sys
import os

sys.path.insert(0, '../../../')

from helpers.vmnf_helpers import VimanaHelp
from core.vmnf_shared_args import VimanaSharedArgs
from core.vmnf_engine_exceptions import engineExceptions



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
        # ----------------------- 
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
        # 'list' command overview 
        # -----------------------
        # vimana list --modules -t/-c/-f [options] 
        # vimana list --exploits [same of `vimana list --modules -t exploit`]
        # -----------------------------------------------------------------
        list_cmd = subparsers.add_parser('list', 
            help='List available resources'
        )
        list_cmd.add_argument('--payloads', action='store_true',dest='list_payloads')
        list_cmd.add_argument('--cases', action='store_true',dest='list_cases')
        list_cmd.add_argument('--modules', action='store_true',dest='module_list')
        list_cmd.add_argument('-t', '--type', action='store')
        list_cmd.add_argument('-c', '--category', action='store', dest='category')
        list_cmd.add_argument('-f', '--framework', action='store', dest='framework')
        list_cmd.add_argument('-x', '--exploits', action='store_true')
        list_cmd.add_argument('-p', '--payload',action='store',
	    choices=('reverse-shell', 'bind-port', 'backdoor', 'exfiltration-server')
        )

        # -----------------------------------------------------------------
        # 'run' command overview 
        # ----------------------
        # vimana run --modules/--fuzzer/--discovery -t https://www.mypyapp.com [-f framewok]
        # -----------------------------------------------------------------
        run_cmd = subparsers.add_parser('run',
            parents=[VimanaSharedArgs().args()],
            add_help=False
        )
        # add aditional arguments to complement shared args
        run_cmd.add_argument('--abduct', action='store', dest='abduct_file')
        run_cmd.add_argument('--save-case', action='store', dest='save_case')
        run_cmd.add_argument('--module', action='store', dest='module_run')
        run_cmd.add_argument('--fuzzer', action='store_true')
        run_cmd.add_argument('--discovery', action='store_true')
        run_cmd.add_argument('--fingerprint', action='store_true')
        run_cmd.add_argument('--exec-case', action='store_true', default=False)
        
        # -----------------------------------------------------------------
        # 'info' command overview 
        # -----------------------
        # vimana info --module <module_name>
        # -----------------------------------------------------------------
        info_cmd = subparsers.add_parser('info',
            help='Show information about Vimana resources'
        )
        info_cmd.add_argument('-m', '--module-name',action='store',dest='module_info')
        
        # -----------------------------------------------------------------
        # 'arg' command overview 
        # ----------------------
        # vimana arg --module <module_name>
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
            '--abduct': VimanaHelp.abduct.__doc__,
            '--proxy':  VimanaHelp.proxy.__doc__, 
            '--proxy-type':  VimanaHelp.proxy.__doc__, 
            '--target': VimanaHelp.set_scope.__doc__,
            '--save-case': VimanaHelp.save_case.__doc__
        }

        required_args = [
            '--save-case',
            '--target',
            '--file',
            '--ip-range',
            '--cidr-range',
            '--target-list',
            '--port',
            '--port-list',
            '--port-range',
            '--fuzzer',
            '--proxy',
            '--proxy-type',
            '--nmap-xml',
            '--abduct'
        ]

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
            module_run      = False,
            module_list     = False,
            list_payloads   = False,
            list_cases      = False,
            save_case       = False,
            module_args     = False,
            framework       = False,
            url_conf        = False,
            view_name       = False,
            proxy           = False,
            proxy_type      = False
        )
        

        if len(sys.argv) > 1:
            _cmd_ = sys.argv[1]

        if (sys.argv[-1]) in required_args:
            if sys.argv[-1] in arg_help.keys():
                print(VimanaHelp().__doc__)
                print(arg_help[sys.argv[-1]])
            
            print('[vmnf_argparser: {}] Missing a value for the argument {}\n\n'.format(
                datetime.now(),
                sys.argv[-1]
                )
            )
            
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
        elif _cmd_ == 'about':
            print("aboutzz")

        try: 
            vmn_options = self.parse_args()
        except argparse.ArgumentError as ArgError:
            engineExceptions(sys.argv, ArgError).argument_error()

        handler_ns.args = vmn_options.parse_known_args(
            namespace=handler_ns)[1]
        
        return handler_ns






