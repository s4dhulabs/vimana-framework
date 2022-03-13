# -*- coding: utf-8 -*-

from argparse import SUPPRESS
import argparse
from time import sleep
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
        vmnf_shared_parser.add_argument('--endpoint-url',action='store',dest='endpoint_url',default=False)
        vmnf_shared_parser.add_argument('--target-dir',action='store',dest='target_dir',default=False)
        vmnf_shared_parser.add_argument('--target-url',action='store',dest='target_url',default=False)
        vmnf_shared_parser.add_argument('--filename',action='store',dest='filename',default=False)
        vmnf_shared_parser.add_argument('--target',action='store',dest='single_target',default=False)
        vmnf_shared_parser.add_argument('--file',action='store',dest='file_scope',default=False)
        vmnf_shared_parser.add_argument('--ip-range',action='store',dest='ip_range', default=False)
        vmnf_shared_parser.add_argument('--cidr-range',action='store',dest='cidr_range', default=False)
        vmnf_shared_parser.add_argument('--target-list',action='store',dest='list_target', default=False)
        vmnf_shared_parser.add_argument('--nmap-xml',action='store',dest='nmap_xml', default=False)
        # -------------------------------------------------------------------------------
        # > Scope setting - [ port parser ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--port",action="store",dest='single_port',default=False)
        vmnf_shared_parser.add_argument("--port-list",action="store",nargs='+',dest='port_list',default=False)
        vmnf_shared_parser.add_argument("--port-range",action="store",dest='port_range',default=False)
        vmnf_shared_parser.add_argument('--ignore-state',action='store_true',dest='ignore_state',default=False)
        vmnf_shared_parser.add_argument('--search-issues',action='store_true',dest='search_issues',default=False)
        # -------------------------------------------------------------------------------
        # > Analysis - [ configuration options ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--debug",action="store_true",default=False)
        vmnf_shared_parser.add_argument("--verbose", '-v', action='count', default=False)
        vmnf_shared_parser.add_argument("--random", action="store_true",default=False)
        vmnf_shared_parser.add_argument("--wait", action="store", default=False)      
        vmnf_shared_parser.add_argument("--threads",action="store", type=int, default=3)
        vmnf_shared_parser.add_argument("--timeout", action="store", type=int, default=5)
        vmnf_shared_parser.add_argument("--pause-steps", action="store_true",default=False) 
        vmnf_shared_parser.add_argument("--auto", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--sample", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--xscope", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--extended-scope", action="store_true",default=False)        
        vmnf_shared_parser.add_argument("--tracker_scope", action="store_true",default=False)        
        # -------------------------------------------------------------------------------
        # > Scope setting - [ scope parser options ] 
        # -------------------------------------------------------------------------------
        vmnf_shared_parser.add_argument("--console-pin", action="store", dest='console_pin',default=False)
        vmnf_shared_parser.add_argument("--urlconf", action="store", dest='url_conf',default=False)
        vmnf_shared_parser.add_argument("--patterns", action="store", dest='patterns_file',default=False)
        vmnf_shared_parser.add_argument("--view-name", action="store", dest='view_name',default=False)
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
        vmnf_shared_parser.add_argument("--session",action="store_true",dest='session_mode',default=False)
        vmnf_shared_parser.add_argument("--callback-session",action="store_true",dest='callback_session',default=False)
        
        return vmnf_shared_parser



    def shared_help(self):
        
        '''
    [target]  

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
 
