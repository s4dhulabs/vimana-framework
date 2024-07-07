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
from neotermcolor import cprint, colored as cl
from .vmnf_navicontrols import *
from ._dbops_.vmnf_dbops import VFDBOps
from .vmnf_navi_banners import main_naviban
from pygments.util import ClassNotFound
from simple_term_menu import TerminalMenu
from datetime import datetime
from os.path import dirname
from .vmnf_navioptions import *
from random import choice
from time import sleep
import yaml
import os

from ._dbops_.models.siddhis import Siddhis
from .vmnf_navi_guides import navi_siddhi_guide
from .vmnf_navi_runs import navi_siddhi_run


class navisiddhis:
    def __init__(self, vmnf_handler:dict):
        self.vmnf_handler = vmnf_handler
        self._plugins_ = self.get_plugins()
    
    def get_plugins(self):
        return (VFDBOps().list_resource('_SIDDHIS_',[]))

    def select(self,selected_plugin):
        return [p for p in self._plugins_ if p.name == selected_plugin]

    def manage(self):
        self.lexer_style = 'Asc'
        self.cursor = '❖ '
        current_index = 0
        hcolor = 'green'
        random_banner = False
        msg = f"{self.cursor} plugins"
        show_banner = False
        keep_banner = 'case_header'
        default_psize = 0.35
        
        if not self.load_menu_settings():
            return False

        current_headers = self.default_headers
        current_filters = self.default_filters

        while True:
            print('\033[2J\033[1;1H')
            
            plugin_options, header = build_options(
                self._plugins_,
                current_headers,
                current_filters
            )
