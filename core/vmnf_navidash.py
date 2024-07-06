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


from prompt_toolkit import prompt
import time

from pygments import formatters, highlight, lexers
from neotermcolor import cprint, colored as cl

from .vmnf_navi_cases import naviCases
from .vmnf_navicontrols import (
    normalize, 
    flush_all, 
    navialert, 
    build_options,
    navioptions_menu
)
from .vmnf_navioptions import *
from .vmnf_navi_siddhis import navisiddhis
from .vmnf_navi_sessions import naviSessions
from .vmnf_scan_tools import naviScan
from .navi.collections.handler import naviCollections
from .vmnf_navi_tools import navitools

from res.vmnf_banners import *

from ._dbops_.vmnf_dbops import VFDBOps
from pygments.util import ClassNotFound
from simple_term_menu import TerminalMenu
from os.path import dirname
from random import choice
from time import sleep
import subprocess
import yaml
import sys
import os

from datetime import datetime

class vimanadash:
    def __init__(self, vmnf_handler:dict):
        self.vmnf_handler = vmnf_handler
        self.accepted_keys = [
            'ctrl-r', 'ctrl-h', 'ctrl-y','enter', 
            'u', 'i', 'd', 'f', 'o', 's', 'p'
        ]
        self.hidden_options = []

        # load just specified resources $ vimana start --sessions
        self.startlr = vmnf_handler.get('start_resource')

    def table_exists(self, _table_):
        if isinstance(_table_, list):
            return all(VFDBOps().table_exists(table) and VFDBOps().getall(table) for table in _table_)
        else:
            return VFDBOps().table_exists(_table_) and VFDBOps().getall(_table_)

    def get_plugins(self):
        return (VFDBOps().list_resource('_SIDDHIS_',[]))

    def select(self,selected_plugin):
        return [p for p in self._plugins_ if p.name == selected_plugin]

    def manage(self):
        caller = sys.argv[0:-1]
        details_enabled = False
        preview_command = self.describe_resource
        self.lexer_style = 'Python3'
        self.cursor = '  '
        current_index = 2
        banner = 'default_naviban'
        menu_flag = ' ❖   '
        self.active_mode = 'default'
        
        self.settings = self.load_menu_settings()

        _catsymbol_ = {
            'collections':'❇',
            'sessions':'⚙',
            'plugins':'❖',
            'tools':'⚒',
            'scans':'🛡',
            'cases':'🗂'
        }

        while True:
            print('\033[2J\033[1;1H')
            _options_ = []
            self.res_info = {}
            self.syncdash()

            self.resources = {
                'collections': self._collections_,
                'sessions': self._sessions_,
                'plugins': self._siddhis_,
                'tools': self._tools_,
                'scans': self._scans_,
                'cases': self._cases_
            }

            for res_name,res_items in self.resources.items():

                # start navigation mode loading just specified resources
                if self.startlr:
                    if f"start_{res_name}" not in self.startlr:
                        continue

                symbol = _catsymbol_[res_name]
                self.res_info[res_name] = f"Manage {res_name}: {len(res_items)}" 

                if res_name not in self.hidden_options:
                    #_options_.append(f'{res_name:>24}   {symbol}         ')
                    _options_.append(f'{symbol:>17}  {res_name}        ')

            banner = globals().get(banner)
            banner('')
            banner = banner.__name__
