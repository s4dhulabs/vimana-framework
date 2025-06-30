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

    def highlight_plugin(self,plugin):
        plugin = plugin.split()[0].strip()
        selected_plugin = self.select(plugin)[0]
        tags = f"\n* Tags: {','.join(selected_plugin.tags)}"
        brief = "{{ " + selected_plugin.brief + " }}\n\n" 
        info = brief + selected_plugin.description + tags
        plugin_info = "\n".join(" " + line for line in info.split('\n'))

        lexer = lexers.get_lexer_by_name(
            self.lexer_style, 
            stripnl=False, 
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(plugin_info, lexer, formatter) 

    def handle_plugin(self, plugin):
        _options_ = []
        self.cursor = ''
        _ops_ = ['setup', 'guide', 'run']
        for op in _ops_:
            _options_.append(f'{op:>24}  ◉ ')

        current_index=0
        while True:
            print('\033[2J\033[1;1H')
            print(main_naviban)
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
            #selected_plugin = self._plugins_[plugin_index]
            current_index = terminal_menu.chosen_menu_index
            oper = _ops_[current_index]

            if oper == 'run':
                navi_siddhi_run(plugin).manage()
                continue

            elif oper == 'guide':
                navi_siddhi_guide(plugin).manage()
                continue
            elif oper == 'setup':
                set_args = navi_set_args(plugin)
                continue

            input()

    def load_menu_settings(self):
        try:
            with open(f'{dirname(__file__)}/navisettings.yaml', 'r') as f:
                settings = yaml.load(f,Loader=yaml.FullLoader)
        except FileNotFoundError:
            default_naviban()
            cprint(f'[{datetime.now()}] Error loading navisettings!','red')
            sys.exit(1)

        ss = settings['plugins']
        detailed = ss.get('detailed')
        default  = ss.get('default')

        self.detailed_headers = detailed.get('headers')
        self.detailed_filters = detailed.get('filters')

        self.default_headers = default.get('headers')
        self.default_filters = default.get('filters')

        return True

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
        preview_command = None

        
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
            header_size = len(header)

            kbann = normalize(
                header, hcolor, msg, show_banner,
                random_banner, keep_banner, header_size
            )
            keep_banner = kbann
            hintext = " "
            terminal_menu = TerminalMenu(
                plugin_options, 
                #preview_command=self.highlight_plugin, 
                preview_command=preview_command,
                preview_size=default_psize,
                preview_title='description',
                preview_border=40,
                menu_cursor = self.cursor,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys=['p', 'o','enter','s', 'g', 'r','c', 'y', 'b', 'd','i', 'ctrl-y'],
                cursor_index=current_index,
                raise_error_on_interrupt=False,
                #accept_sigwinch=False
            )
            
            plugin_index = terminal_menu.show()
            if plugin_index is None:
                print('\033[2J\033[1;1H')
                break
       
            chosen_key = terminal_menu._chosen_accept_key
            selected_entry = terminal_menu.chosen_menu_entry
            selected_plugin = self._plugins_[plugin_index]
            current_index = terminal_menu.chosen_menu_index
            
            if chosen_key == 'enter':
                self.cursor = choice(cursor_options)
                self.handle_plugin(selected_plugin)
                continue

            elif chosen_key == 'c':
                set_args = navi_set_args(selected_plugin)
                input(set_args)
                continue
            
            elif chosen_key == 'i':
                current_headers = self.detailed_headers
                current_filters = self.detailed_filters
                default_psize = 0.85
                continue

            elif chosen_key == 'd':
                current_headers = self.default_headers
                current_filters = self.default_filters
                default_psize = 0.35
                continue

            elif chosen_key == 'ctrl-y':
                self.lexer_style = choice(srandlexers)
                self.cursor = choice(cursor_options)
                hcolor=choice(range(12))
                continue
            
            elif chosen_key == 'o':
                navioptions_menu('plugins_main_menu')
                continue

            elif chosen_key == 'g':
                navi_siddhi_guide(selected_plugin).manage()
                continue

            elif chosen_key == 'r':
                navi_siddhi_run(selected_plugin).manage()
                continue

            elif chosen_key == 'p':
                preview_command = self.highlight_plugin
                continue

