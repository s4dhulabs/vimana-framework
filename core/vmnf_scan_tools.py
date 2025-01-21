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
from siddhis.viewscan.tools.vs_tools import (
    get_object_issues, 
    handle_sast_output
)
from core._dbops_.models.scans import VFScans
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

class naviScan:
    def __init__(self, vmnf_handler:dict) -> None:
        self.vmnf_handler = vmnf_handler
        self.health_check = []
        self.prompt = '🛡 '
        self.accepted_keys = (
            "enter", "o", "f", "t", "r", "s", "i", "d", "ctrl-y", "p"
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
        
    def flush_scan(self,scan_id):
        VFDBOps(**self.vmnf_handler).flush_resource(
            self.model,
            self.obj_id_col,
            scan_id
        )
        return True

    def run_on_instance(self, scan, reqs:dict=False):
        scan_handler = jsonpickle.decode(scan.vmnf_handler)
        scan_handler['navigation_mode'] = True
        
        if reqs:
            scan_handler.update(reqs)

        plugin = scan.scan_plugin

        module_path = f"siddhis.{plugin}.{plugin}"
        siddhi = __import__(module_path, globals(), 'siddhi', 1).siddhi
        result = siddhi(**scan_handler).start()

    def highlight_item(self, plugin):
        scan_id = plugin.split()[0]
        scan = [s for s in self._scans_ if s.scan_id == scan_id][0]

        scan_scope = jsonpickle.decode(scan.__dict__['scan_scope'])
        info = "\n".join([f"{k:>25}:    {v}" for k, v in scan.__dict__.items()])
        
        lexer = lexers.get_lexer_by_name(
            self.lexer_style,
            stripnl=False,
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(info, lexer, formatter)

    def load_menu_settings(self):
        try:
            with open(f'{dirname(__file__)}/navisettings.yaml', 'r') as f:
                settings = yaml.load(f,Loader=yaml.FullLoader)
        except FileNotFoundError:
            os.system('clear')
            default_naviban()
            cprint(f'[{datetime.now()}] Error loading navisettings!','red')
            sys.exit(1)

        ss = settings['scans']
        detailed = ss.get('detailed')
        default  = ss.get('default')

        self.detailed_headers = detailed.get('headers')
        self.detailed_filters = detailed.get('filters')

        self.default_headers = default.get('headers')
        self.default_filters = default.get('filters')

        return True

    def manage(self) -> bool:
        self.lexer_style = 'Asc'
        hcolor = 'green'
        random_banner = 'default_naviban'
        msg = '🛡 scans'
        show_banner = True
        keep_banner = 'default_naviban'
        preview_command = None
        filters = False

        if self.vmnf_handler.get('keep_banner', False):
            keep_banner = self.vmnf_handler['keep_banner']

        if not self.load_menu_settings():
            return False

        current_headers = self.default_headers
        current_filters = self.default_filters

        while True:
            
            if self.vmnf_handler.get('start_resource'):
                # vimana start --scans @fbfc83eeb8 @e391297800
                filters = [i.replace('@','') for i in sys.argv if i.startswith('@')]

            self._scans_ = (VFDBOps().list_resource(self.model, []))
            
            if not self._scans_:
                input(cl("        It seems like you haven't performed any security scans lately.  \n", 'blue'))
                break

            if filters:
                self._scans_ = [s for s in self._scans_ if s.scan_id in filters]

            _options_, header = build_options(
                self._scans_,
                current_headers,
                current_filters
            )
            header_size = len(header)
            total_scans = len(self._scans_)

            kbann = normalize(
                header, hcolor, msg, show_banner,
                random_banner, keep_banner, header_size
            )
            keep_banner = kbann
            scans_menu = TerminalMenu(
                _options_,
                preview_command=preview_command,
                preview_size=0.85,
                preview_title='details',
                preview_border=40,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys,
                show_search_hint=True,
                show_search_hint_text=" ",
                cursor_index=len(self._scans_) - 1,
            )
            scan_index = scans_menu.show()
            chosen_key = scans_menu._chosen_accept_key
            
            if scan_index is None:
                print('\033[2J\033[1;1H')
                break

            selected_scan = self._scans_[scan_index]

            if chosen_key == 't':
                input('here in ctrl-t')
                print_scan_tree(selected_scan.scan_cache_dir)
                input()
                continue

            elif chosen_key == 'p':
                preview_command = self.highlight_item
                continue

            elif chosen_key == 'i':
                current_headers = self.detailed_headers
                current_filters = self.detailed_filters
                #preview_command = self.highlight_item
                continue

            elif chosen_key == 'd':
                current_headers = self.default_headers
                current_filters = self.default_filters
                preview_command = None
                continue

            elif chosen_key == 'f':
                apply_action = naviscan_delete(selected_scan)
                if apply_action:
                    total_scans -=1
                    self.flush_scan(selected_scan.scan_id)
                    
                    if total_scans == 0:
                        break

                    _options_ = [o for o in _options_ \
                            if o.split()[0].strip() != selected_scan.scan_id
                    ]
                continue

            elif chosen_key == 'o':
                navioptions_menu('scans_main_menu')
                continue
            
            elif chosen_key == 's':
                pager(selected_scan.scan_output_file).run()
                input()
                continue

            elif chosen_key == 'r':
                self.run_on_instance(selected_scan)
                continue

            elif chosen_key == 'p':
                preview_command = self.highlight_item
                continue

            elif chosen_key == 'ctrl-y':
                keep_banner = False
                random_banner=True
                self.cursor = choice(cursor_options)
                self.lexer_style = choice(srandlexers)
                hcolor=choice(range(321))
                continue

            elif chosen_key == 'enter':
                if not selected_scan.has_issues:
                    print('\033[2J\033[1;1H')
                    input(f'nothing to see here, not findings on scan {selected_scan.scan_id}')
                    continue

                scan_plugin = selected_scan.scan_plugin
                navihandler = f'siddhis/{scan_plugin}/navi/handler.py'

                if not os.path.exists(f"{vimana_path}/{navihandler}"):
                    os.system('clear')
                    default_naviban()
                    cprint(f"   → Plugin {scan_plugin} doesn't support navigation handler yet", 'red')
                    input()
                    continue
                
                project = selected_scan.scan_target.replace('/','')
                scan_id = selected_scan.scan_id

                handler_path = navihandler.replace('.py','').replace('/','.')
                handler_instance = __import__(handler_path, globals(), 'navi_handler', 1).navi_handler
                
                result = handler_instance(self.vmnf_handler).manage_scan(
                    selected_scan,keep_banner
                )

        return True    

