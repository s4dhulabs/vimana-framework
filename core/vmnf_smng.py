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
from core.vmnf_sessions_utils import abduct_items
from neotermcolor import cprint, colored as cl
from ._dbops_.vmnf_dbops import VFDBOps
from ._dbops_.db_utils import handle_OpErr
from .vmnf_navi_siddhis import navisiddhis 
#from .setevars import set_vimana_path
from core.load_settings import _version_
from core.vmnf_siddhi_schema import (
    SiddhiSchemaError,
    guide_section,
    normalize_guide,
    validate_siddhi_schema,
)

from res.vmnf_banners import case_header
from .vmnf_asserts import vfasserts
from .vmnf_utils import describe
from sqlalchemy import inspect
from time import sleep
import hashlib
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

    def _get_vimana_root(self):
        """Get the Vimana root directory using VIMANA_PATH or fallback to __file__."""
        vimana_path = os.getenv("VIMANA_PATH")
        if vimana_path and os.path.exists(vimana_path):
            return vimana_path
        
        # Fallback to __file__ based resolution
        current_file = os.path.abspath(__file__)
        # Navigate up from core/vmnf_smng.py to vimana root
        vimana_root = os.path.dirname(os.path.dirname(current_file))
        return vimana_root

    def _siddhis_already_loaded(self):
        """Check if siddhis are already loaded efficiently (auto-first-load gate only)."""
        if not VFDBOps().table_exists('_SIDDHIS_'):
            return False
        
        # Just check if table has any records, don't load all data
        try:
            count = VFDBOps().count_records('_SIDDHIS_')
            return count > 0
        except Exception:
            return False

    def _discover_plugin_dirs(self, siddhis_path):
        """Discover plugin directories with error handling."""
        plugin_dirs = []
        
        if not os.path.exists(siddhis_path):
            cprint(f"Warning: Siddhis directory not found: {siddhis_path}", 'yellow')
            return plugin_dirs
        
        try:
            for s in os.scandir(siddhis_path):
                if s.is_dir() and not s.name.startswith('_'):
                    plugin_docs = os.path.join(s.path, f"{s.name}.yaml")
                    if os.path.exists(plugin_docs):
                        plugin_dirs.append({
                            'name': s.name,
                            'path': s.path,
                            'yaml_file': plugin_docs
                        })
        except Exception as e:
            cprint(f"Error scanning siddhis directory: {e}", 'red')
        
        return plugin_dirs

    def _yaml_content_hash(self, yaml_file):
        try:
            with open(yaml_file, 'rb') as handle:
                return hashlib.sha256(handle.read()).hexdigest()[:16]
        except OSError:
            return None

    def _load_plugin_yaml(self, yaml_file, plugin_name):
        """Load a single plugin YAML file with error handling."""
        try:
            with open(yaml_file, 'r') as f:
                siddhi_data = yaml.load(f, Loader=yaml.FullLoader)
            return siddhi_data
        except yaml.YAMLError as e:
            cprint(f"Warning: Invalid YAML in {plugin_name}: {e}", 'yellow')
            return None
        except Exception as e:
            cprint(f"Warning: Could not load {plugin_name}: {e}", 'yellow')
            return None

    def _process_siddhi_data(self, siddhi_data, plugin_name, yaml_file=None):
        """Validate, normalize, and prepare siddhi data for registration."""
        if not siddhi_data:
            return None

        try:
            validated, warnings = validate_siddhi_schema(
                siddhi_data,
                plugin_name=plugin_name,
                yaml_file=yaml_file,
            )
        except SiddhiSchemaError as err:
            cprint(f"Schema error in {plugin_name}:", 'red')
            for detail in err.errors:
                cprint(f"  - {detail}", 'red')
            if yaml_file:
                cprint(f"  file: {yaml_file}", 'yellow')
            return None

        for warning in warnings:
            cprint(f"Warning ({plugin_name}): {warning}", 'yellow')

        fields = ['name', 'category', 'framework', 'package', 'type']
        processed_data = {}
        for field in fields:
            if field in validated:
                value = validated[field]
                if not isinstance(value, bool):
                    processed_data[field] = value.lower()
                else:
                    processed_data[field] = value

        for key, value in validated.items():
            if key not in fields:
                processed_data[key] = value

        # Ensure guide is normalized (labs -> lab_setup)
        if isinstance(processed_data.get('guide'), dict):
            processed_data['guide'] = normalize_guide(processed_data['guide'])

        # Stamp content hash into vfset for change detection
        if yaml_file:
            vfset = dict(processed_data.get('vfset') or {})
            content_hash = self._yaml_content_hash(yaml_file)
            if content_hash:
                vfset['_yaml_hash'] = content_hash
            processed_data['vfset'] = vfset

        return processed_data

    def _register_siddhis_batch(self, siddhis_data, *, force: bool = False):
        """Upsert multiple siddhis with schema validation and error handling."""
        success_count = 0
        updated_count = 0
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for plugin_info in siddhis_data:
            plugin_name = plugin_info['name']
            yaml_file = plugin_info['yaml_file']
            
            print(f"\tLoading {plugin_name}...")
            
            siddhi_data = self._load_plugin_yaml(yaml_file, plugin_name)
            if not siddhi_data:
                error_count += 1
                continue
            
            processed_data = self._process_siddhi_data(
                siddhi_data, plugin_name, yaml_file=yaml_file
            )
            if not processed_data:
                error_count += 1
                continue

            # Skip unchanged plugins unless --reload/--force
            if not force:
                existing = VFDBOps().get_by_id('_SIDDHIS_', 'name', processed_data.get('name'))
                if existing is not None:
                    existing_hash = (existing.vfset or {}).get('_yaml_hash') if isinstance(existing.vfset, dict) else None
                    new_hash = (processed_data.get('vfset') or {}).get('_yaml_hash')
                    if existing_hash and new_hash and existing_hash == new_hash:
                        skipped_count += 1
                        cprint(f"\t  unchanged ({plugin_name})", 'cyan')
                        success_count += 1
                        continue
            
            try:
                abduct_items(**processed_data)
                action = VFDBOps(**processed_data).upsert('_SIDDHIS_', match_col='name')
                if action == 'updated':
                    updated_count += 1
                    cprint(f"\t  updated ({plugin_name})", 'green')
                else:
                    created_count += 1
                    cprint(f"\t  created ({plugin_name})", 'green')
                success_count += 1
            except Exception as e:
                cprint(f"Error registering {plugin_name}: {e}", 'red')
                error_count += 1
        
        if error_count > 0:
            cprint(f"Warning: {error_count} plugins failed to load", 'yellow')
        if created_count or updated_count or skipped_count:
            cprint(
                f"Sync summary: {created_count} created, {updated_count} updated, "
                f"{skipped_count} unchanged, {error_count} errors",
                'cyan',
            )
        
        return success_count, error_count

    def load_tools(self):
        if VFDBOps().table_exists('_TOOLS_') and VFDBOps().getall('_TOOLS_'):
            return

        vimana_root = self._get_vimana_root()
        tools_file = os.path.join(vimana_root, 'tools', 'tools.yaml')
        
        if not os.path.exists(tools_file):
            cprint(f"Warning: Tools file not found: {tools_file}", 'yellow')
            return

        try:
            with open(tools_file, 'r') as f:
                tools = yaml.load(f, Loader=yaml.FullLoader)
            
            for tool in tools['tools']:
                VFDBOps(**tool).register('_TOOLS_')
        except Exception as e:
            cprint(f"Error loading tools: {e}", 'red')
            
    def load_siddhis(self):
        """Load/sync siddhis from YAML. Explicit load always upserts; auto-first-load skips if DB has rows."""
        force = bool(self.handler.get('reload_plugins') or self.handler.get('force_reload'))
        explicit_load = bool(self.handler.get('load_plugins'))

        # Auto-first-load only: skip when DB already populated (unless --reload/--force)
        if not explicit_load and not force and self._siddhis_already_loaded():
            handle_OpErr('db ready')
            return True

        if force:
            cprint("Reloading plugins from YAML (--reload)...", 'cyan')
        
        # Get Vimana root path
        vimana_root = self._get_vimana_root()
        siddhis_path = os.path.join(vimana_root, 'siddhis')
        
        # Discover plugin directories
        plugin_dirs = self._discover_plugin_dirs(siddhis_path)
        
        if not plugin_dirs:
            cprint("No valid plugin directories found", 'red')
            return False
        
        # Upsert siddhis with schema validation
        success_count, error_count = self._register_siddhis_batch(plugin_dirs, force=force)
        
        if success_count > 0:
            cprint(f"Successfully synced {success_count} plugins", 'green')
        
        # Load tools and list siddhis
        self.load_tools()
        self.list_siddhis()
        
        return True
    
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
        if not isinstance(sguide, dict):
            self.print_guide_line('(guide unavailable)')
            print()
            return

        missing = '(section not documented for this plugin)'

        if '-e' in sections:
            examples = guide_section(sguide, 'examples', default=missing)
            for ie in examples.split('\n'):
                self.print_guide_line(ie)
        if '-a' in sections:
            args = guide_section(sguide, 'args', default=missing)
            for arg in args.split('\n'):
                self.print_guide_line(arg)
        if '-l' in sections:
            labs = guide_section(sguide, 'lab_setup', 'labs', default=missing)
            for lset in labs.split('\n'):
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
        
        print("\033c", end="")
        vimana_version = cl(f'Vimana {_version_}', 77,attrs=['bold'])
        vimana_desc = cl('(Security & Automation Tools for Python Web Frameworks)', 77,attrs=['bold'])
        plugin_catalog = cl('Plugin Catalog', 15)  

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
            from siddhis.djunch.engines._dju_utils import DJUtils

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
