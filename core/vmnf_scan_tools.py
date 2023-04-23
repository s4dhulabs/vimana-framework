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

from core.vmnf_navicontrols import *
from siddhis.viewscan.tools.vs_tools import (
    get_object_issues, 
    handle_sast_output
)
from core.vmnf_utils import antiCrashSystem as ACS
from core._dbops_.db_utils import get_elapsed_time
from core.vmnf_sessions_utils import abduct_items
from neotermcolor import cprint, colored as cl
from core._dbops_.vmnf_dbops import VFDBOps
from simple_term_menu import TerminalMenu
from datetime import datetime,timezone
from core.load_settings import _vfs_
from urllib.parse import urlparse
from typing import Tuple, Union
from res.vmnf_banners import *
from shutil import rmtree
from time import sleep
import jsonpickle
import json
import sys
import io
import os



class naviScan:
    def __init__(self, vmnf_handler:dict) -> None:
        self.vmnf_handler = vmnf_handler
        self.health_check = []
        self.prompt = '➤ '
        self.accepted_keys = (
            "enter", "ctrl-o", "ctrl-d", "ctrl-t","ctrl-r","alt-s",
        )
        self.model = '_SCANS_'
        self.obj_id_col = 'scan_id'

    def checklast_app(self, scan_id):
        if (self._total_apps_ - 1) == 0:
            self.flush_scan(scan_id)
            print('\033[2J\033[1;1H')
            case_header()
            sys.exit(1)
        return False

    def app_objects(
        self, 
        scan_id:str, 
        project:str, 
        selected_app:str, 
        cache_dir:str
        )-> Union[str, bool]:

        selected_object = False
        app_view_objects= False

        while True:

            app_dir_header = f"[{scan_id}]→ {project:>7}.{selected_app}"
            jazzit(app_dir_header, f"[{scan_id}]→ {project:>7}")
            _app_dir_ = f"{cache_dir}/{selected_app}"
            _app_files_ = list_files(_app_dir_)
            _raw_objects_ = [o for o in _app_files_ if '_vs_' in o]
            # check if len of raw is 0 no objects to show
            _objects_ = [o.replace('.sarif','').split('_vs_') for o in _raw_objects_]
            
            max_key_width = max(len(_[0]) for _ in _objects_) + 10

            _objects_ = [f' {op[0]:{max_key_width}} ⚡ {op[1]}' for op in _objects_]
            total_objects = len(_raw_objects_)

            objects_menu = TerminalMenu(
                _objects_,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys
            )
            obj_index = objects_menu.show()
            chosen_key = objects_menu._chosen_accept_key
            
            if obj_index is None:
                break

            raw_selected_object = _objects_[obj_index]
            selected_object = raw_selected_object.split()[0].strip()
            rule_id = raw_selected_object.split()[-1].strip()
            obj_file = _raw_objects_[obj_index]
            obj_file_path = f'{cache_dir}/{selected_app}/{obj_file}'
            full_scan_file = f'{cache_dir}/{scan_id}.sarif'
            
            if chosen_key == 'ctrl-o':
                navioptions_menu()
                selected_object = False
                continue

            elif chosen_key == 'alt-s':
                pager(obj_file_path).run()
                selected_object = False
            
            elif chosen_key == 'ctrl-d':
                object_ref = f"{scan_id}.{project}.{selected_app}.{selected_object}.{rule_id}"
                action_confirmed = naviobject_delete(object_ref,app_view_objects)
                
                if not action_confirmed:
                    continue

                with open(full_scan_file, 'r') as f:
                    data = json.load(f)
                
                updated_results = []

                for results in data['runs'][0]['results']:
                    for f in results:
                        sarif_object = f['locations'][0]['physicalLocation']['contextRegion']['object']
                        
                        if sarif_object == selected_object:
                            continue
                        
                        updated_results.append(f)
                        
                updated_sarif = handle_sast_output().get_schema()
                updated_sarif["runs"][0]["results"].append(updated_results)

                with open(full_scan_file, "w") as f:
                    json.dump(updated_sarif, f, indent=4)
                
                selected_object = False

                os.remove(obj_file_path)
                if total_objects == 1:
                    try:
                        os.rmdir(_app_dir_)
                    except OSError as e:
                        pass
                    
                    if not self.checklast_app(scan_id):
                        break
                continue
                
            if selected_object:
                break 

        return selected_object

    def project_apps(
        self,
        scan_id:str,
        project:str,
        cache_dir:str
        ) -> Union[Tuple[str, str, str], bool]:

        selected_object, selected_app, app_dir = (False,)*3

        while True:
            jazzit(f"[{scan_id}]→ {project:>7} ", f"[{scan_id}]")
            _apps_ = list_files(cache_dir)
            _apps_ = [' ' + app for app in _apps_ if not app.endswith('.sarif')]
            self._total_apps_ = len(_apps_)
            apps_menu = TerminalMenu(
                _apps_,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys
            )
            app_index = apps_menu.show()
            chosen_key = apps_menu._chosen_accept_key

            if app_index is None:
                break
            
            _apps_ = [a.strip() for a in _apps_] 
            selected_app = _apps_[app_index]
            selected_app_path = f"{cache_dir}/{selected_app}"
       
            if chosen_key == 'ctrl-o':
                navioptions_menu()
                continue

            #elif chosen_key == 'alt-s':
            #    pager(obj_file_path).run()
            #    selected_object = False

            elif chosen_key == 'ctrl-d':
                view_objects_to_delete = [o.split('_vs_')[0] 
                    for o in list_files(selected_app_path)
                ]
                object_ref = f"{scan_id}.{project}.{selected_app}.NA.NA"
                action_confirmed = naviobject_delete(object_ref,view_objects_to_delete) 

                if not action_confirmed:
                    continue
                
                rmtree(selected_app_path)
                if not self.checklast_app(scan_id):
                    continue

            app_dir = f"[{scan_id}]→ {project:>7}.{selected_app}"
            selected_object = self.app_objects(
                scan_id, project, selected_app, cache_dir
            )
            if selected_object:
                break

        return selected_object,selected_app,app_dir

    def scan_details(
        self,
        scan_id:str,
        project:str,
        selected_app:str,
        selected_object:str,
        scan_scope:str, 
        scan_output_file:str,
        app_dir:str
        ) -> bool:

        status = False
        scan_data = jsonpickle.decode(scan_scope)
        if not scan_data:
            return False

        while True:
            try:
                _object_data_ = [d[selected_object] for d in scan_data if selected_object in d][0]
            except IndexError:
                break

            location = [_object_data_['start'],_object_data_['end']]
            node = _object_data_['node']
            node_type = (type(node).__name__)
            address = (hex(id(node)))

            load_status_msg = (
                f"[{scan_id}]→ "
                f"{project}."
                f"{selected_app}."
                f"views.{selected_object} "
                f"{location} - "
                f"{node_type} "
                f"({address}) "
            )
            jazzit(load_status_msg + " ✓ ",app_dir)
            sleep(0.11)

            status = get_object_issues(
                selected_object,
                scan_output_file,
                _object_data_['hl_code'],
                load_status_msg
            )
            self.health_check.append(status)
            print()
            input(cl('      [ENTER] return to scan list / [Ctrl-C] exit navigation ' + ' '*30, 'red', 'on_white',attrs=[]))
            break

        return status

    def flush_scan(self,scan_id):
        VFDBOps(**self.vmnf_handler).flush_resource(
            self.model,
            self.obj_id_col,
            scan_id
        )

        return True

    def build_options_list(self, _scans_:list) -> list:
        _OPTIONS_ = []

        version_width = max(len(s.project_framework_version) for s in _scans_) 
        plugin_width = max(len(s.scan_plugin) for s in _scans_) 
        v_space = ' ' * version_width

        for _sc_ in _scans_:
            project_framework = f"{_sc_.project_framework} ({_sc_.project_framework_version})"
            p_space = ' ' * (20 - len(project_framework))
            project_framework = f"{v_space}{project_framework}{p_space}"
            
            project_name = _sc_.scan_target_project
            elapsed = get_elapsed_time(_sc_)

            if len(project_name) > 10:
                project_name = project_name[:7] + '...'

            _OPTIONS_.append(
                f" {_sc_.scan_id} "
                f"{_sc_.scan_type:>10} "
                f"{project_name:>16} "
                f"{project_framework:>20} "
                f"{_sc_.scan_plugin:>9} "
                f"{elapsed:>19}"
            )
        return _OPTIONS_

    def manage(self) -> bool:
        while True:
            _scans_ = (VFDBOps().list_resource(self.model, []))
            total_scans = len(_scans_)
            _options_ = self.build_options_list(_scans_)

            normalize(
                f" {'id':>7} " 
                f"{'type':>15} " 
                f"{'project':>15} " 
                f"{'framework':>19} " 
                f"{'plugin':>16} "
                f"{'date':>15} ",'green',
            )
            
            scans_menu = TerminalMenu(
                _options_,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys,
                cursor_index=len(_scans_) - 1,
            )
            scan_index = scans_menu.show()
            chosen_key = scans_menu._chosen_accept_key

            if scan_index is None:
                print('\033[2J\033[1;1H')
                break

            selected_scan = _scans_[scan_index]

            if chosen_key == 'ctrl-t':
                print_scan_tree(selected_scan.scan_cache_dir)
                input()
                continue

            if chosen_key == 'ctrl-d':
                apply_action = naviscan_delete(selected_scan)
                if apply_action:
                    total_scans -=1
                    self.flush_scan(selected_scan.scan_id)
                    
                    if total_scans == 0:
                        print('\033[2J\033[1;1H')
                        case_header()
                        sys.exit(1)

                    _options_ = [o for o in _options_ \
                            if o.split()[0].strip() != selected_scan.scan_id
                    ]
                
                continue

            elif chosen_key == 'ctrl-o':
                navioptions_menu()
                continue
            
            elif chosen_key == 'alt-s':
                pager(selected_scan.scan_output_file).run()
                continue

            elif chosen_key == 'ctrl-r':
                scan_handler = jsonpickle.decode(selected_scan.vmnf_handler)
                scan_handler['navigation_mode'] = True
                _instance_ = jsonpickle.decode(selected_scan.plugin_instance)
                _instance_exec_ = getattr(_instance_, '__class__')
                _instance_exec_(**scan_handler).start()

                continue

            project = selected_scan.scan_target_project.replace('/','')
            scan_id = selected_scan.scan_id
            jazzit(f"[{scan_id}]→ ", "[")
            sleep(0.03)

            selected_object, selected_app, app_dir = self.project_apps(
                scan_id,project,selected_scan.scan_cache_dir
            )

            if not all((selected_app, selected_object)):
                self.health_check.append(selected_object)
                continue

            status = self.scan_details(
                scan_id,
                project,
                selected_app,
                selected_object,
                selected_scan.scan_scope,
                selected_scan.scan_output_file,
                app_dir
            )
        
            if self.vmnf_handler['vf_debugger']:
                self.health_check.append(status)
                dump = {name: value for name, value in locals().items()}
                ACS(self.vmnf_handler).check_feature_status(self.health_check,dump)

        return True    

