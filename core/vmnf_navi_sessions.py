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

vimana_path = os.getenv("VIMANA_PATH") or os.getenv("vimana_path")


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

        for op in _ops_:
            _options_.append(f'{op:>24}  ✺ ')

        while True:
            print('\033[2J\033[1;1H')
            default_naviban()
            terminal_menu = TerminalMenu(
                _options_,
                #preview_command=self.highlight_plugin,
                #preview_size=0.75,
                #preview_title='description',
                #preview_border=40,
                menu_cursor = self.cursor,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys=['enter'],
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
            oper = _ops_[current_index].lower()

            if oper == 'overview':
                print(djunch_result['_count_issues_'])
                input(f"lets show overview")
                continue
            
            elif oper == 'fuzzl0g':
                for e in djunch_result['FUZZ_STATUS_LOG']:
                    for k,v in e.items():
                        print(f"{k:>20}: {v}")
                input()
                continue

            elif oper == 'cves':
                cprint(f" → CVEs for {framework}", 'green')
                print(report_tables['cves'])
                input(f"lets show cves")
                continue

            elif oper == 'exceptions':
                print(report_tables['exceptions'])

                input(f"exceptions")
                continue

            elif oper == 'urls':
                print(session['fingerprint'])

                for i,url in enumerate(URLs):
                    print(f"    {cl(url, 'green')}")

                input(f"urls")
                continue

            elif oper == 'tickets':
                cprint(f" → Security Tickets for {framework}", 'green')
                print(report_tables['tickets'])
                input(f"tickets")
                continue

            input()

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
        self.lexer_style = 'Asc'
        self.cursor = '⚙ '
        current_index = 0
        hcolor = 'green'
        random_banner = 'default_naviban'
        msg = '⚙ sessions'
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
            self._sessions_ = self.get_sessions()
            _options_, header = build_options(
                self._sessions_, 
                current_headers, 
                current_filters
            )
            total_sessions = len(self._sessions_)
            header_size = len(header)

            print('\033[2J\033[1;1H')
            hintext = " "
            terminal_menu = TerminalMenu(
                _options_, 
                preview_command=preview_command,
                #preview_command=self.highlight_session, 
                preview_size=0.75,
                preview_title='session details',
                preview_border=40,
                menu_cursor = self.cursor,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys=['d', 'u', 'i', 'o', 'f', 'l', 's', 'd', 'enter', 'ctrl-y', 'p'],
                cursor_index=current_index,
                raise_error_on_interrupt=False
            )

            kbann = normalize(
                header, hcolor, msg, show_banner, 
                random_banner, keep_banner, header_size
            )
            keep_banner = kbann
            session_index = terminal_menu.show()
            if session_index is None:
                print('\033[2J\033[1;1H')
                break
       
            chosen_key = terminal_menu._chosen_accept_key
            selected_entry = terminal_menu.chosen_menu_entry
            selected_session = self._sessions_[session_index]
            current_index = terminal_menu.chosen_menu_index
            session_id = selected_session.session_id

            if chosen_key == 'ctrl-y':
                keep_banner = False
                random_banner=True
                self.cursor = choice(cursor_options)
                self.lexer_style = choice(srandlexers)
                hcolor=choice(range(321))
                continue
            
            elif chosen_key == 'p':
                preview_command = self.highlight_session
                continue

            elif chosen_key == 'o':
                navioptions_menu('sessions_main_menu')
                continue
            
            elif chosen_key == 'l':
                print('\033[2J\033[1;1H')
                default_naviban()

                for k,v in selected_session.__dict__.items():
                    if k in ['session_hash','session_path', 'id', 'session_file', '_sa_instance_state']:
                        continue

                    print(f"{colored(k,12):>40}: {v}")
                    sleep(0.01)

                print()
                sleep(1)

                VFSession(**self.vmnf_handler).load_session(selected_session)
                continue

            elif chosen_key == 'f':
                input('lets flush session')

                VFDBOps().flush_resource(self.model,self.obj_id_col, session_id)
                _options_ = [s for s in _options_ \
                        if s.split()[0].strip() != session_id
                    ]

                total_sessions -=1
                if total_sessions == 0:
                    break

                continue
            
            elif chosen_key == 'i':
                current_headers = self.detailed_headers
                current_filters = self.detailed_filters
                continue
            
            elif chosen_key == 'd':
                current_headers = self.default_headers
                current_filters = self.default_filters
                continue

            elif chosen_key == 'enter':
                self.manage_session(selected_session)
                continue

            continue

     



