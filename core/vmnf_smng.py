# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# 
# This file is part of Vimana Framework Project.

from siddhis.djunch.engines._dju_settings import table_models
from siddhis.djunch.engines._dju_utils import DJUtils 
from core.vmnf_sessions_utils import abduct_items
from neotermcolor import cprint, colored as cl
from ._dbops_.vmnf_dbops import VFDBOps
from ._dbops_.db_utils import handle_OpErr
from .vmnf_navi_siddhis import navisiddhis 
#from .setevars import set_vimana_path
from core.load_settings import _version_

from res.vmnf_banners import case_header
from .vmnf_asserts import vfasserts
from .vmnf_utils import describe
from sqlalchemy import inspect
from time import sleep
import yaml
import sys
import os

from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from pygments import highlight
from core.vmnf_utils import gen_issues_table

class VFManager:
    def __init__(self,**handler:False):
        self.handler = handler
        self.query_filters = []
        self.model = '_SIDDHIS_'
        self.obj_id_col = 'name'
        self.interactive_mode = handler.get('navigation_mode',False)
        self.handler['fancy_table'] = True 
        
        if not handler.get('module_run',False) and not handler.get('load_plugins',False) and not self.interactive_mode:
            ''' We're not going to use query filters with vf run -m/-p/-s '''
            self.query_filters = self.get_filters()

    def load_tools(self):
        if VFDBOps().table_exists('_TOOLS_') and VFDBOps().getall('_TOOLS_'):
            handle_OpErr('db ready')

        with open(f'{os.getcwd()}/tools/tools.yaml', 'r') as f:
            tools = yaml.load(f, Loader=yaml.FullLoader)
            
            for tool in tools['tools']:
                VFDBOps(**tool).register('_TOOLS_')
            
    def load_siddhis(self):
        
        if VFDBOps().table_exists('_SIDDHIS_') and VFDBOps().getall(self.model):
            handle_OpErr('db ready')
            return True  
        
        fields = ['name','category','framework','package','type']

        for s in os.scandir(f'{os.getcwd()}/siddhis/'):
            print(f"\tLoading {s.name}...")
            sleep(0.1)
            if (s.is_dir() and not s.name.startswith('_')):
                with open(f"{s.path}/{s.name}.yaml", 'r') as f:
                    siddhi = yaml.load(f, Loader=yaml.FullLoader)
                
                siddhi.update((f, siddhi[f].lower()) 
                    if not isinstance(siddhi[f], bool) \
                        else (f, siddhi[f]) for f in fields)
                
                abduct_items(**siddhi)
                VFDBOps(**siddhi).register('_SIDDHIS_')

        # No need for global path tracking - just use relative paths
        vimana_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  
        
        self.load_tools()
        self.list_siddhis()
    
    def no_match(self):
        case_header()
        cprint("\tNo modules were found with the given criteria:\n", 'red')

        [print(f"\t{filter.get('field'):>15}: {filter.get('value')}") \
            for filter in self.query_filters ]
        print()
        print()

    def get_filters(self):
        filters = []

        for field,value in self.handler.items():
            if not value or value is None:
                continue
            
            if field in [
                'fancy_table',
                'color_enabled',
                'colors_enabled',
                'highlight_enabled',
                'guide_examples', 
                'module_list', 
                'guide_args', 
                'guide_labs',
                'args'
                ]:
                continue
            
            if field in ['module_info']:
                self.handler['module'] = \
                        self.handler['module_info']
                self.handler['module_info'] = False
                field = 'module'
            
            elif field == 'module_guide':
                self.handler['module'] = \
                        self.handler['module_guide']
                self.handler['module_guide'] = False
                field = 'module'

            elif field == 'module_run':
                self.handler['module'] = \
                        self.handler['module_run']
                self.handler['module_run'] = False
                field = 'module'
            
            # recorded as is: uppercase stuff
            if field in ['astt']:
                value = value.upper()
            else:
                value = value.lower()

            filters.append({
                'field': field,
                'op': '==',
                'value': value
                }
            )

        return filters

    def print_guide_line(self, line):
        if self.handler['color_enabled']:
            print(f"\t\t{highlight(line,PythonLexer(),TerminalFormatter()).strip()}")
        else:
            print(f"\t\t{cl(line,'white')}")

    def show_guide(self, sguide, sections:list):
        if '-e' in sections:
            for ie in sguide['examples'].split('\n'):
                self.print_guide_line(ie)
        if '-a' in sections:
            for arg in sguide['args'].split('\n'):
                self.print_guide_line(arg)
        if '-l' in sections:
            for lset in sguide['lab_setup'].split('\n'):
                self.print_guide_line(lset)
        print()
    
    def get_siddhi_guide(self):
        siddhi = self.get_siddhi()
        _vfassert_ = vfasserts(**self.handler)
        
        if siddhi is None:
            self.no_match()
            return False

        sguide = siddhi.guide
        
        print("\033c", end="")
        print()
        
        # full guide -> examples, args, labs
        if _vfassert_.default_guide_mode():
            self.show_guide(sguide,['-e', '-a', '-l'])

        # command line examples
        elif self.handler.get('guide_examples'):
            self.show_guide(sguide,['-e'])

        # only args
        elif self.handler.get('guide_args'):
            self.show_guide(sguide,['-a'])
    
        # lab test setup
        elif self.handler.get('guide_labs'):
            self.show_guide(sguide,['-l'])

        return sguide

    def show_siddhi_info(self):
        siddhi = self.get_siddhi()

        if siddhi is None:
            self.no_match() 
            return False

        describe().siddhi(siddhi)

    def query_siddhis(self):
        if not VFDBOps().table_exists(self.model):
            from res.vmnf_banners import default_naviban    
            print("\033c", end="")
            default_naviban()
            print(f"\n  No plugins loaded. Please run 'vimana load --plugins' to load plugins.\n")
            sys.exit(1)
        
        return (VFDBOps().list_resource(self.model,self.query_filters))

    def get_siddhi(self):
        return VFDBOps().get_by_id(
            self.model, self.obj_id_col, self.handler['module']
        )

    def get_siddhis_stats(self):
        from core.vmnf_payloads import VMNFPayloads

        payloads = VMNFPayloads()._vmnfp_payload_types_(True,False)
        siddhis = VFDBOps().getall(self.model)
        stats = [s.type.lower() for s in siddhis]
        stats = {st:stats.count(st) for st in stats}
        stats['payloads'] = len(payloads)

        for k,v in stats.items():
            print(f"{cl(k, 'cyan'):>30}: {cl(v,'green')}")
        print()
        print()

    def list_siddhis(self):

        if self.interactive_mode:
            navisiddhis(self.handler).manage()
            return True

        _plugins_table_ = False
        matches = self.query_siddhis()

        if not matches:
            self.no_match() 
            return False
        
        #case_header()
        #print("\033c", end="")
        vimana_version = cl(f'Vimana v{_version_}', 77,attrs=['bold'])
        vimana_desc = cl('(Security & Automation Tools for Python Web Frameworks)', 77,attrs=['bold'])
        plugin_catalog = cl('Plugin Catalog', 15)  # or 97 for bright white

        vimana_banner = f"""
        
                      __'__'__         
                        `''´          
                   {vimana_version} - {plugin_catalog}
                   {vimana_desc}
        """

        cprint(vimana_banner, 77)

        
        if self.handler.get('fancy_table'):
            _plugins_table_ = gen_issues_table(matches, 'plugins')

        else:
            _plugins_table_ = DJUtils().get_pretty_table(
                **table_models().siddhis_tbl_set
            )

            for siddhi in matches:
                _plugins_table_.add_row(
                    [
                        cl(siddhi.name.lower(),64),
                        siddhi.type.lower(),
                        siddhi.category.lower(),
                        siddhi.astt.upper(),
                        siddhi.info
                    ]
                )
                
        #cprint(f"\n❖ Vimana Plugin Catalog:", "white",attrs=['bold'])
        print(_plugins_table_)
        print()

    def run_siddhi(self):
        self.handler['module'] = self.handler['module_run']
        siddhi = self.get_siddhi()

        # `project_dir` could also be set right here
        if not self.handler['runner_mode'] and not self.handler['request_data_set']:
            ''' In Runner mode we already have the scope 
            and everything else in place '''
            # new stuff here
            if siddhi.vfset.get('parse_plugin_scope'):
                self.parse_handler_scope()


        siddhi = self.get_siddhi()

        try:
            module_path = (siddhi.module.replace('/', '.').replace('\\', '.'))[:-3]
        except AttributeError as aex:
            if "no attribute 'module'" in aex.args[0]:
                cprint("It seems like you haven't populated the database yet.", 'cyan')
                cprint(f"   Just run load to fix this: {cl('$ vimana load --plugins.','green')}\n", 'cyan')
                return False

        try:
            _siddhi_ = __import__(module_path, globals(), 'siddhi', 1).siddhi
        except AttributeError as AEX:
            if self.handler['debug']:
                _ex_().template_atribute_error(AEX,module_name)
            sys.exit(1)
        
        try:
            run_status = _siddhi_(**self.handler).start()
        except KeyboardInterrupt:
            sys.exit(1)
        return True

    def set_sessions_control(self):
        return VFDBOps(**self.handler).getall(self.model) 

    def parse_handler_scope(self):
        from res.vmnf_validators import get_tool_scope as get_scope
        from core.vmnf_scope_parser import ScopeParser
        from core.vmnf_dscan import DockerDiscovery
        from core.vmnf_rrunner import rudrunner
        from core.vmnf_cases import CasManager
        from res.vmnf_banners import vmn05
        from res import vmnf_banners

        targets_ports_set = []

        _vfassert_ = vfasserts(**self.handler)
        
        if _vfassert_.version_search():
            self.handler['framework_search_version'] = True

        if self.handler['docker_scope'] \
                and not self.handler['save_case'] \
            or _vfassert_.exec_enabled():

            self.handler['docker_scope'] = DockerDiscovery()
            self.handler['auto'] = True 

            [targets_ports_set.extend(y) \
                for y in [x['target_list'] \
                    for x in self.handler['docker_scope']
                    ]
            ]
            
        if sys.argv[-1] != self.handler['module']:
            if self.handler['save_case']:
                self.handler['args'] = sys.argv
                CasManager(self.handler).save_case()

            if self.handler['sample']:
                print("\033c", end="")
                vmnf_banners.sample_mode(
                    cl('  sample mode   ','red', 'on_white', attrs=['bold'])
                )

            if not self.handler['session_mode']\
                    and not self.handler['sample']:

                vmnf_banners.load(self.handler['module'],3)
                vmnf_banners.default_vmn_banner()
            
            # plugins that require 'project_dir' argument doesn't use target scope,e.g: IP's, URLs,etc
            if self.handler['project_dir']:
                sleep(1)
                return True

        if not self.handler['docker_scope']:
            self.handler['scope'] = ScopeParser(**self.handler).parse_scope()
            targets_ports_set = get_scope(**self.handler)

        if targets_ports_set:
            len_tps = len(targets_ports_set)
        else:
            len_tps = False

        self.handler['multi_target'] = True if len_tps and len_tps> 1 else False

        if self.handler['multi_target']:
            cs_b = len(self.set_sessions_control())
            if not self.handler['args']:
                self.handler['args'] = sys.argv

            self.handler['runner_mode']  = True
            self.handler['runner_tasks'] = targets_ports_set
            rudrunner(**self.handler)
            cs_a = len(self.set_sessions_control())

            if cs_a:
                new_sessions = cs_a - cs_b
                cprint(f"\n\t{new_sessions} {self.handler['module_run']} sessions successfuly recorded!\n", 'blue')
            os._exit(os.EX_OK) 

        if not vfasserts(**self.handler).tactical_mode():
            try:
                self.handler['target_url'] = targets_ports_set[0]
            except IndexError: 
                vmn05()
                print(f"""
                
                [{cl(self.handler['module_run'],'blue')}] {cl('→ Missing scope!', 'red')}\n 
                * Protip: Use vf guide -m {self.handler['module_run']} --args/--labs/--examples

                """
                )

                sys.exit(1)
        else:
            if self.handler['target_url']:
                self.handler['scope'] = {
                    'target_url': [
                        self.handler.get('target_url')
                    ]
                }
