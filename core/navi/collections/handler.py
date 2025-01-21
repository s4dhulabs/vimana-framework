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


from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit import print_formatted_text

from pygments import formatters, highlight, lexers
from neotermcolor import cprint, colored as cl
from simple_term_menu import TerminalMenu

import os
import yaml
from time import sleep
from random import choice
from os.path import dirname
from ...vmnf_navioptions import *
from ...vmnf_navicontrols import *
from ..._dbops_.vmnf_dbops import VFDBOps
from ...vmnf_sessions import VFSession
from pygments.util import ClassNotFound

from res.vmnf_banners import *
from urllib.parse import urlparse, urljoin
from datetime import datetime
from .exceptions import xc_handler


class naviCollections:
    def __init__(self, vmnf_handler:dict):

        self.vmnf_handler = vmnf_handler
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

    def load_menu_settings(self):
        try:
            with open(f'{dirname(__file__)}/navisettings.yaml', 'r') as f:
                settings = yaml.load(f,Loader=yaml.FullLoader)
        except FileNotFoundError:
            os.system("clear")
            default_naviban()
            cprint(f'[{datetime.now()}] Error loading navisettings!','red')
            sys.exit(1)
        
        ss = settings['sessions']
        detailed = ss.get('detailed')
        default  = ss.get('default')

        self.detailed_headers = detailed.get('headers')
        self.detailed_filters = detailed.get('filters')
        self.default_headers = default.get('headers')
        self.default_filters = default.get('filters')

        return True

    def manage(self):
        _options_ = []
        current_index=0
        self.cursor = '❇   '
        keep_banner = 'default_naviban'
        banner = keep_banner
        _ops_ = ['Credentials', 'Tickets', 'Snippets', 'Exceptions', 'Objects', "CVE's", "URL's"]

        _catsymbols_ = {
            'Exceptions': '🚫',
            #'Credentials': '🔐',
            #'Snippets': '📄',
            #'Variables': '📚',
            #'Queries': '🔍',
            #'Techs': '💻',
            #'Tickets': '🎫',
            #'CVEs': '🛡️',
            #'URLs': '🔗'
        }

        for cat, symbol in _catsymbols_.items():
            _options_.append(f'{cat:>23}  {symbol}        ')
        
        if self.vmnf_handler.get('keep_banner', False):
            keep_banner = self.vmnf_handler['keep_banner']
            banner = keep_banner
            
        while True:
            print('\033[2J\033[1;1H')
            banner = globals().get(banner)
            banner('')
            banner = banner.__name__

            fmsg = FormattedText([('ansibrightblack',f"{'❇ Collections':>28}")])
            print_formatted_text(fmsg)
            print()

            terminal_menu = TerminalMenu(
                _options_,
                menu_cursor = self.cursor,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys=['enter', 'r', 'o', 'ctrl-y'],
                cursor_index=current_index,
                raise_error_on_interrupt=False
            )

            plugin_index = terminal_menu.show()
            if plugin_index is None:
                print('\033[2J\033[1;1H')
                break

            chosen_key = terminal_menu._chosen_accept_key
            selected_entry = terminal_menu.chosen_menu_entry
            current_index = terminal_menu.chosen_menu_index
            oper = [c for c in _catsymbols_][current_index].lower()

            if chosen_key == 'r':
                from ...vmnf_navi_tools import navitools
                navitools(self.vmnf_handler).manage(oper)

            elif chosen_key == 'o':
                navioptions_menu('collections_main_menu')
            
            elif chosen_key == 'ctrl-y':
                banner = choice(banner_options)
                menu_flag = choice(cursor_options)
                self.lexer_style = choice(srandlexers)
                self.cursor = choice(cursor_options)
                hcolor=choice(range(12))
                continue

            elif chosen_key == 'enter':
                if oper == 'exceptions':
                    xc_handler(self.vmnf_handler).manage()
                    continue
                else:
                    input(f"    >>> This resource is not available yet! Press Enter to continue...")
            
            
