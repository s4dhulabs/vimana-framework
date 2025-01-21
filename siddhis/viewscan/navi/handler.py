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

from pygments import formatters, highlight, lexers

from core.vmnf_navicontrols import *


from ..tools.vs_tools import (
    get_mod_hash
)

from siddhis.viewscan.tools.vs_tools import (
    get_object_issues, 
    handle_sast_output
)

from core.vmnf_utils import antiCrashSystem as ACS
from core._dbops_.db_utils import get_elapsed_time
from core.vmnf_sessions_utils import abduct_items
from neotermcolor import cprint, colored as cl
from core._dbops_.models.scans import VFScans
from core._dbops_.vmnf_dbops import VFDBOps
from simple_term_menu import TerminalMenu
from datetime import datetime,timezone
from core.load_settings import _vfs_
from urllib.parse import urlparse
from typing import Tuple, Union
from res.vmnf_banners import *
from os.path import dirname
from shutil import rmtree
from time import sleep
import jsonpickle
import yaml
import json
import sys
import io
import os

vimana_path = os.getenv("vimana_path")

class navi_handler:
    def __init__(self, vmnf_handler:dict) -> None:
        self.vmnf_handler = vmnf_handler
        self.health_check = []
        self.prompt = '➤ '
        self.accepted_keys = (
            "enter", "o", "f", "t","r","s","d", "b", "u", 'y'
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

    def get_app_objects(self, _app_dir_):
        _app_files_ = list_files(_app_dir_)
        _raw_objects_ = [o for o in _app_files_ if '_vs_' in o]

        # check if len of raw is 0 no objects to show
        _objects_ = [o.replace('.sarif','').split('_vs_') for o in _raw_objects_]

        return _app_files_,_raw_objects_,_objects_
        
    def app_objects(
        self, 
        scan, 
        project:str, 
        selected_app:str, 
        keep_banner:False
        )-> Union[str, bool]:

        self.object_scan_flag = False
        scan_id = scan.scan_id
        scan_scope = scan.scan_scope
        scan_output_file = scan.scan_output_file
        cache_dir = scan.scan_cache_dir
        app_dir = f"[{scan_id}]→ {project}.{selected_app}"

        selected_object = False
        app_view_objects= False

        while True:
            _app_dir_ = f"{cache_dir}/{selected_app}"
            _app_files_,_raw_objects_,_objects_ = self.get_app_objects(_app_dir_)
        
            app_dir_header = f"[{scan_id}]→ {project}.{selected_app}"
            jazzit(app_dir_header, f"[{scan_id}]→ {project:>7}", keep_banner)
            max_key_width = max(len(_[0]) for _ in _objects_) + 10
        
            _objects_ = [f' {op[0]:{max_key_width}} ⚡  {op[1]}' for op in _objects_]
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

            if chosen_key == 'o':
                navioptions_menu()
                selected_object = False
                continue

            elif chosen_key == 's':
                pager(obj_file_path).run()
                selected_object = False
            
            elif chosen_key == 'd':
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
            
            elif chosen_key == 'r':
                # current: selected scan - vs_vparser objects: list of dicts
                scan_objects = jsonpickle.decode(scan.__dict__['scan_scope'])
                
                # argparser namespace
                scan_handler = jsonpickle.decode(scan.vmnf_handler)
                scan_target = scan.scan_target

                if 'scope_type' in scan_handler and scan_handler['scope_type'] == 'view':

	            # apiv3.users
                    if '.' in scan.scan_target:

		        # apiv3
                        scan_target = scan.scan_target.split('.')[0]
                
                for object in scan_objects:
                    if selected_object in object:
                        scanned_object = object[selected_object]
                        scanned_view_hash = scanned_object['view_hash']
                        scanned_object_hash = scanned_object['obj_hash']
                
                # Check if the view exists in the path below
                view_app_path = scan.scan_target_full_path

                if not 'scope_type' in scan_handler or scan_handler['scope_type'] == 'object':
                    view_app_path = f"{view_app_path}/{selected_app}"

                full_view_path = f"{view_app_path}/views.py"

                if not os.path.exists(full_view_path):
                    input(f'Could not find view at {full_view_path}')
                    input(f"> fullpath: {scan.scan_target_full_path}")

                    input(scan_handler)
                    continue
                
                with open(full_view_path,'r') as file:
                    module_content = file.read()
                    #tree = ast.parse(module_content)
                    current_view_hash = get_mod_hash(module_content)
               
                # Check if the view changed
                if current_view_hash == scanned_view_hash:
                    input('hashes are the same')
                    print()

                    for line in scanned_object['hl_code']:
                        print(line.strip())
                    print()
                    input()

                    continue
                
                # start a scan just in the select object: project.app.object
                set_plugin_target = f"{scan_target}.{selected_app}.{selected_object}"
                self.run_plugin(
                    scan,{
                        'project_dir': view_app_path,
                        'scope_type': 'object',
                        'app_dir': app_dir,
                        'filter_by_objects': {
                            selected_object: scanned_object_hash
                        },
                        'set_plugin_target': set_plugin_target
                    }
                )  
                
                self.object_scan_flag = True
                break

            elif chosen_key == 'enter':
                if selected_object:
                    status = self.scan_details(
                        scan_id,
                        project,
                        selected_app,
                        selected_object,
                        scan_scope,
                        scan_output_file,
                        app_dir,
                        keep_banner
                    )

        return selected_object

    def manage_scan(self, _scan_, keep_banner:False) -> Union[Tuple[str, str, str], bool]:
        scan_handler = jsonpickle.decode(_scan_.vmnf_handler)
        project = _scan_.scan_target.replace('/','')
        scan_id = _scan_.scan_id
        plugin  = _scan_.scan_plugin
        selected_object, selected_app, app_dir = (False,)*3
        cache_dir = _scan_.scan_cache_dir
       
        # project.app.view.object → Go straight to the view objects
        if 'scope_type' in scan_handler:
            
            if scan_handler['scope_type'] in ['view']:
                input('here')
                selected_app = _scan_.scan_target_full_path.split('/')[-1]
            
                selected_object = self.app_objects(
                    _scan_, project, selected_app, keep_banner
                )

            elif scan_handler['scope_type'] in ['object']:
                selected_object = scan_handler['filter_by_objects']
                selected_app = scan_handler['set_plugin_target'].split('.')[1]
                app_dir = scan_handler['app_dir']
                scan_output_file = _scan_.scan_output_file

                status = self.scan_details(
                    scan_id,
                    project.split('.')[0],
                    selected_app,
                    selected_object,
                    _scan_.scan_scope,
                    scan_output_file,
                    app_dir,
                    keep_banner
                )

            return True
    
        while True:
            jazzit(f"[{scan_id}]→ {project} ", f"[{scan_id}]", keep_banner)
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
       
            if chosen_key == 'o':
                navioptions_menu('scans_main_menu')
                continue
            
            elif chosen_key == 'r':
                # objects scanned → from metadata of scanned view
                scan_objects = jsonpickle.decode(_scan_.__dict__['scan_scope'])

                # get the selected app's objects → from sarif files
                _app_files_, _raw_objects_, _objects_ = self.get_app_objects(selected_app_path)

                filtered_objects = []
                for f in _objects_:
                    filtered_objects.append(f[0])

                # filtered_objects: unique objects, in case we want to scan just the affected objects
                # instead of the whole view again, it should be set to `False` or empty dict to scan 
                # the whole view
                filtered_objects = list(set(filtered_objects))
            
                new_scope_objects = {}

                for entry in scan_objects:
                    for view_object in entry:
                        if view_object in filtered_objects:
                            if entry[view_object]['target_app'] == selected_app:
                                new_scope_objects[view_object] = entry[view_object]['obj_hash']

                abs_path = os.path.join(_scan_.scan_target_full_path, selected_app)

                self.run_plugin(
                    _scan_,{
                        'project_dir': abs_path, 
                        'scope_type': 'view',
                        'filter_by_objects': new_scope_objects,
                        'set_plugin_target':  f"{_scan_.scan_target}.{selected_app}"
                    }
                )
                
                break
                
            elif chosen_key == 'd':
                view_objects_to_delete = [o.split('_vs_')[0] 
                    for o in list_files(selected_app_path)
                ]
                object_ref = f"{scan_id}.{project}.{selected_app}.NA.NA"
                action_confirmed = naviobject_delete(object_ref, view_objects_to_delete) 

                if not action_confirmed:
                    continue
                
                rmtree(selected_app_path)

                if not self.checklast_app(scan_id):
                    continue
            
            elif chosen_key == 'enter':
                app_dir = f"[{scan_id}]→ {project}.{selected_app}"

                # project.app.view.object
                selected_object = self.app_objects(
                    _scan_, project, selected_app, keep_banner
                )

                if self.object_scan_flag and self.newscan_done:
                    break

    def scan_details(
        self,
        scan_id:str,
        project:str,
        selected_app:str,
        selected_object:str,
        scan_scope:str, 
        scan_output_file:str,
        app_dir:str,
        keep_banner:bool=False
        ) -> bool:

        status = False

        try:
            scan_data = jsonpickle.decode(scan_scope)
        except json.decoder.JSONDecodeError:
            return False

        if not scan_data:
            return False

        while True:
            try:
                if isinstance(selected_object, dict):
                    selected_object = list(selected_object.keys())[0]

                _object_data_ = [d[selected_object] for d in scan_data if selected_object in d][0]
            except IndexError:
                break

            location = f"[{_object_data_['start']},{_object_data_['end']}]"
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

            jazzit(load_status_msg + " ✓ ", app_dir, keep_banner)
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

    def run_plugin(self, scan, reqs:dict=False):
        self.newscan_done = False
        scan_handler = jsonpickle.decode(scan.vmnf_handler)
        scan_handler['navigation_mode'] = True

        if reqs:
            scan_handler.update(reqs)

        plugin = scan.scan_plugin
        module_path = f"siddhis.{plugin}.{plugin}"
        siddhi = __import__(module_path, globals(), 'siddhi', 1).siddhi
        self.newscan_done = siddhi(**scan_handler).start()



