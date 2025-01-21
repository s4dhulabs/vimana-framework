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

from argparse import SUPPRESS
from time import sleep
import argparse
import sys

sys.path.insert(0, '../../../')

from helpers.vmnf_helpers import VimanaHelp



class MyParser(argparse.ArgumentParser):
    def format_help(self):
        VimanaHelp().full_help()

class VimanaSharedArgs:
    '''
        Vimana Framework shared arguments
        =================================

        This class implements a method to shares common arguments
        with siddhi modules. 

        Usage example:

        # Import Vimana shared args Class
        from core.vmnf_shared_args import VimanaSharedArgs


        def siddhi_args_method(self):

            # This will invoke VimanaSharedArgs().args() method and return common arguments
            # to siddhi module parser as a parent arguments 
            siddhi_parser = argparse.ArgumentParser(
                parents=[VimanaSharedArgs().args()],
                add_help=False
            )

            # So you can insert your own modules arguments to parser  
            siddhi_parser.add_argument('--siddhi-argument1')
            siddhi_parser.add_argument('--siddhi-argument2')

            # And here will be all the arguments, siddhi own arguments and Vimana shared ones
            args = siddhi_parser.parse_args()

            # Show argparser Namepace
            print(args)

    '''

    def __init__(self):
        ''' ~ VIMANA SHARED ARGUMENTS ~ '''

    def args(self): 
        vmnf_shared_parser = MyParser(argparse.ArgumentParser(
            conflict_handler='resolve',
	    argument_default=SUPPRESS,
	    prog="Vimana shared args", 
            add_help=False,
	    formatter_class=argparse.RawDescriptionHelpFormatter)
        )

        # -------------------------------------------------------------------------------
        # > Scope setting - [ Target parser ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument('--runner-mode',action='store_true',dest='runner_mode',default=False)
        vmnf_shared_parser.add_argument('--runner-tasks',action='store_true',dest='runner_tasks',default=False)
        vmnf_shared_parser.add_argument('--multi-target',action='store_true',dest='multi_target',default=False)
        vmnf_shared_parser.add_argument('--docker-scope',action='store_true',dest='docker_scope',default=False)
        vmnf_shared_parser.add_argument('--endpoint-url',action='store',dest='endpoint_url',default=False)
        vmnf_shared_parser.add_argument('--target-dir',action='store',dest='target_dir',default=False)
        vmnf_shared_parser.add_argument('--target-url',action='store',dest='target_url',default=False)
        #vmnf_shared_parser.add_argument('--target',action='store',dest='target',default=False)
        vmnf_shared_parser.add_argument('--filename',action='store',dest='filename',default=False)
        vmnf_shared_parser.add_argument('-t','--target',action='store',dest='single_target',default=False)
        vmnf_shared_parser.add_argument('--file',action='store',dest='file_scope',default=False)
        vmnf_shared_parser.add_argument('--ip-range',action='store',dest='ip_range', default=False)
        vmnf_shared_parser.add_argument('--cidr-range',action='store',dest='cidr_range', default=False)
        vmnf_shared_parser.add_argument('--target-list',action='store',dest='list_target', default=False)
        vmnf_shared_parser.add_argument('--nmap-xml',action='store',dest='nmap_xml', default=False)
        vmnf_shared_parser.add_argument('--target-input',action='store',dest='target_input', default=False)
        vmnf_shared_parser.add_argument('--form-input-target',action='store',dest='target_input', default=False)
        # -------------------------------------------------------------------------------
        # > Scope setting - [ port parser ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--port",action="store",dest='single_port',default=False)
        vmnf_shared_parser.add_argument("--port-list",action="store",nargs='+',dest='port_list',default=False)
        vmnf_shared_parser.add_argument("--port-range",action="store",dest='port_range',default=False)
        vmnf_shared_parser.add_argument('--ignore-state',action='store_true',dest='ignore_state',default=False)
        # -------------------------------------------------------------------------------
        # > Analysis - [ configuration options ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--debug",action="store_true",default=False)
        vmnf_shared_parser.add_argument("--verbose", '-v', action='count', default=False)
        vmnf_shared_parser.add_argument("--random", action="store_true",default=False)
        vmnf_shared_parser.add_argument("--wait", action="store", default=False)      
        vmnf_shared_parser.add_argument("--threads",action="store", type=int, default=10)
        vmnf_shared_parser.add_argument("--timeout", action="store", type=int, default=5)
        vmnf_shared_parser.add_argument("--pause-steps", action="store_true",default=False) 
        vmnf_shared_parser.add_argument("--auto", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--sample", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--xscope", action="store_true", dest='extended_scope',default=False)        
        vmnf_shared_parser.add_argument("--extended-scope", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--tracker-scope", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--disable-cache", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--ignore-cache", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--agressive", action="store_true",dest='agressive_mode',default=False)        
        vmnf_shared_parser.add_argument("--slow", action="store_true", dest='slow_mode',default=False)        
        vmnf_shared_parser.add_argument('--search-issues',action='store_true',dest='search_issues',default=False)
        vmnf_shared_parser.add_argument('--fuzzspec',action='store',dest='fuzzerspec_enabled',default=False)
        vmnf_shared_parser.add_argument('--fuzzspec-file',action='store',dest='use_fuzzerspec_file',default=False)
        vmnf_shared_parser.add_argument('-cv','--custom-variations',action='store',dest='fuzzer_custom_variations',type=int, default=3)
        vmnf_shared_parser.add_argument('--verbose-logging',action='store_true',dest='verbose_logging',default=False)
        vmnf_shared_parser.add_argument('--debug-logging',action='store_true',dest='debug_logging',default=False)
        vmnf_shared_parser.add_argument('--schemavalidate',action='store_true',dest='schema_validate',default=False)
        vmnf_shared_parser.add_argument('--show-response',action='store_true',dest='show_response',default=False)
        vmnf_shared_parser.add_argument('--describe',action='store_true',dest='describe_mode_enabled',default=False)
        # -------------------------------------------------------------------------------
        # > Scope setting - [ scope parser options ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--console-pin", action="store", dest='console_pin',default=False)
        vmnf_shared_parser.add_argument("--urlconf", action="store", dest='url_conf',default=False)
        vmnf_shared_parser.add_argument("--patterns", action="store", dest='patterns_file',default=False)
        vmnf_shared_parser.add_argument("--view-name", action="store", dest='view_name',default=False)
        vmnf_shared_parser.add_argument("--passwords", action="store", dest='passwords_file',default=False)
        vmnf_shared_parser.add_argument("--usernames", action="store", dest='usernames_file',default=False)
        vmnf_shared_parser.add_argument("--django-version", action="store", dest='django_version',default=False)
        vmnf_shared_parser.add_argument("--flask-version", action="store", dest='flask_version',default=False)
        vmnf_shared_parser.add_argument("--tornado-version", action="store", dest='tornado_version',default=False)
        vmnf_shared_parser.add_argument("--web2py-version", action="store", dest='web2py_version',default=False)
        vmnf_shared_parser.add_argument("--framework-version", action="store", dest='framework_version',default=False)
        vmnf_shared_parser.add_argument("--search-version", action="store", dest='framework_search_version',default=False)
        vmnf_shared_parser.add_argument("--issues-table", action="store_true", dest='issues_table',default=False)
        vmnf_shared_parser.add_argument("--table", action="store_true", dest='output_table',default=False)
        vmnf_shared_parser.add_argument("-ot","--output-table", action="store_true", dest='output_table',default=False)
        vmnf_shared_parser.add_argument("--text", action="store_true", dest='output_text',default=False)
        vmnf_shared_parser.add_argument("--framework", action="store", dest='framework',default=False)
        vmnf_shared_parser.add_argument("--project-dir", action="store", dest='project_dir',default=False)
        vmnf_shared_parser.add_argument("--data", action="store", dest='data_set',default=False)
        vmnf_shared_parser.add_argument("--use-request", action="store", dest='request_data_set',default=False)
        vmnf_shared_parser.add_argument("--object", action="store", dest='filter_by_objects',default=False)
        vmnf_shared_parser.add_argument("--plugin-target", action="store", dest='set_plugin_target',default=False)
        # -------------------------------------------------------------------------------
        # > Connection setting - [ proxy options ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--set-proxy", action="store_true", dest='set_proxy', default=False)
        vmnf_shared_parser.add_argument("--proxy", action="store", default=False)
        vmnf_shared_parser.add_argument("--proxy-type", action="store", dest='proxy_type', default=False)
        # -------------------------------------------------------------------------------
        # > Payload, session settings
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--local-port",action="store",dest='local_port',default=False)
        vmnf_shared_parser.add_argument("--local-host",action="store",dest='local_host',default=False)
        vmnf_shared_parser.add_argument("--remote-port",action="store",dest='remote_port',default=False)
        vmnf_shared_parser.add_argument("--remote-host",action="store",dest='remote_port',default=False)
        vmnf_shared_parser.add_argument("--payload",action="store",dest='payload_type',default=False)
        vmnf_shared_parser.add_argument("--forward",action="store",dest='forward_session',default=False)
        vmnf_shared_parser.add_argument("--siddhi-call",action="store_true",dest='siddhi_call',default=False)
        vmnf_shared_parser.add_argument("--session-mode",action="store_true",dest='session_mode',default=False)
        vmnf_shared_parser.add_argument("--listener",action="store_true",dest='listener_mode',default=False)
        vmnf_shared_parser.add_argument("--auth",action="store_true",dest='auth_mode',default=False)
        vmnf_shared_parser.add_argument("--save-session",action="store_true",dest='save_session',default=False)
        vmnf_shared_parser.add_argument("--callback-session",action="store_true",dest='callback_session',default=False)
        vmnf_shared_parser.add_argument("--flask-pinstealer",action="store_true",dest='flask_pinstealer',default=False)
        vmnf_shared_parser.add_argument("--flask-consolehook",action="store_true",dest='flask_consolehook',default=False)
        vmnf_shared_parser.add_argument("--connect-back",action="store_true",dest='connect_back',default=False)

        vmnf_shared_parser.add_argument("--split-payload",action="store",dest='split_payload',default=False, type=int)
        vmnf_shared_parser.add_argument("--random-vars",action="store_true",dest='random_vars',default=False)
        vmnf_shared_parser.add_argument("--max-var-length",action="store",dest='max_var_length',default=False, type=int)
        # -------------------------------------------------------------------------------
        # > common plugin shared options
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--brute-force",action="store_true",dest='brute_force_mode',default=False)
        vmnf_shared_parser.add_argument("--discovery",action="store_true",dest='discovery_mode',default=False)
        vmnf_shared_parser.add_argument("--search",action="store",dest='search_mode',default=False)
        vmnf_shared_parser.add_argument("--dump",action="store",dest='dump_mode',default=False)
        vmnf_shared_parser.add_argument("--search-object",action="store",dest='search_object',default=False)
        vmnf_shared_parser.add_argument("--output-file",action="store",dest='output_file',default='scan_results.sarif')
        vmnf_shared_parser.add_argument("--cmd",action="store",dest='run_cmd',default=False)
        vmnf_shared_parser.add_argument("--read-file",action="store",dest='read_file',default=False)

        vmnf_shared_parser.add_argument("--package",action="store_true",dest='search_package',default=False)
        vmnf_shared_parser.add_argument("--class",action="store_true",dest='search_class',default=False)
        vmnf_shared_parser.add_argument("--subclass",action="store_true",dest='search_subclass',default=False)
        vmnf_shared_parser.add_argument("--attr",action="store_true",dest='search_attr',default=False)

        vmnf_shared_parser.add_argument("--double-encode",action="store_true",dest='double_encode',default=False)
        vmnf_shared_parser.add_argument("--single-encode",action="store_true",dest='single_encode',default=False)
        vmnf_shared_parser.add_argument("--no-encode",action="store_true",dest='no_encode',default=False)
        vmnf_shared_parser.add_argument("--sleep",action="store",dest='set_sleep',default=1)
        vmnf_shared_parser.add_argument("--show-details",action="store_true",dest='show_details',default=False)

        vmnf_shared_parser.add_argument("--flush-specs",action="store_true",dest='flush_specs',default=False)
        vmnf_shared_parser.add_argument("--flush-spec",action="store",dest='flush_spec',default=False)
        vmnf_shared_parser.add_argument("--list-specs",action="store_true",dest='list_specs',default=False)
        vmnf_shared_parser.add_argument("--list-paths",action="store_true",dest='list_paths',default=False)
        vmnf_shared_parser.add_argument("--list-op-ids",action="store_true",dest='list_op_ids',default=False)
        vmnf_shared_parser.add_argument("--list-opids",action="store_true",dest='list_op_ids',default=False) 
        vmnf_shared_parser.add_argument("--list-schemas",action="store_true",dest='list_schemas',default=False)
        vmnf_shared_parser.add_argument("--list-parameters",action="store_true",dest='list_parameters',default=False) 
        vmnf_shared_parser.add_argument("--list-response-codes",action="store_true",dest='list_response_codes',default=False) 
        vmnf_shared_parser.add_argument("--list-examples",action="store_true",dest='list_examples',default=False) 
        vmnf_shared_parser.add_argument("--list-tags",action="store_true",dest='list_tags',default=False) 
        vmnf_shared_parser.add_argument("--list-descriptions",action="store_true",dest='list_descriptions',default=False) 
        vmnf_shared_parser.add_argument("--list-description",action="store_true",dest='list_descriptions',default=False) 
        vmnf_shared_parser.add_argument("--list-response-headers",action="store_true",dest='list_response_headers',default=False) 

        vmnf_shared_parser.add_argument("--apispec",action="store",dest='apispec_enabled',default=False)
        vmnf_shared_parser.add_argument("--oas",action="store",dest='apispec_enabled',default=False)
        vmnf_shared_parser.add_argument("--path",action="store",dest='set_path_scope',default=False)
        vmnf_shared_parser.add_argument("--set-path",action="store",dest='set_path_scope',default=False)
        vmnf_shared_parser.add_argument("--set-parameter",action="store",dest='set_param_scope',default=False)
        vmnf_shared_parser.add_argument("--set-param",action="store",dest='set_param_scope',default=False)
        #vmnf_shared_parser.add_argument("--spec",action="store",dest='apispec_enabled',default=False)

        vmnf_shared_parser.add_argument("--inspect",action="store",dest='inspect',default=False)
        vmnf_shared_parser.add_argument("--highlight",action="store_true",dest='highlight_enabled',default=False)
        vmnf_shared_parser.add_argument("--api-fingerprint",action="store_true",dest='api_fingerprint',default=False)
        vmnf_shared_parser.add_argument("--methods",action="store",dest='filter_by_method',default=False)
        vmnf_shared_parser.add_argument("--method",action="store",dest='filter_by_method',default=False)
        vmnf_shared_parser.add_argument("--operation",action="store",dest='filter_by_opid',default=False)
        vmnf_shared_parser.add_argument("--operation-id",action="store",dest='filter_by_opid',default=False)
        vmnf_shared_parser.add_argument("--tags",action="store",dest='filter_by_tag',default=False)

        vmnf_shared_parser.add_argument("--export-body",action="store_true",dest='export_body',default=False)
        vmnf_shared_parser.add_argument("-nc","--no-colors",action="store_true",dest='colors_disabled',default=False)
        vmnf_shared_parser.add_argument("--pretty",action="store_true",dest='pretty_output',default=False)
        vmnf_shared_parser.add_argument("--app-scope",action="store_true",dest='app_scope',default=False)

        # -------------------------------------------------------------------------------
        # > Rules settings
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--use-rules",action="store_true",dest='rule_scan',default=False)
        vmnf_shared_parser.add_argument("--scan-rules",action="store_true",dest='rule_scan',default=False)
        vmnf_shared_parser.add_argument("--scan-rule",action="store_true",dest='rule_scan',default=False)
        vmnf_shared_parser.add_argument("--rule",action="store_true",dest='rule_scan',default=False)
        
        return vmnf_shared_parser

    def shared_help(self):
        
        '''
    [target]  

    --docker-scope      build scope from docker containers
    --target            defines a single target scope
    --file              defines a file with a target list
    --ip-range          defines ip range scope
    --cidr-range        defines cidr range scope
    --target-list       defines a target list (comma-separeted) scope
    --nmap-xml          defines the result of the nmap xml as a scope
        
    [port]

    --port              sets a single port scope
    --port-list         sets a port list scope
    --port-range        sets port range scope
    --ignore-state      ignore port status
        
    [general]

    --debug             enables debug information
    --verbose           enables verbose mode (incremental)
    --random            enables randominez for suported steps
    --wait              wait 'n' seconds between steps
    --threads           sets number of threads 
    --timeout           sets timeout 
    --pause-steps       pause between steps 
    --auto              assume yes for all subtasks

    [proxy] 

    --set-proxy         enables the default proxy for all requests: SOCKS5://127.0.0.1:9050
    --proxy             configures the proxy specified by the ip:port string
    --proxy-type        specifies the proxy protocol to be used (required --proxy option)

    '''        
 
