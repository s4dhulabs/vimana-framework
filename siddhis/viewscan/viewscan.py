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

import os
import sys
import argparse
import jsonpickle
from time import sleep
from datetime import datetime
from django.urls import include, path
from res.vmnf_banners import case_header,default_naviban
from neotermcolor import cprint,colored as cl

#from .parsers.vs_vparser import parse_view
from .parsers.vs_vparser import vsparser

from .engines.vs_authentication import vs_authentication
from .engines.vs_authorization import vs_authorization
from .engines.vs_sensitive_data import vs_sensitive_data

from core._dbops_.vmnf_dbops import VFDBOps
from core._dbops_.db_utils import get_elapsed_time
from .tools.vs_tools import (
    get_views,
    hashdir,
    get_django_version,
    handle_sast_output
)

# vflogging
import logging
from core.vmnf_log_utils import configure_logging
configure_logging(os.path.basename(__file__))

class siddhi:
    def __init__(self,**vmnf_handler):
        logging.info("Initializing VS siddhi class...")

        self.vmnf_handler = vmnf_handler
        self.vmnf_handler['rule'] = False
        self.model = '_SCANS_'
        self.obj_id_col = 'scan_id'
        self.scan_scope = []
        
        self.target_dir = vmnf_handler.get('project_dir',False)
        
        if not self.target_dir:
            cprint("\n Missing project directory: vimana run --plugin viewscan --project-dir mydjangoapp/\n", "red")
            sys.exit(1)
        
        self.no_views = []

        if self.target_dir.endswith('/'):
            self.target_dir = self.target_dir[:-1]

        if os.path.isabs(self.target_dir):
            self.directory_path = self.target_dir
            self.target_dir = self.target_dir.split('/')[-1]
        else:
            self.directory_path = os.path.join(os.getcwd(), self.target_dir)
        
        if '/' in self.target_dir:
            self.target_dir = self.target_dir.split('/')[-1]

        scope_type = self.vmnf_handler.get('scope_type',False)

        if scope_type and scope_type in ['view', 'object']:
            plugin_target = self.vmnf_handler.get('set_plugin_target')

            if plugin_target:
                self.target_dir = plugin_target

        self.engines_loaded = False
        engines_on = self.load_vsengines()

        if not engines_on:
            case_header()
            print(f"\n\t[viewscan:engines_load()] → Something went wrong!\n")
            sys.exit(1)

        issue_type = 'sast/output'
        plugin_scope = f'django/{issue_type}'
        self.cache_dir = f"vimana/__cache__/{plugin_scope}/{self.target_dir.replace('/','')}"
        self.cache_dir = os.path.join(os.path.expanduser("~"), self.cache_dir)

        logging.info("VS class initialized successfully!")

    def load_vsengines(self):
        self.engines_set = (
            os.path.join(os.path.dirname(__file__), 'engines')
        )
        
        if not self.engines_set:
            return False

        self.engines = [os.path.splitext(f)[0] \
                for f in os.listdir(self.engines_set) \
            if f.endswith('.py') and f.startswith('vs_')]
        
        if not self.engines:
            return False

        self.engines_loaded = True
        return True

    def run_engines(self, vast:dict):
        for engine in self.engines:
            if engine.startswith('__'):
                continue

            module_name = f'siddhis.viewscan.engines.{engine}'
            module = __import__(module_name, fromlist=[engine])
            engine_class = getattr(module, engine)
            engine_instance = engine_class(**vast)
            engine_instance.__start_scan__()

    def scan(self, views_file:str):
        target_app = views_file.split("/")[-2].strip()
        print(f'\n\n * App: {cl(target_app,44, 867, attrs=["underline", "bold"])}\n')
       
        parser = vsparser(self.vmnf_handler)
        module_obj = parser.parse_view(views_file)
        self.scan_scope.append(module_obj)

        if not module_obj:
            '''

            → vs_parser().parse_view() returned an empty view_object: {}

                - `filter_by_objects` dict: {view_object: object_hash}

                If `filter_by_object` is enabled it means the selected object
                was not found or it didn't change since the base scan `r` in navigation mode
                
                Change tracker params:

                    + view_hash: app's view: djangoproject.users
                    + obj_hash:  view's methods: djangoproject.users.views.record_user()

                * By now viewscan will register a new scan with 'no issues' because the 
                  scan is registered regardless of the result. We can set a specific `reason`
                  here to use in navigation mode when hadling viewscan scans

            '''

            self.no_views.append(target_app)
            return False

        print()

        for view, vast in module_obj.items():
            vast['scan_cache_dir'] = self.scan_cache_dir
            self.run_engines(vast)

    def get_content(self,file_path):
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return False

    def start(self):
        from siddhis.prana.prana import siddhi as prana
        
        if not os.path.isdir(self.directory_path):
            case_header()
            print(f"\n\t[viewscan] → Invalid target directory: {cl(self.target_dir, 'red')}!\n")
            sys.exit(1)
        
        scan_hash = hashdir(self.directory_path)
        scan_id = scan_hash[:10]
        scan_done = VFDBOps(**self.vmnf_handler).get_by_id(
            self.model, 
            self.obj_id_col, 
            scan_id
        )

        if scan_done:
            hl_target = cl(self.target_dir,"green")
            scan_date =  cl(scan_done.scan_date,"green")
            last_scan = get_elapsed_time(scan_done.scan_date)

            print()
            print(f'[viewscan] No changes on {hl_target} project since the last scan {last_scan}!')
            print()

            if self.vmnf_handler['navigation_mode']:
                input()
                return False

            sys.exit(1)

        scan = VFDBOps(**self.vmnf_handler).get_model_dict("_SCANS_")
        views = get_views(self.directory_path)
        
        if not views:
            case_header()
            print(f'\n\t[viewscan] → No views found in: {cl(self.target_dir, "red")}\n')
            sys.exit(1)

        django_version_req,req_number = get_django_version(self.directory_path)

        if django_version_req and req_number:
            self.vmnf_handler['django_version'] = '.'.join(django_version_req.split('.')[:-1])
            cves,cves_table = prana(**self.vmnf_handler).get_cves_for_version()
        else:
            django_version_req = '?'
            req_number = '?'
            cves=[]


        os.system('clear')
        default_naviban()

        cprint(f"\n[{datetime.now()}] ⌲  Starting viewscan...", 'cyan')
        sleep(0.30)
        
        self.scan_cache_dir = f"{self.cache_dir}/{scan_id}"
        scan_output_file = f"{self.scan_cache_dir}/{scan_id}.sarif"

        scan.update(
            {
                'scan_id': scan_id,
                'scan_type': 'SAST',
                'scan_date': datetime.now(),
                'scan_hash': scan_hash,
                'scan_target': self.target_dir.replace('/',''),
                'scan_target_full_path': self.directory_path,
                'scan_cache_dir': self.scan_cache_dir,
                'scan_output_file':scan_output_file,
                'project_framework': 'Django',
                'project_framework_version': django_version_req,
                'project_framework_total_cves': len(cves),
                'project_total_requirements': req_number,
                'project_total_view_modules': len(views),
                'scan_plugin': self.vmnf_handler['module_run'],
                'vmnf_handler': jsonpickle.encode(self.vmnf_handler)
            }
        )

        print('-'*54)
        cprint(f"+ ScanID: {cl(scan_id[:10],'green')}")
        cprint(f"+ ScanEngines: {cl(len(self.engines),'green')}")
        cprint(f"+ Target: {cl(self.target_dir,'green')}")
        cprint(f"+ Django Version: {cl(django_version_req,'green')} ({len(cves)} CVEs)")
        cprint(f"+ Requirements: {cl(req_number,'green')}")
        cprint(f"+ View modules: {cl(len(views),'green')}")
        print('-'*54)
        
        input() if self.vmnf_handler.get('pause_steps') else sleep(1)

        if django_version_req != '?':
            print(cves_table)
            input() if self.vmnf_handler.get('pause_steps') else sleep(1)

        for views_file in views:
            status = 'done'

            if os.path.getsize(views_file) == 0:
                if len(views) == 1:
                    status = 'aborted'
                    case_header()

                print(f'\n\t[viewscan] → Empty views file: {cl(views_file, "red")}\n')
                continue
            
            self.scan(views_file)

        # scan_cache_dir is created just when a rule is triggered 
        # so it indicates an issues was found 
        if os.path.exists(self.scan_cache_dir):
            scan['has_issues'] = True

            sarif_handle = handle_sast_output(self.vmnf_handler)
            consolidation_status = sarif_handle.consolidate_sarif_output(
                self.scan_cache_dir,
                scan_output_file
            )

        scan['scan_scope'] = jsonpickle.encode(self.scan_scope)
        VFDBOps(**scan).register('_SCANS_')

        print(f"\n\n[{datetime.now()}]: ViewScan {status}!\n\n")
        
        if self.vmnf_handler['debug']:
            if self.no_views:
                print(f'\nNo views found for apps:')
                for v in self.no_views:
                    print(f'    * {cl(v,44,867)}')
                print()

        return True
