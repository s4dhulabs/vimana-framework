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

class xc_handler:
    def __init__(self, vmnf_handler:dict) -> None:
        self.vmnf_handler = vmnf_handler
        self.health_check = []
        self.prompt = '➤ '
        self.accepted_keys = (
            "enter", "o", "f", "t","r","s","d", "b", "u", 'y'
        )
        self.model = '_EXCEPTIONS_'
        self.obj_id_col = 'exception_id'

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

    def highlight_item(self, exception):
        
        exception_id = exception.split()[0]
        exception = [x for x in self._exceptions_ if x.exception_id == exception_id][0]
        exception_meta = exception.__dict__['exception_meta']
        exception_summary = exception_meta['summary']
        exception_summary['trigger'] = exception_meta['view_trigger']['trigger_line']
        
        #scan_scope = jsonpickle.decode(scan.__dict__['scan_scope'])
        #info = "\n".join([f"{k:>25}:    {v}" for k, v in exception_meta.__dict__.items()])
        info = "\n".join([f"{k:>25}:    {v}" for k, v in exception_summary.items()])
        
        #info=exception
        lexer = lexers.get_lexer_by_name(
            self.lexer_style,
            stripnl=False,
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(info, lexer, formatter)

    def load_menu_settings(self):
        try:
            with open(f'{vimana_path}/core/navisettings.yaml', 'r') as f:
                settings = yaml.load(f,Loader=yaml.FullLoader)
        except FileNotFoundError:
            os.system('clear')
            default_naviban()
            cprint(f'[{datetime.now()}] Error loading navisettings!','red')
            sys.exit(1)

        ss = settings['exceptions']
        detailed = ss.get('detailed')
        default  = ss.get('default')

        self.detailed_headers = detailed.get('headers')
        self.detailed_filters = detailed.get('filters')

        self.default_headers = default.get('headers')
        self.default_filters = default.get('filters')

        return True


    def flush_exception(self, exception_id):
        VFDBOps(**self.vmnf_handler).flush_resource(
            self.model,
            self.obj_id_col,
            exception_id
        )

        return True

    def manage(self, scan_id:str=None) -> bool:
        self.lexer_style = 'Java'
        hcolor = 'green'
        random_banner = 'default_naviban'
        msg = False
        show_banner = True
        keep_banner = 'default_naviban'
        preview_command = None
        getall = False

        if self.vmnf_handler.get('keep_banner', False):
            keep_banner = self.vmnf_handler['keep_banner']

        if not self.load_menu_settings():
            return False

        current_headers = self.default_headers
        current_filters = self.default_filters

        while True:
            if scan_id:
                getall = True
                self._exceptions_ = VFDBOps(**self.vmnf_handler).get_by_id(
                    self.model, 'scan_id', scan_id, getall
                )
            else:
                self._exceptions_ = VFDBOps().list_resource(self.model,[])

            _options_, header = build_options(
                self._exceptions_,
                current_headers,
                current_filters
            )
            header_size = len(header)

            if not self._exceptions_:
                input(cl("        It seems like you haven't performed any security scans lately.  \n", 'blue'))
                break
            total_exceptions = len(self._exceptions_)

            kbann = normalize(
                header, hcolor, msg, show_banner,
                random_banner, keep_banner, header_size
            )
            keep_banner = kbann
            exceptions_menu = TerminalMenu(
                _options_,
                preview_command=preview_command,
                preview_size=0.85,
                preview_title='details',
                preview_border=40,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys,
                show_search_hint=True,
                show_search_hint_text=" ",
                cursor_index=len(self._exceptions_) - 1,
            )
            exception_index = exceptions_menu.show()
            chosen_key = exceptions_menu._chosen_accept_key
            
            if exception_index is None:
                print('\033[2J\033[1;1H')
                break

            selected_exception = self._exceptions_[exception_index]
            
            if chosen_key == 't':
                input('here in ctrl-t')
                print_scan_tree(selected_scan.scan_cache_dir)
                input()
                continue

            elif chosen_key == 'd':
                current_headers = self.detailed_headers
                current_filters = self.detailed_filters
                preview_command = self.highlight_item
                continue

            elif chosen_key in ['b', 'u']:
                current_headers = self.default_headers
                current_filters = self.default_filters
                preview_command = None
                continue

            elif chosen_key == 'y':
                keep_banner = False
                random_banner=True
                self.cursor = choice(cursor_options)
                self.lexer_style = choice(srandlexers)
                hcolor=choice(range(321))
                continue

            elif chosen_key == 'f':
                apply_action = navix_delete(selected_exception)

                if apply_action:
                    total_exceptions -=1
                    self.flush_exception(selected_exception.exception_id)

                    if total_exceptions == 0:
                        break

                continue


        return True    

