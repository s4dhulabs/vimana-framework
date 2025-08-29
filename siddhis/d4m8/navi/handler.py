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

'''
from ..tools.vs_tools import (
    get_mod_hash
)

from siddhis.viewscan.tools.vs_tools import (
    get_object_issues, 
    handle_sast_output
)
'''

from core.navi.collections.exceptions import xc_handler
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

vimana_path = os.getenv("VIMANA_PATH") or os.getenv("vimana_path")

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

    def manage_scan(self, _scan_, keep_banner:False) -> Union[Tuple[str, str, str], bool]:
        # using collections exception handler to manage d4m8 exceptions 
        # passing the scan id as reference to filter 
        xc_handler(self.vmnf_handler).manage(_scan_.scan_id)

    def manage_scan1(self, _scan_, keep_banner:False) -> Union[Tuple[str, str, str], bool]:

        """
        """

        scan_objects = jsonpickle.decode(_scan_.__dict__['scan_scope'])

        with open(_scan_.scan_output_file, 'r') as file:
            yaml_data = file.read()

        deserialized_data = yaml.load(yaml_data, Loader=yaml.SafeLoader)
        deserialized_data = jsonpickle.decode(deserialized_data)
    
        _apps_ = []
        found_categories = []

        for exception in  deserialized_data:
            trigger_line = '' 
            xtype = exception['summary']['Exception Type']
            xvalue = exception['summary']['Exception Value'][0]
            xmethod = exception['summary']['Request Method']
            xcategory = exception['summary']['Category']
            module = exception['view_trigger']['shortpath']
            function = exception['view_trigger']['object']
            line_number = exception['view_trigger']['line_number']

            xpress = (
                f"{xtype}{' '*(30 - (len(xtype)))} {module} "
                f"{' '*(23 - (len(module)))} {function} "
                f"{' '*(18 - (len(function)))} {line_number} "
                f"{' '*(10 - (len(line_number)))} {xmethod} "
                f"{xvalue}"
            )


            _apps_.append(xpress)
            

        while True:
            """
            jazzit(f"[{scan_id}]→ {project} ", f"[{scan_id}]", keep_banner)
            _apps_ = list_files(cache_dir)
            _apps_ = [' ' + app for app in _apps_ if not app.endswith('.sarif')]
            self._total_apps_ = len(_apps_)
            """

            apps_menu = TerminalMenu(
                _apps_,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys
            )
            app_index = apps_menu.show()
            chosen_key = apps_menu._chosen_accept_key

            if app_index is None:
                break
    
            input(_apps_[app_index])
            continue
