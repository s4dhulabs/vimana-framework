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
from simple_term_menu import TerminalMenu

from .vmnf_navicontrols import *
from ._dbops_.vmnf_dbops import VFDBOps
from .vmnf_sessions import VFSession
from pygments.util import ClassNotFound

from .vmnf_navioptions import *
from os.path import dirname
from random import choice
from time import sleep
import yaml
import os
#from .vmnf_navi_banners import default_naviban
from res.vmnf_banners import *
from urllib.parse import urlparse, urljoin
from datetime import datetime

vimana_path = os.getenv("vimana_path")


class naviSessions:
    def __init__(self, vmnf_handler:dict):
        self.vmnf_handler = vmnf_handler
        #self._sessions_ = self.get_sessions()
        self.model = '_SESSIONS_'
        self.obj_id_col = 'session_id'

    def get_sessions(self):
        return (VFDBOps().list_resource('_SESSIONS_',[]))

    def select(self,session_id):
        return [s for s in self._sessions_ if s.session_id == session_id]

    def highlight_session(self,session):
        session_id = session.split()[0].strip()
        selected_session = self.select(session_id)[0]
        session_info = "\n".join([f"{k:>25}:    {v}" for k, v in selected_session.__dict__.items()])

        lexer = lexers.get_lexer_by_name(
            self.lexer_style, 
            stripnl=False, 
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(session_info, lexer, formatter) 

    def manage_session(self, session):
        _options_ = []
        current_index=0
        _ops_ = ['overview', 'exceptions', 'CVEs', 'tickets', 'URLs', 'FuzzL0g']
        
        
        with open(session.session_path, 'r') as s:
            session = yaml.unsafe_load(s)

        report_tables = session['report_tables']
        djunch_result = session['djunch_result']
        patterns = session['patterns']
        overview = session['issues_overview']
        target_url = session['target_url']
        framework = f"{session['framework']} {session['framework_version']}"

        URLs = [urljoin(target_url, p) for p in patterns] 

        
