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


class navitools:
    def __init__(self, vmnf_handler:dict):
        self.vmnf_handler = vmnf_handler
        #self._plugins_ = self.get_plugins()
    
    def get_plugins(self):
        return (VFDBOps().list_resource('_SIDDHIS_',[]))

    def select(self,selected_plugin):
        return [p for p in self._plugins_ if p.name == selected_plugin]

    def manage(self,oper:str=False):

        self.lexer_style = 'Asc'
        self.cursor = '❖ '
        current_index = 0
        hcolor = 'green'
        random_banner = 'default_naviban'
        msg = f"{self.cursor} tools"
        show_banner = True
        keep_banner = 'default_naviban'
        default_psize = 0.35

        all_tools = VFDBOps().list_resource('_TOOLS_',[])
        self.selected_tools = []

        if oper:
            for tool in all_tools:
                # if the selected collection is in the scope of the current tool
                if oper in tool.scope:
                    self.selected_tools.append(tool)
        else:
            self.selected_tools = all_tools

        if self.vmnf_handler.get('keep_banner', False):
            keep_banner = self.vmnf_handler['keep_banner']
        
        if not self.load_menu_settings():
            return False

        current_headers = self.default_headers
        current_filters = self.default_filters
