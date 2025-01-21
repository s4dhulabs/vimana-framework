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


class naviCases:
    def __init__(self, vmnf_handler:dict) -> None:
        self.vmnf_handler = vmnf_handler
        self.health_check = []
        self.prompt = '🗂 '
        self.accepted_keys = (
            "enter", "f", "r", "o", "c", "i", "d", "ctrl-y", "p"
        )
        self.model = '_CASES_'
        self.obj_id_col = 'case_id'
        self._cases_ = self.get_cases()

    def flush_case(self,scan_id):
        VFDBOps(**self.vmnf_handler).flush_resource(
            self.model,
            self.obj_id_col,
            scan_id
        )

        return True

    def highlight_case(self,selected_case):
        case_id = selected_case.split()[0]
        case = [c for c in self._cases_ if c.case_id == case_id][0]
        info = "\n".join([f"{k:>25}:    {v}" for k, v in case.__dict__.items() if v])
        lexer = lexers.get_lexer_by_name(
            self.lexer_style,
            stripnl=False,
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(info, lexer, formatter)

    def get_cases(self):
        self._cases_ = VFDBOps().getall(self.model)

    def load_menu_settings(self):
        try:
            with open(f'{dirname(__file__)}/navisettings.yaml', 'r') as f:
                settings = yaml.load(f,Loader=yaml.FullLoader)
        except FileNotFoundError:
            os.system('clear')
            default_naviban()
            cprint(f'[{datetime.now()}] Error loading navisettings!','red')
            sys.exit(1)

        ss = settings['cases']
        detailed = ss.get('detailed')
        default  = ss.get('default')

        self.detailed_headers = detailed.get('headers')
        self.detailed_filters = detailed.get('filters')

        self.default_headers = default.get('headers')
        self.default_filters = default.get('filters')

        return True

    def get_cmd_line(self, case):
        case_ns = jsonpickle.decode(case.case_ns)
        case_args = ','.join(case_ns.args).replace(',',' ')
        tokens = case_args.split()
        cmd_tokens = []

        for i, token in enumerate(tokens):
            cmd_tokens.append(token)
            if i+1 < len(tokens) and tokens[i+1].startswith("--"):
                    cmd_tokens.append("\\\n    ")
        return "\n" + " " + " ".join(cmd_tokens) + "\n"

    def manage(self) -> bool:
        from core.vmnf_cases import CasManager as cm
        
        self.lexer_style = 'Asc'
        _options_ = []
        hcolor = 'green'
        msg = f"{self.prompt} cases"
        random_banner = True
        show_banner = True
        keep_banner = 'default_naviban'
        preview_command = None

        if self.vmnf_handler.get('keep_banner', False):
            keep_banner = self.vmnf_handler['keep_banner']

        if not self.load_menu_settings():
            return False

        current_headers = self.default_headers
        current_filters = self.default_filters

        while True:
            self.get_cases()
            if not self._cases_:
                input(cl("\t\tNo cases found!  \n", 'blue'))
                break

            _options_, header = build_options(
                self._cases_,
                current_headers,
                current_filters
            )
            header_size = len(header)
            total_cases = len(self._cases_)
            
            kbann = normalize(
                header, hcolor, msg, show_banner,
                random_banner, keep_banner, header_size
            )
            keep_banner = kbann

            cases_menu = TerminalMenu(
                _options_,
                preview_command=preview_command,
                preview_size=0.75,
                preview_title='details',
                preview_border=40,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys,
                show_search_hint=True,
                show_search_hint_text=" ",
                cursor_index=len(self._cases_) - 1,
            )
            case_index = cases_menu.show()
            chosen_key = cases_menu._chosen_accept_key
            
            if case_index is None:
                print('\033[2J\033[1;1H')
                break

            selected_case = self._cases_[case_index]
            case_id = selected_case.case_id
            case_name = selected_case.case_name

            if chosen_key == 'f':
                VFDBOps().flush_resource(self.model,self.obj_id_col, case_id)
                _options_ = [c for c in _options_ \
                        if c.split()[0].strip() != case_id
                    ]

                total_cases -=1
                if total_cases == 0:
                    break
                continue

            elif chosen_key == 'c':
                navioptions_menu(
                    self.get_cmd_line(selected_case),
                    f'{case_name}:{case_id}'
                )
                continue

            elif chosen_key == 'i':
                current_headers = self.detailed_headers
                current_filters = self.detailed_filters
                continue
                
            elif chosen_key == 'd':
                current_headers = self.default_headers
                current_filters = self.default_filters
                continue

            if chosen_key == 'ctrl-y':
                keep_banner = False
                random_banner=True
                self.cursor = choice(cursor_options)
                self.lexer_style = choice(srandlexers)
                hcolor=choice(range(321))
                continue

            elif chosen_key == 'o':
                navioptions_menu('cases_main_menu')
                continue

            elif chosen_key == 'p':
                preview_command = self.highlight_case
                continue

            elif chosen_key == 'r':
                cm(self.vmnf_handler).load_case(case_id)
                continue

        return True    

