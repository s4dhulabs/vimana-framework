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


from res.vmnf_banners import mdtt1,case_header,vmn05,create_status
from .vmnf_navi_cases import naviCases
from ._dbops_.vmnf_dbops import VFDBOps
from ._dbops_.db_utils import get_elapsed_time
from res.vmnf_validators import check_file
from neotermcolor import colored,cprint
from .load_settings import _cs_
from tabulate import tabulate
from datetime import datetime
import sys,os,yaml,glob
from time import sleep
import subprocess 
import jsonpickle
import itertools
import hashlib
import re


class CasManager:
    def __init__(self, handler):
        self.handler = handler
        self.model = '_CASES_'
        self.obj_id_col = 'case_id'
       
    def handle_case_id(self, case_id):
        if not re.match(r"^[a-fA-F0-9]{10}$", case_id):
            self.obj_id_col = 'case_name'

    def get_cases(self):
        self._cases_ = VFDBOps().getall(self.model)

    def handler_no_case(self):
        print("\033c", end="")
        mdtt1('white','bold')
        cprint(_cs_.get('empty_msg').format(
            '!'#datetime.now()
            ), 'cyan'
        )
        print()

        if self.handler.navigation_mode:
            return True
        sys.exit(1)

    def case_table_exists(self):
        if VFDBOps().table_exists(self.model) and VFDBOps().getall(self.model):
            return True
        return False

    def case_exists(self, case_id):
        return case_id in itertools.chain.from_iterable(
                [(c.case_id, c.case_name) 
                    for c in self._cases_]
        )
    
    def flush_case(self, case_id):
        self.get_cases()
        self.handle_case_id(case_id)
        
        if not self.case_exists(case_id):
            _cs_['empty_msg'] = f'\t\tInvalid case: {case_id}'
            self.handler_no_case()

        VFDBOps().flush_resource(self.model,self.obj_id_col, case_id)
        _cs_['empty_msg'] = f'\t\t{colored(case_id, "red")} case flushed!'
        self.handler_no_case()
        
    def flush_cases(self):
        self.get_cases()

        if not self._cases_:
            self.handler_no_case()
        
        total_cases = len(self._cases_)
        vmn05()
        print()

        for c in self._cases_:
            fmsg = colored(f'          \t- flushing {c.case_id} → {c.case_name} ','red')
            print(fmsg.ljust(os.get_terminal_size().columns - 1), end="\r")
            sleep(0.10)
            VFDBOps().flush_resource(self.model,self.obj_id_col, c.case_id)
            
        smsg = colored(f'          \t* {total_cases} cases flushed','green')
        print(smsg.ljust(os.get_terminal_size().columns - 1), end="\r")
        print('\n\n\n')
        sleep(1)
        return 

    def list_cases(self):
        if self.handler.navigation_mode:
            naviCases(vars(self.handler)).manage()

        if not self.case_table_exists():
            self.handler_no_case()

        self.get_cases()

        if not self._cases_:
            self.handler_no_case()

        attrs=[]
        color = 'green'
        cases_tbl = []
        cases_tbl.append(
            [
                colored('id', 'cyan', attrs=[]),
                colored('plugin','cyan', attrs=[]),
                colored('target','cyan', attrs=[]),
                colored('name','cyan', attrs=[]),
                colored('type','cyan', attrs=[]),
                colored('astt','cyan', attrs=[]),
                colored('date','cyan', attrs=[]),
            ]
        )

        for c in self._cases_:
            if os.path.isabs(c.case_target):
                c.case_target = c.case_target.split('/')[-1]

            c.case_date = get_elapsed_time(c.case_date)
            cases_tbl.append(
                [
                    c.case_id, 
                    c.case_plugin, 
                    c.case_target,
                    c.case_name, 
                    c.case_plugin_type,
                    c.case_plugin_astt,
                    c.case_date
                ]
            )

        print("\033c", end="")
        case_header()
        cprint("\n→ Available cases:",'cyan')

        print(tabulate(
            cases_tbl,
            headers='firstrow',
            numalign="left",
            tablefmt='pretty',missingval='?'
            )
        )

    def load_case(self, case_id):
        self.handle_case_id(case_id)
        _case_ = VFDBOps().get_by_id(
            self.model,
            self.obj_id_col,
            case_id
        )
        
        if _case_ is None:
            _cs_['empty_msg'] = f'\t Invalid case: {case_id}'
            self.handler_no_case()

        case_ns = jsonpickle.decode(_case_.case_ns)
        case_args = case_ns.args
        sc_index = case_args.index('--save-case')
        del case_args[sc_index + 1] 
        del case_args[sc_index] 
        subprocess.run(case_args)

    def save_case(self):
        case_date = datetime.now()
        dt_str = case_date.strftime('%Y-%m-%d %H:%M:%S')
        args_str = ' '.join(self.handler.args)
        case_sign = f"{dt_str}: {args_str}"  
        case_target = False

        case_hash = hashlib.sha256(case_sign.encode('utf-8')).hexdigest()
        case_id = case_hash[:10]
        case_name = self.handler.save_case.split('.')[0]
        case_ns = jsonpickle.encode(self.handler)
        case_plugin = self.handler.module_run

        siddhi = VFDBOps().get_by_id(
            '_SIDDHIS_', 'name', case_plugin
        )
        

        if self.handler.target_url:
            case_target = self.handler.target_url

        elif self.handler.single_target:
            case_target = self.handler.single_target

        elif self.handler.project_dir:
            case_target = self.handler.project_dir

        elif self.handler.request_data_set:
            request_file = self.handler.request_data_set

            if os.path.isabs(request_file):
                case_target = request_file
            else:
                case_target = os.path.join(os.getcwd(), request_file)

        case = {
            'case_id': case_id,
            'case_hash': case_hash,
            'case_name': case_name,
            'case_target': case_target,
            'case_date': case_date,
            'case_plugin': case_plugin,
            'case_plugin_info': siddhi.info,
            'case_plugin_type': siddhi.type,
            'case_plugin_astt': siddhi.astt,
            'case_ns': case_ns
        }
        
        VFDBOps(**case).register(self.model)
        sys.exit(1)


