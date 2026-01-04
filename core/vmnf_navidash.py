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


from prompt_toolkit import prompt
import time

from pygments import formatters, highlight, lexers
from neotermcolor import cprint, colored as cl

from .vmnf_navi_cases import naviCases
from .vmnf_navicontrols import (
    normalize, 
    flush_all, 
    navialert, 
    build_options,
    navioptions_menu
)
from .vmnf_navioptions import *
from .vmnf_navi_siddhis import navisiddhis
from .vmnf_navi_sessions import naviSessions
from .vmnf_scan_tools import naviScan
from .navi.collections.handler import naviCollections
from .vmnf_navi_tools import navitools

from res.vmnf_banners import *

from ._dbops_.vmnf_dbops import VFDBOps
from pygments.util import ClassNotFound
from simple_term_menu import TerminalMenu
from os.path import dirname
from random import choice
from time import sleep
import subprocess
import yaml
import sys
import os

from datetime import datetime

class vimanadash:
    def __init__(self, vmnf_handler:dict):
        self.vmnf_handler = vmnf_handler
        self.accepted_keys = [
            'ctrl-r', 'ctrl-h', 'ctrl-y','enter', 
            'u', 'i', 'd', 'f', 'o', 's', 'p'
        ]
        self.hidden_options = []

        # load just specified resources $ vimana start --sessions
        self.startlr = vmnf_handler.get('start_resource')

    def table_exists(self, _table_):
        if isinstance(_table_, list):
            return all(VFDBOps().table_exists(table) and VFDBOps().getall(table) for table in _table_)
        else:
            return VFDBOps().table_exists(_table_) and VFDBOps().getall(_table_)

    def get_plugins(self):
        return (VFDBOps().list_resource('_SIDDHIS_',[]))

    def select(self,selected_plugin):
        return [p for p in self._plugins_ if p.name == selected_plugin]

    def describe_resource(self, resource):
        res_items = []
        ident = ' '*10
        resource = resource.split()[1].strip()
        res_desc = self.res_info.get(resource)

        if resource in ['collections']:
            for c_type, c_items in self.collection_control.items():
                res_items.append(f"  →  {c_type}: {len(c_items)}")
        else:
            res_items = self.resources.get(resource)

        res_info = ",".join(ident + str(i) for i in res_items)
        res_info = res_info.replace(',','\n')
        res_info = ident + res_desc + '\n\n' + res_info

        lexer = lexers.get_lexer_by_name(
            self.lexer_style, 
            stripnl=False, 
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(res_info, lexer, formatter) 


    def syncdash(self):
        """
        Synchronize and update resource data based on specified options.

        This method synchronizes the internal state of the object by fetching and refreshing resource data from a database.
        
        :return: None
        
        Resources:
        
        - 'scans': Updates '_scans_' attribute with data from '_SCANS_' table.
        - 'sessions': Updates '_sessions_' attribute with data from '_SESSIONS_' table.
        - 'plugins': Updates '_siddhis_' attribute with data from '_SIDDHIS_' table.
        - 'cases': Updates '_cases_' attribute with data from '_CASES_' table.
        - 'collections': Updates '_collections_' attribute with combined data from '_EXCEPTIONS_', '_TICKETS_', and '_CVES_'
            tables. Individual collections are accessible through the 'collection_control' attribute, with keys 'exceptions',
            'tickets', and 'cves'.

        Conditions:
        
        - Hidden options are checked to exclude certain resources.
        - The 'startlr' attribute is consulted to determine which resources to update.
        - For each resource, it checks if the corresponding table exists using the 'VFDBOps' class's 'table_exists' method.
            - The 'table_exists' method in 'VFDBOps' relies on SQLAlchemy's 'inspect' function to check table existence.
            - If a single table is provided, it checks if the table exists.
            - If a list of tables is provided, it checks if all tables in the list exist and have data using 'all'.

        Note: Requires a VFDBOps class with appropriate methods for table existence checks and resource data retrieval.

        """

        self._scans_ = []
        self._sessions_ = []
        self._siddhis_  = []
        self._cases_ = []
        self._collections_  = []
        self._tools_  = []
        self.collection_control = {}

        resource_mapping = {
            'scans': ('_SCANS_', '_scans_', 'start_scans'),
            'sessions': ('_SESSIONS_', '_sessions_', 'start_sessions'),
            'plugins': ('_SIDDHIS_', '_siddhis_', 'start_plugins'),
            'cases': ('_CASES_', '_cases_', 'start_cases'),
            'tools': ('_TOOLS_', '_tools_', 'start_tools')
        }

        for resource, (table_name, attribute_name, start_option) in resource_mapping.items():
            if resource not in self.hidden_options:
                if self.table_exists(table_name) and (not self.startlr or (start_option in self.startlr)):
                    setattr(self, attribute_name, VFDBOps().list_resource(table_name, []))

        if 'collections' not in self.hidden_options and (not self.startlr or 'start_collections' in self.startlr):
            collection_types = ['_EXCEPTIONS_', '_TICKETS_', '_CVES_']

            for collection_type in collection_types:
                if self.table_exists(collection_type):
                    collection_data = VFDBOps().list_resource(collection_type, [])
                else:
                    collection_data = []

                setattr(self, f'_{collection_type.lower()}_', collection_data)
                self._collections_.append(collection_data)
                self.collection_control[collection_type.lower()[1:-1]] = collection_data

    def load_menu_settings(self):
        try:
            with open(f'{dirname(__file__)}/navisettings.yaml', 'r') as f:
                settings = yaml.load(f,Loader=yaml.FullLoader)
        except FileNotFoundError:
            os.system('clear')
            default_naviban()
            cprint(f'[{datetime.now()}] Error loading navisettings!\n\n', 'red')
            sys.exit(1)
        
        return settings 

    def set_resource_settings(self, resource):
        try:
            ss = self.settings[resource]
        except:
            return False

        detailed = ss.get('detailed')
        default  = ss.get('default')

        self.detailed_headers = detailed.get('headers')
        self.detailed_filters = detailed.get('filters')

        self.default_headers = default.get('headers')
        self.default_filters = default.get('filters')

        return True

    def enable_preview(self, resource):
        ident = ''
        resource = resource.split()[1].strip()
        res_items = self.resources.get(resource)
        
        if not self.set_resource_settings(resource):
            return self.describe_resource(resource)
      
        if self.active_mode == 'detailed':
            current_headers = self.detailed_headers
            current_filters = self.detailed_filters
        else:
            current_headers = self.default_headers
            current_filters = self.default_filters

        _options_, header = build_options(
            res_items,
            current_headers,
            current_filters
        )
        
        #res_desc = self.res_info.get(resource)
        res_desc = header
        
        res_info = "$$".join('  ' + str(i) for i in _options_)
        res_info = res_info.replace('$$','\n')
        res_info = ident + res_desc + '\n\n' + res_info

        lexer = lexers.get_lexer_by_name(
            self.lexer_style, 
            stripnl=False, 
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(res_info, lexer, formatter) 

    def manage(self):
        caller = sys.argv[0:-1]
        details_enabled = False
        preview_command = self.describe_resource
        self.lexer_style = 'Python3'
        self.cursor = '  '
        current_index = 2
        banner = 'default_naviban'
        menu_flag = ' ❖   '
        self.active_mode = 'default'
        
        self.settings = self.load_menu_settings()

        _catsymbol_ = {
            'collections':'❇',
            'sessions':'⚙',
            'plugins':'❖',
            'tools':'⚒',
            'scans':'🛡',
            'cases':'🗂'
        }

        while True:
            print('\033[2J\033[1;1H')
            _options_ = []
            self.res_info = {}
            self.syncdash()

            self.resources = {
                'collections': self._collections_,
                'sessions': self._sessions_,
                'plugins': self._siddhis_,
                'tools': self._tools_,
                'scans': self._scans_,
                'cases': self._cases_
            }

            for res_name,res_items in self.resources.items():

                # start navigation mode loading just specified resources
                if self.startlr:
                    if f"start_{res_name}" not in self.startlr:
                        continue

                symbol = _catsymbol_[res_name]
                self.res_info[res_name] = f"Manage {res_name}: {len(res_items)}" 

                if res_name not in self.hidden_options:
                    #_options_.append(f'{res_name:>24}   {symbol}         ')
                    _options_.append(f'{symbol:>17}  {res_name}        ')

            banner = globals().get(banner)
            banner('')
            banner = banner.__name__
            
            list_menu = TerminalMenu(
                _options_, 
                preview_command=preview_command, 
                #preview_size=0.1,
                preview_title='─',
                preview_border=0.1,
                menu_cursor = self.cursor,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys=self.accepted_keys,
                cursor_index=current_index,
                raise_error_on_interrupt=False
            )
            
            list_index = list_menu.show()

            if list_index is None:
                print('\033[2J\033[1;1H')
                break

            current_index = list_index
            chosen_key = list_menu._chosen_accept_key
            selected_option = list_menu.chosen_menu_entry
            oper = selected_option.split()[1].strip()
            table = oper
            items = self.resources.get(oper)
            n_items = len(items)

            try:
                active_preview = preview_command.__name__
            except AttributeError:
                active_preview = None
                pass
            
            # main dash options
            if chosen_key == 'o':
                navioptions_menu('dash_main_menu', 'dashboard → options')
                continue
            
            # hide options
            elif chosen_key == 'ctrl-h':
                self.hidden_options.append(oper)
                continue
            
            # reset to default dash
            elif chosen_key == 'ctrl-r':
                self.hidden_options = []
                self.active_mode = 'default'
                preview_command = self.describe_resource
                continue

            elif chosen_key == 'p':
                continue

            elif chosen_key == 'f':
                if table == 'tools':    
                    #input('Are you sure you want to flush all tools?')
                    continue

                if table == 'plugins':
                    table = 'siddhis'
                
                table = f'_{table.upper()}_'
                
                if n_items == 0:
                    navialert(f'No {oper} found, s4dhu!')
                    continue

                action_confirmed = flush_all(items, oper)
                
                if not action_confirmed:
                    continue

                status = VFDBOps().clean_table(table)
                #self.get_updated_res()

                if not status:
                    input(f' Something went wrong while trying to flush {oper}')
                continue
        
            elif chosen_key == 'ctrl-y':
                banner = choice(banner_options)
                menu_flag = choice(cursor_options)
                self.lexer_style = choice(srandlexers)
                self.cursor = choice(cursor_options)
                hcolor=choice(range(12))
                continue

            elif chosen_key == 'i':
                if active_preview == 'enable_preview':
                    self.active_mode = 'detailed'

                elif active_preview == 'describe_resource':
                    self.active_mode = 'default'
                    preview_command = self.enable_preview

                elif not active_preview:
                    self.active_mode = 'default'
                    preview_command = self.describe_resource
                
                continue

            elif chosen_key == 'd':
                if active_preview == 'enable_preview':
                    if self.active_mode == 'detailed':
                        self.active_mode = 'default'
                        
                    elif self.active_mode == 'default':
                        preview_command = self.describe_resource

                elif active_preview == 'describe_resource':
                    preview_command = None

                elif active_preview is None:
                    print('\033[2J\033[1;1H')
                    subprocess.run(caller)
                    break

                continue

            if chosen_key == 'enter' and n_items == 0:
                navialert(f'No {oper} found, s4dhu!')
                continue


            self.vmnf_handler['keep_banner'] = banner

            if oper == 'plugins':
                if not self._siddhis_:
                    input('nothing to show here sadhu')
                    continue
                navisiddhis(self.vmnf_handler).manage()

            elif oper == 'scans':
                naviScan(self.vmnf_handler).manage()

            elif oper == 'sessions':
                naviSessions(self.vmnf_handler).manage()

            elif oper == 'cases':
                if not self._cases_:
                    cprint('No cases found, s4dhu!', 'red')
                    input()
                    continue
                naviCases(self.vmnf_handler).manage()

            elif oper == 'collections':
                naviCollections(self.vmnf_handler).manage()

            elif oper == 'tools':
                navitools(self.vmnf_handler).manage(False)