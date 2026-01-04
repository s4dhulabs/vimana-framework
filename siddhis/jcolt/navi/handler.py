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
import asyncio



from siddhis.viewscan.tools.vs_tools import (
    get_object_issues, 
    handle_sast_output
)

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
from random import choice
from time import sleep
import jsonpickle
import inspect
import shutil
import yaml
import json
import sys
import io
import os

from ..utils import *
from .displays import PopupDisplay
from ..cmd.list import jcList
from ..cmd.show import jcShow


vimana_path = os.getenv("VIMANA_PATH") or os.getenv("vimana_path")

class navi_handler:
    def __init__(self, vmnf_handler:dict) -> None:
        self.vmnf_handler = vmnf_handler
        self.health_check = []
        self.prompt = '➤ '
        self.accepted_keys = (
            "enter", "o", "f", "t","r","s","d", "b", "u", 'y', 'p', 'ctrl-y','i'
        )
        self.model = '_SCANS_'
        self.obj_id_col = 'scan_id'
        self.schema = self.vmnf_handler['schema']
        self.jc_list = jcList(self.schema)
        self.spec_parameters = self.jc_list.list_parameters()
        #input(self.spec_parameters)
        self.jc_show = jcShow(30, True)
        self.set_param_scope = self.vmnf_handler.get('set_param_scope')

    def get_reason(self, response):
        import http
        return http.HTTPStatus(response.status).phrase
    
    def enable_preview(self,test_case):
        selected_endpoint = test_case.split()[1]
        if self.set_param_scope:
            tests = [t[0] for p, t in self.fuzz_results.items() 
                if t[0].get('spec_path') == selected_endpoint]
        else:
            tests = self.fuzz_results[selected_endpoint]

        teste_info = "\n".join(
            [
                f"Req {_}: "
                f"{t['method'].upper()} {t['path']} → "
                f"Status: {t['response'].status} "
                f"{self.get_reason(t['response'])}: "
                f"RL: {t['response'].content_length } /" 
                f"RT: {t['response_time']}"
                for _,t in enumerate(tests,1)
            ]
        )

        lexer = lexers.get_lexer_by_name(
            self.lexer_style, 
            stripnl=False, 
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(teste_info, lexer, formatter) 
    
    def get_terminal_height(self):
        return shutil.get_terminal_size().lines
    
    def load_menu_settings(self):
        m_caller = inspect.stack()[1].function

        if m_caller == 'manage':
            self.detailed_headers = [
                'Method', 
                'Endpoint', 
                'OperationId',
                'Parameters', 
                'Fuzz_rounds', 
                'Status_codes', 
                'NS_status'
            ]
            self.default_headers =  [
                'Method', 
                'Endpoint', 
                'Fuzz_rounds', 
                'Status_codes', 
            ]

        elif m_caller == 'handle_endpoint_results':
            
            self.detailed_headers = [
                'Round', 
                'Method', 
                'Status', 
                'Response-Length', 
                'Response-Time'
            ]
            self.default_headers =  [
                'Round', 
                'Method', 
                'Status', 
                'Response-Length', 
                'Response-Time'
            ]

        return True

    def get_path_parameters(self, path: str) -> list:
        # Verifica se o caminho está presente no esquema
        if path in self.spec_parameters:
            # Inicializa uma lista para armazenar os nomes dos parâmetros
            parameters = []
            # Itera sobre os métodos (get, post, etc.) no caminho fornecido
            for method, params in self.spec_parameters[path].items():
                # Itera sobre os parâmetros e adiciona os nomes à lista
                for param in params:
                    parameters.append(param['name'])
            return parameters
        else:
            # Retorna uma lista vazia se o caminho não estiver presente no esquema
            return []

    def build_fuzz_items(self, fuzz_results:dict):
        m_caller = inspect.stack()[1].function
        path_control = []

        l=[]
        if m_caller == 'manage':

            for endpoint, tests in fuzz_results.items():
                sample_test = tests[0]
                method = sample_test['method'].upper()
                spec_endpoint = endpoint
                fuzz_rounds = len(tests)
                status_codes = ','.join(set(str(test['response'].status) for test in tests))

                # --set-parameter <param>
                if self.set_param_scope:
                    spec_endpoint = sample_test.get('spec_path', False)
                    if spec_endpoint in path_control:
                        continue

                    fuzz_rounds = sample_test.get('fuzz_rounds',False)
                    status_codes = ','.join(
                        set(
                            str(t[0]['response'].status) 
                            for p, t in fuzz_results.items() 
                            if t[0].get('spec_path') == spec_endpoint
                        )
                    )
                    path_control.append(spec_endpoint)

                if self.detailed_enabled:
                    parameters = self.get_path_parameters(endpoint)
                    opid = self.jc_list.list_opids(endpoint)
                    ns_codes = ','.join(set(str(t['response_status_audit']['fuzz_response_status']) for t in tests if t['response_status_audit']['fuzz_response_status']))

                    l.append(
                        {
                        'Method': method,
                        'Endpoint': spec_endpoint,
                        'OperationId': ','.join(opid),
                        'Parameters': ','.join(parameters),    
                        'Fuzz_rounds': fuzz_rounds,
                        'Status_codes': status_codes,
                        'NS_status': ns_codes
                        }
                    )
                else:
                    l.append(
                        {
                        'Method': method,
                        'Endpoint': spec_endpoint,    
                        'Fuzz_rounds': fuzz_rounds,
                        'Status_codes': status_codes
                        }
                    )
        elif m_caller == 'handle_endpoint_results':
            for _, test in enumerate(fuzz_results,1):
            #{self.get_reason(t['response'])}

                method = test['method'].upper()
                endpoint = test['path']
                status_reason = f"{str(test['response'].status)} ({self.get_reason(test['response'])})"

                if self.detailed_enabled:
                    #parameters = self.get_path_parameters(endpoint)
                    #opid = self.jc_list.list_opids(endpoint)

                    l.append(
                        {
                        'Round': _,
                        'Method': method,
                        'Status': f"{str(test['response'].status)}",
                        'Response-Length': test['response'].content_length,
                        'Response-Time': test['response_time']
                        }
                    )
                else:
                    l.append(
                        {
                        'Round': _,
                        'Method': method,
                        'Status': status_reason,
                        'Response-Length': test['response'].content_length,
                        'Response-Time': test['response_time']
                        }
                    )
            
        
        return l
    
    def truncate_string(self, s, max_length):
        if len(s) > max_length:
            return s[:max_length - 3] + '...'
        return s

    def fuzz_test_preview(self, option_index):
        test_data = self.endpoint_results[int(option_index.split()[0].strip()) - 1]
        method = test_data['method'].upper()
        path = test_data['path']
        session_version = test_data['session'].version
        headers = test_data['headers']
        body = test_data.get('body')
        response = test_data['response']
        response_text = asyncio.run(self.jc_show.get_response_text(response))
        request_info = self.jc_show.show_request_info(method, path, session_version, headers, body)
        response_info = self.jc_show.show_response_info(response, response_text)
        terminal_width = shutil.get_terminal_size().columns
        column_width = terminal_width // 2
        max_line_length = column_width - 5  

        request_lines = request_info.split('\n')
        response_lines = response_info.split('\n')
        
        preview_lines = []
        for req_line, res_line in zip(request_lines, response_lines):
            truncated_req_line = self.truncate_string(req_line, max_line_length)
            truncated_res_line = self.truncate_string(res_line, max_line_length)
            preview_lines.append(f"{truncated_req_line:<{column_width}} | {truncated_res_line:<{column_width}}")
        
        if len(request_lines) > len(response_lines):
            for req_line in request_lines[len(response_lines):]:
                truncated_req_line = self.truncate_string(req_line, max_line_length)
                preview_lines.append(f"{truncated_req_line:<{column_width}} | {'':<{column_width}}")
        elif len(response_lines) > len(request_lines):
            for res_line in response_lines[len(request_lines):]:
                truncated_res_line = self.truncate_string(res_line, max_line_length)
                preview_lines.append(f"{'':<{column_width}} | {truncated_res_line:<{column_width}}")
        
        preview_text = "\n".join(preview_lines)

        lexer = lexers.get_lexer_by_name(
            self.lexer_style, 
            stripnl=False, 
            stripall=False
        )
        formatter = formatters.TerminalFormatter(bg="dark")
        return '\n' + highlight(preview_text, lexer, formatter) 

    def handle_endpoint_results(self, endpoint_results):
        self.endpoint_results = endpoint_results
        self.lexer_style = 'Asc'
        hcolor = 'green'
        random_banner = 'default_naviban'
        msg = '⚙ sessions'
        show_banner = False
        keep_banner = 'default_naviban'
        preview_command = None
        self.preview_title = " ~ Request and Response Preview ~"
        #self.detailed_enabled = False
            
        l=[]

        if not self.load_menu_settings():
            return False
        
        current_headers = self.default_headers

        while True:
            endpoint_items = self.build_fuzz_items(endpoint_results) 
            _options_, header = build_options(
                endpoint_items, 
                current_headers, 
                False
            )
            total_sessions = len(l)
            header_size = len(header)
            print('\033[2J\033[1;1H')
            
            fuzzmenu = TerminalMenu(
                menu_entries =_options_,
                preview_command = preview_command,
                menu_cursor = self.prompt,
                show_search_hint=True,
                show_search_hint_text=" ",
                accept_keys = self.accepted_keys,
                preview_title=self.preview_title,
                preview_size=self.get_terminal_height() - 1
            )
            spec_info = VFDBOps().get_by_id(
                '_SPECS_', 'spec_id', self.vmnf_handler['spec_id']
            )
            
            jcbanner_fmt(spec_info.__dict__)

            kbann = normalize(
                header, hcolor, 'msg', show_banner, 
                random_banner, keep_banner, header_size, False
            )
            keep_banner = kbann
            fuzz_index = fuzzmenu.show()

            if fuzz_index is None:
                print('\033[2J\033[1;1H')
                break

            chosen_key = fuzzmenu._chosen_accept_key

            if chosen_key == 'p':
                if preview_command is None:
                    preview_command = self.fuzz_test_preview
                else:
                    preview_command = None
                continue

            elif chosen_key == 'ctrl-y':
                self.lexer_style = choice(srandlexers)
                continue

    def manage(self, fuzz_results:dict):
        self.fuzz_results = fuzz_results
        self.lexer_style = 'Asc'
        hcolor = 'green'
        random_banner = 'default_naviban'
        msg = '⚙ sessions'
        show_banner = False
        keep_banner = 'default_naviban'
        preview_command = None
        self.detailed_enabled = False
            
        l=[]

        if not self.load_menu_settings():
            return False
        
        current_headers = self.default_headers

        while True:
            #print(current_headers)
            fuzz_items = self.build_fuzz_items(fuzz_results)

            _options_, header = build_options(
                fuzz_items, 
                current_headers, 
                False
            )
            total_sessions = len(l)
            header_size = len(header)
            print('\033[2J\033[1;1H')
            
            fuzzmenu = TerminalMenu(
                _options_,
                preview_command=preview_command,
                menu_cursor=self.prompt,
                accept_keys=self.accepted_keys,
                preview_title=""
                #preview_size=10#self.get_terminal_height() - 15
            )

            spec_info = VFDBOps().get_by_id(
                '_SPECS_', 'spec_id', self.vmnf_handler['spec_id']
            )
            jcbanner_fmt(spec_info.__dict__)

            kbann = normalize(
                header, hcolor, 'msg', show_banner, 
                random_banner, keep_banner, header_size, False
            )
            keep_banner = kbann
            fuzz_index = fuzzmenu.show()

            if fuzz_index is None:
                print('\033[2J\033[1;1H')
                break

            chosen_key = fuzzmenu._chosen_accept_key

            if chosen_key == 'p':
                if preview_command is None:
                    preview_command = self.enable_preview
                else:
                    preview_command = None
                continue
            
            elif chosen_key == 'ctrl-y':
                self.lexer_style = choice(srandlexers)
                continue
            
            elif chosen_key == 'i':
                self.detailed_enabled = True
                current_headers = self.detailed_headers

                #current_filters = self.detailed_filters
                #default_psize = 0.85
                #let's implement the detailed view
                
                # Example usage:
                #popup = PopupDisplay("comando i escolhido")
                #popup.display_detailed_view()
                continue

            elif chosen_key == 'd':
                self.detailed_enabled = False
                current_headers = self.default_headers
                continue

            if chosen_key == "enter":
                try:
                    previous_headers = current_headers.copy()
                    previous_detailed_enabled = self.detailed_enabled
                    test_case = _options_[fuzz_index]
                    selected_test = test_case.split()[1]

                    if self.set_param_scope:
                        selected_fuzz_endpoint = [t[0] for p, t in fuzz_results.items() if t[0].get('spec_path') == selected_test]
                    else:
                        selected_fuzz_endpoint = fuzz_results[selected_test]

                    self.handle_endpoint_results(selected_fuzz_endpoint)
                    self.load_menu_settings()  
                    self.detailed_enabled = previous_detailed_enabled
                    current_headers = self.default_headers if not self.detailed_enabled else self.detailed_headers
                    continue
                except KeyError:
                    continue
 