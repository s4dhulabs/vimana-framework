# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Site: https://sadhulabs.substack.com/
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

    def load_menu_settings(self):
        try:
            with open(f'{dirname(__file__)}/navisettings.yaml', 'r') as f:
                settings = yaml.load(f,Loader=yaml.FullLoader)
        except FileNotFoundError:
            os.system('clear')
            default_naviban()
            cprint(f'[{datetime.now()}] Error loading navisettings!','red')
            sys.exit(1)

