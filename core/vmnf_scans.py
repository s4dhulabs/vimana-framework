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

from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from pygments import highlight
from tabulate import tabulate

from core._dbops_.db_utils import get_elapsed_time
from core.vmnf_sessions_utils import abduct_items
from core._dbops_.vmnf_dbops import VFDBOps
from core.vmnf_scan_tools import naviScan

from siddhis.viewscan.tools.vs_tools import get_object_issues
from scrapy.utils.serialize import ScrapyJSONEncoder
from neotermcolor import cprint, colored as cl
from simple_term_menu import TerminalMenu
from datetime import datetime,timezone
from core.load_settings import _vfs_
from urllib.parse import urlparse
from res.vmnf_banners import *
from random import choice
from time import sleep
import jsonpickle
import hashlib
import json
import yaml
import glob
import sys
import io
import os


class VFScan:
    def __init__(self, **vmnf_handler):
        self.navigation_enabled = vmnf_handler['navigation_mode']
        self.vmnf_handler = vmnf_handler
        self.encoder = ScrapyJSONEncoder()
        self.flush_mode = False
        self.model = '_SCANS_'
        self.obj_id_col = 'scan_id'

    def get_last_scan(self):
        try:
            return sorted(self._scans_, key=lambda r: r.scan_date, reverse=True)[0].scan_date
        except (IndexError,TypeError):
            cprint("        It seems like you haven't performed any security scans lately.  \n", 'blue')
            os._exit(os.EX_OK)

    def list_scans(self, headless=False):
        if self.vmnf_handler['navigation_mode']:
            naviScan(self.vmnf_handler).manage()
            return 

        _options_ = []
        self.query_filters = []
        self._scans_ = (VFDBOps().list_resource(self.model, self.query_filters))
        
        attrs = []
        clc  = 'white'
        
        if not headless:
            print("\033c", end="")
            case_header()
        
        self.scans_tbl =[]
        self.scans_tbl.append(
            [
                cl('ID', 'cyan', attrs=[]),
                cl('Type','cyan', attrs=[]),
                cl('Project','cyan', attrs=[]),
                cl('Framework','cyan', attrs=[]),
                cl('CVEs','cyan', attrs=[]),
                cl('Modules','cyan', attrs=[]),
                cl('Date','cyan', attrs=[]),
            ]
        )

        latest_scan = self.get_last_scan()

        for _sc_ in self._scans_:
            color = None
            attrs=[]
            
            if _sc_.scan_date == latest_scan:
                color = 'green'
                attrs=['bold']

            elapsed = get_elapsed_time(_sc_)
            project_framework = f"{_sc_.project_framework} ({_sc_.project_framework_version})"
            
            self.scans_tbl.append(
                [
                    cl(_sc_.scan_id,color,attrs=attrs), 
                    cl(_sc_.scan_type,color,attrs=attrs), 
                    cl(_sc_.scan_target_project,color,attrs=attrs), 
                    cl(project_framework,color,attrs=attrs), 
                    cl(_sc_.project_framework_total_cves,color,attrs=attrs),
                    cl(_sc_.project_total_view_modules,color,attrs=attrs),
                    cl(elapsed,color,attrs=attrs)
                ]
            )

        print(tabulate(
            self.scans_tbl,
            headers='firstrow',
            numalign="left",
            tablefmt='pretty',missingval='?'
            )
        )
        print('\n\n') 
    
