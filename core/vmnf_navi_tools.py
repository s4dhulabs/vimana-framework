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

    def highlight_plugin(self, tool):
        tool = tool.split()[0].strip()
        tool = [t for t in self.selected_tools if t.name == tool][0]
        tool_name = tool.full_name
        tool_desc = tool.description
        tool_brief = tool.brief
        tool_scope = ', '.join(tool.scope)

        tool_header = f"  {tool_name} - {tool_brief}\n\n"
        tool_info = tool_header + ".\n".join(" " + l for l in tool_desc.split('.'))
        tool_info = tool_info + f"\n\n  Scope: {tool_scope}\n\n"
        
        lexer = lexers.get_lexer_by_name(
            self.lexer_style, 
            stripnl=False, 
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(tool_info, lexer, formatter) 

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
            oper = _ops_[current_index]

            if oper == 'runs':
                navi_siddhi_run(plugin).manage()
                continue

            elif oper == 'guide':
                navi_siddhi_guide(plugin).manage()
                continue

            elif oper == 'setup':
                set_args = navi_set_args(plugin)
                #input(set_args)
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

        ss = settings['tools']
        detailed = ss.get('detailed')
        default  = ss.get('default')

        self.detailed_headers = detailed.get('headers')
        self.detailed_filters = detailed.get('filters')
        self.default_headers = default.get('headers')
        self.default_filters = default.get('filters')

        return True

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
        preview_command = None

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

        while True:
            print('\033[2J\033[1;1H')
            
            tool_options, header = build_options(
                self.selected_tools,
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
                tool_options, 
                #preview_command=self.highlight_plugin, 
                preview_command=preview_command,
                preview_size=default_psize,
                preview_title='details',
                preview_border=40,
                menu_cursor = self.cursor,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys=['o','enter','s', 'g', 'r','c', 'ctrl-y', 'd', 'i','p'],
                cursor_index=current_index,
                raise_error_on_interrupt=False
            )
            
            tool_index = terminal_menu.show()

            if tool_index is None:
                print('\033[2J\033[1;1H')
                break
       
            chosen_key = terminal_menu._chosen_accept_key
            selected_entry = terminal_menu.chosen_menu_entry
            selected_tool = [self.selected_tools[tool_index]]
            current_index = terminal_menu.chosen_menu_index
            
            dashtools = False
            if chosen_key == 'enter':
                print('\033[2J\033[1;1H')
                banner = globals().get(keep_banner)
                banner('')

                import importlib
                from pathlib import Path
                tools_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))

                # needs to check if it is a valid collection category ['exceptions', 'requests', etc]
                if not oper:
                    dashtools = True
                    # if there is no oper, it means we got here by dash → tools → enter
                    # so we need to get the scope of the selected tool as the oper ['exceptions', 'requests', etc]
                    oper = selected_tool[0].scope

                if dashtools:
                    data = []
                    for o in oper:
                        try:
                            data.extend(VFDBOps().list_resource(f'_{o.upper()}_',[]))
                        except TypeError:
                            continue
                else:
                    try:
                        data = VFDBOps().list_resource(f'_{oper.upper()}_',[])
                    except AttributeError:
                        pass

                for tool in selected_tool:
                    module_name = f"tools.{tool.name}"
                    tool_path = os.path.join(tools_dir, f"{tool.name}.py")
                    spec = importlib.util.spec_from_file_location(module_name, tool_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    ToolClass = getattr(module, 'tool')
                    ToolClass().run(data)
                
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
                keep_banner = False
                random_banner=True
                self.cursor = choice(cursor_options)
                self.lexer_style = choice(srandlexers)
                hcolor=choice(range(321))
                continue
            
            elif chosen_key == 'o':
                navioptions_menu('tools_main_menu')
                continue

            elif chosen_key == 'p':
                preview_command = self.highlight_plugin
                continue

