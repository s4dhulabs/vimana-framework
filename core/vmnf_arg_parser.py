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

from res.vmnf_banners import vmn07
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
        '''
        start_cmd.add_argument('-s','--start', default=False, action='store_true', 
	    help='Start Vimana in interactive mode (default)'
        )
        '''
        start_cmd.add_argument('--start-resource', action='store_true',dest='start_resource')
        start_cmd.add_argument('--collections', action='store_true',dest='start_collections')
        start_cmd.add_argument('--sessions', action='store_true',dest='start_sessions')
        start_cmd.add_argument('--plugins', action='store_true',dest='start_plugins')
        start_cmd.add_argument('--tools', action='store_true',dest='start_tools')
        start_cmd.add_argument('--scans', action='store_true',dest='start_scans')
        start_cmd.add_argument('--cases', action='store_true',dest='start_cases')

        # -----------------------------------------------------------------
        # `help` command overview 
        # -----------------------------------------------------------------
        # vf help --module <module_name>
        # -----------------------------------------------------------------         
        #help_cmd = subparsers.add_parser('help', add_help=False, dest='help_cmd')

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
        list_cmd.add_argument('--scans', action='store_true',dest='list_scans')
        list_cmd.add_argument('--channels', action='store_true',dest='list_channels')
        list_cmd.add_argument('--summary', action='store_true', dest='channels_summary', help='Show channels in compact summary format')
        list_cmd.add_argument('--channel-type', action='store', dest='channel_type', help='Filter channels by type (RCE, File Write, etc.)')
        list_cmd.add_argument('--channel-plugin', action='store', dest='channel_plugin', help='Filter channels by plugin name')
        list_cmd.add_argument('--channel-target', action='store', dest='channel_target', help='Filter channels by target URL')
        list_cmd.add_argument('--channel-status', action='store', dest='channel_status', help='Filter channels by status (active, verified, etc.)')
        list_cmd.add_argument('-i', '--interactive', action='store_true', dest='navigation_mode')
        list_cmd.add_argument('--nav', action='store_true', dest='navigation_mode')
        list_cmd.add_argument('-t', '--type', action='store')
        list_cmd.add_argument('-c', '--category', action='store', dest='category')
        list_cmd.add_argument('-f', '--framework', action='store', dest='framework')
        list_cmd.add_argument('-x', '--exploits', action='store_true')
        list_cmd.add_argument('--astt', action='store',dest='astt')
        list_cmd.add_argument('-ft', '--fancy-table', action='store_true')
        #list_cmd.add_argument('-p', '--payload',action='store',
	    #choices=('reverse-shell', 'bind-port', 'backdoor', 'exfiltration-server')
        #)

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
        flush_cmd.add_argument('--channel', action='store', dest='flush_channel')
        flush_cmd.add_argument('--channels', action='store_true', dest='flush_channels')
        # -----------------------------------------------------------------
        # `load` command overview 
        # -----------------------------------------------------------------
        # vf load --plugins
        # vf load --session <session_id>
        # -----------------------------------------------------------------
        load_cmd = subparsers.add_parser('load', add_help=False)
        load_cmd.add_argument('--session', action='store', dest='load_session') 
        load_cmd.add_argument('--plugins', action='store_true', dest='load_plugins') 
        load_cmd.add_argument('--case', action='store', dest='load_case') 
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
        run_cmd.add_argument('--origin', action='store', dest='origin', default='engine')
        run_cmd.add_argument('--abduct', action='store', dest='abduct_file')
        run_cmd.add_argument('--save-case', action='store', dest='save_case')
        #run_cmd.add_argument('--case', action='store', dest='load_case')
        #run_cmd.add_argument('--case', action='store', dest='case_file')
        run_cmd.add_argument('--flush-cases', action='store_true', dest='flush_cases')
        run_cmd.add_argument('-m','--module', action='store', dest='module_run')
        run_cmd.add_argument('--siddhi', action='store', dest='module_run')
        run_cmd.add_argument('-p','--plugin', action='store', dest='module_run')
        run_cmd.add_argument('--fuzzer', action='store_true')
        #run_cmd.add_argument('--discovery', action='store_true')
        run_cmd.add_argument('--fingerprint', action='store_true')
        run_cmd.add_argument('--exec-case', action='store_true', default=False)
        run_cmd.add_argument("--exit-on-trigger", action="store_true", dest='exit_on_trigger')
        run_cmd.add_argument("--disable-external", action="store_true", dest='external_disabled')
        run_cmd.add_argument("--vf-debugger", action="store_true", dest='vf_debugger')
        run_cmd.add_argument('-i', '--interactive', action='store_true', dest='navigation_mode')
        run_cmd.add_argument('plugin_name', nargs='?', default=None, help='Plugin name to run')
        run_cmd.add_argument('--workflow', action='store', nargs='?', default=False, dest='workflow')
        run_cmd.add_argument('--channel', action='store', nargs='?', default=False, dest='cmd_channel')
        #run_cmd.add_argument('--cmd', action='store', nargs='?', default=False, dest='cmd')
        #run_cmd.add_argument('--pycode', action='store', nargs='?', default=False, dest='pycode')

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
        # 'show' command overview 
        # -----------------------------------------------------------------
        # vf show --channel <channel_name>
        # -----------------------------------------------------------------
        show_cmd = subparsers.add_parser('show',
            help='Show information about Vimana resources'
        )
        show_cmd.add_argument('-c', '--channel',action='store',dest='show_channel')
        show_cmd.add_argument('--compact', action='store_true', dest='show_compact', help='Show channel details in compact format')

        
        # -----------------------------------------------------------------
        # 'db' command overview 
        # -----------------------------------------------------------------
        # vf db --channel <channel_name>
        # -----------------------------------------------------------------
        db_cmd = subparsers.add_parser('dbops',
            help='CLI Database operations'
        )
        db_cmd.add_argument('-r', '--reset',action='store_true',dest='db_reset')
        db_cmd.add_argument('-l', '--list',action='store_true',dest='db_list')
        db_cmd.add_argument('--integrity-check',action='store_true',dest='db_integrity_check')
        #db_cmd.add_argument('-c', '--clear',action='store_true',dest='db_clear')
        #db_cmd.add_argument('-s', '--show',action='store',dest='db_show')
        #db_cmd.add_argument('-a', '--add',action='store',dest='db_add')
        #db_cmd.add_argument('-d', '--delete',action='store',dest='db_delete')
        #db_cmd.add_argument('-u', '--update',action='store',dest='db_update')
        #db_cmd.add_argument('-r', '--rename',action='store',dest='db_rename')
        
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
        guide_cmd.add_argument('-c', '--color',action='store_true',dest='color_enabled')
        guide_cmd.add_argument('--colors',action='store_true',dest='color_enabled')
        
        guide_cmd = subparsers.add_parser('guides',
            help='Show usage examples'
        )
        guide_cmd.add_argument('-m', '--module',action='store',dest='module_guide')
        guide_cmd.add_argument('-p', '--plugin',action='store',dest='module_guide')
        guide_cmd.add_argument('-a', '--args',action='store_true',dest='guide_args')
        guide_cmd.add_argument('-e', '--examples',action='store_true',dest='guide_examples')
        guide_cmd.add_argument('-l', '--labs',action='store_true',dest='guide_labs')
        guide_cmd.add_argument('-c', '--color',action='store_true',dest='color_enabled')
        guide_cmd.add_argument('--colors',action='store_true',dest='color_enabled')
        # -----------------------------------------------------------------
        # `create` command overview 
        # -----------------------------------------------------------------
        # vf create --env/--environment/--project/--workspace/--variable/--var
        # -----------------------------------------------------------------
        create_cmd = subparsers.add_parser('create',
            parents=[VimanaSharedArgs().args()],
            add_help=False
        )
        # add aditional arguments to complement shared args
        create_cmd.add_argument('--env', action='store_true', dest='create_env', default=False)
        create_cmd.add_argument('--environment', action='store_true', dest='create_env', default=False)
        create_cmd.add_argument('--project', action='store', dest='create_project', default=False)
        create_cmd.add_argument('--workspace', action='store', dest='create_workspace', default=False)

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
            astt            = False,
            exploits        = False,
            fancy_table     = False,
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
            color_enabled   = False,
            module_run      = False,
            siddhi_run      = False,
            plugin_run      = False,
            external_disabled = False,
            module_list     = False,
            list_payloads   = False,
            create_env      = False,
            list_cases      = False,
            list_sessions   = False,
            list_scans      = False,
            navigation_mode = False,
            navi            = False,
            save_case       = False,
            load_case       = False,
            runner_mode     = False,
            runner_tasks    = False,
            docker_scope    = False,
            exit_on_trigger = False,
            vf_debugger     = False,
            load_session    = False,
            load_plugins    = False,
            list_channels   = False,
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
            project_dir     = False,
            flush_channel   = False,
            flush_channels  = False,
            show_channel    = False,
            channel_type    = False,
            channel_plugin  = False,
            channel_target  = False,
            channel_status  = False,
            workflow        = False,
            channels_summary = False,
            show_compact    = False,
            cmd             = False,
            pycode          = False,
            help_cmd        = False,
            db_reset        = False,
            db_list         = False,
            db_clear        = False,
            db_show         = False,
            db_add          = False,
            db_delete       = False,
            db_update       = False,
            db_rename       = False,
            db_integrity_check = False
        )

        if len(sys.argv) > 1:
            _cmd_ = sys.argv[1]

        if (sys.argv[-1]) in _ap_['require_args']:
            if sys.argv[-1] in arg_help.keys():
                vmn05()
                print(arg_help[sys.argv[-1]])
            
            vmn07()
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

        elif _cmd_ == 'about':
            VimanaHelp().basic_help()
            sys.exit(1)
        
        elif _cmd_ == 'run':
            m_args = [a for a in sys.argv if a in _ap_['require_args'] 
                and sys.argv[sys.argv.index(a) + 1].startswith('-')
            ]

            if m_args:
                for a in m_args:
                    print(f"{a} requires a value")

                sys.exit(1)
        
        try: 
            vmn_options = self.parse_args()
        except argparse.ArgumentError as ArgError:
            engineExceptions(sys.argv, ArgError).argument_error()

        try:
            handler_ns.args = vmn_options.parse_known_args(
                namespace=handler_ns)[1]
        except UnboundLocalError:
            return False    

        return handler_ns






