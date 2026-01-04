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

from core._dbops_.models.sessions import VFSessions
from core.vmnf_sessions_utils import abduct_items
from core._dbops_.vmnf_dbops import VFDBOps
#from core.vmnf_navi_sessions import naviSessions

from scrapy.utils.serialize import ScrapyJSONEncoder
from neotermcolor import cprint, colored as cl
from res.vmnf_banners import *
from core.load_settings import _vfs_
from urllib.parse import urlparse
from datetime import datetime
from random import choice
from time import sleep
import jsonpickle
import hashlib
import inspect
import json
import yaml
import glob
import sys
import io
import os




class VFSession:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler

        self.encoder = ScrapyJSONEncoder()
        self.sessions_tbl = []
        self.flush_mode = False
        self.model = '_SESSIONS_'
        self.obj_id_col = 'session_id'

    def hashsession(self):
        self.record_time = datetime.now()
        _session_hash_ = hashlib.sha224()
        _session_hash_.update(yaml.dump(self.vmnf_handler, default_flow_style=False).encode())
        return _session_hash_.hexdigest()

    def save_session(self):
        # {vmnf_log:flag}
        
        session_hash  = self.hashsession()
        session_id = session_hash[:10]
        session_file = f'{session_id}.yaml' 
        sessions_dir = f'vimana/sessions'
        abs_sessions_path = os.path.join(os.path.expanduser("~"), sessions_dir)
        full_session_path  = f"{abs_sessions_path}/{session_file}"

        if not os.path.exists(abs_sessions_path):
            os.makedirs(abs_sessions_path)

        if not os.path.exists(full_session_path):
            with open(full_session_path, 'w') as _file_:
                yaml.dump(
                    self.vmnf_handler, _file_, 
                    default_flow_style=False
                )

        _target_ = urlparse(self.vmnf_handler['target_url']).netloc
        _issues_ = self.vmnf_handler.get('issues_overview')
        
        session = {}
        session = {
            '_session_':{
                'session_id': session_id,
                'session_hash': session_hash,
                'session_file': session_file,
                'session_path': full_session_path,
                'session_date': self.record_time,
                'session_plugin': self.vmnf_handler['module_run'],
                'session_target': _target_.split(':')[0],
                'target_port': _target_.split(':')[1],
                'target_url': self.vmnf_handler['target_url'],
                'framework': self.vmnf_handler['framework'],
                'framework_version': self.vmnf_handler['framework_version'],
                'total_exceptions': _issues_['exceptions'],
                'total_cves': _issues_['cve_ids'],
                'total_tickets': _issues_['security_tickets'],
                }
        }
        

        VFDBOps(**session).register('_SESSIONS_')
        
        plugin  = cl(self.vmnf_handler['module_run'], 'red')
        target  = cl(self.vmnf_handler['target_url'], 'red')
        session = cl(session_id, 'red')

        if self.vmnf_handler['sample']:
            print("\033c", end="")
            sample_mode(
                cl('  sample mode   ','red', 'on_white', attrs=['bold'])
            )
        else:
            vmn05()

        print(f"\n\t→ {plugin} session {session} sucessfully recorded for target {target}!")
        sleep(2)
        
        if self.vmnf_handler['sample']:
            print("\033c", end="")
            sample_mode(
                cl('  sample mode   ','red', 'on_white', attrs=['bold'])
            )
        else:
            vmn05()
            sleep(0.30)
        
        return session_id

    def flush_session_file(self, session_path):
        # {vmnf_log:flag}

        try:
            os.remove(session_path)
        except FileNotFoundError as fnf:
            return False

        return True

    def check_sessions(self):
        recorded_sessions = VFDBOps(**self.vmnf_handler).list_resource(self.model,[])
        
        if not recorded_sessions or len(recorded_sessions) == 0:
            if self.vmnf_handler['runner_mode']:
                return []

            self.handle_no_sessions()
            return False

        return recorded_sessions

    def flush_all_sessions(self):
        self.flush_mode = True
        recorded_sessions = self.check_sessions()
        total = len(recorded_sessions)
        hl_total = cl(total, 'red', attrs=['blink'])

        for sc, _s_ in enumerate(recorded_sessions,1):
            session = cl(_s_.session_id, 'red')
            plugin  = cl(_s_.session_plugin, 'blue')
            target  = cl(_s_.target_url, 'blue')

            vmn05()
            print(f"\n\t Flushing session {session} ({sc}/{total}) / {plugin} → {target} ...\n")
            
            if not self.vmnf_handler['fastflush']:
                sleep(1)

            if self.vmnf_handler['xray_enabled']:
                try:
                    abduct_items(
                        **self.load_session(
                            _s_.session_id, 
                            self.flush_mode
                        )
                    )
                except:
                    pass
            
            session_dict = _s_.__dict__
            session = VFDBOps(**session_dict).flush_resource(
                self.model, self.obj_id_col, _s_.session_id
            )

            self.flush_session_file(_s_.session_path)
            
            if not self.vmnf_handler['fastflush']:
                sleep(1)
        
        cprint(f"\n\t   → {hl_total} sessions flushed!\n\n\n", 'blue')

    def flush_session(self):

        self.flush_mode = True
        sid = self.vmnf_handler['flush_session']
        _s_ = VFDBOps(**self.session).get_session(sid)
        
        if not _s_:
            self.handle_invalid_session(sid)
            return False
        
        session = cl(_s_.session_id, 'red')
        plugin  = cl(_s_.session_plugin, 'blue')
        target  = cl(_s_.target_url, 'blue')

        vmn05()
        print(f"\n\t Flushing session {session} / {plugin} → {target}...\n")
        sleep(2)

        if self.vmnf_handler['xray_enabled']:
                abduct_items(**self.load_session(_s_.session_id, self.flush_mode))
                sleep(1)
        
        if not VFDBOps(**self.session).flush_resource(
                self.model, self.obj_id_col, _s_.session_id):
            self.handle_invalid_session(_s_.session_id)
            return False
        
        print()
        os.remove(_s_.session_path)
        
    def format_date(self):
        return self._s_session_date.strftime("%Y-%m-%d %H:%M:%S")

    def get_total_sessions(self):
        return len(self.check_sessions())

    def list_sessions(self, headless=False):
        from core.vmnf_navi_sessions import naviSessions

        if self.vmnf_handler['navigation_mode']:
            naviSessions(self.vmnf_handler).manage()
            return True

        _sessions_ = self.check_sessions()
        
        attrs = []
        clc  = 'white'
        
        if not headless:
            print("\033c", end="")
            case_header()

        self.sessions_tbl.append(
            [
                cl('Session', 'cyan', attrs=[]),
                cl('Date','cyan', attrs=[]),
                cl('Plugin','cyan', attrs=[]),
                cl('Target','cyan', attrs=[]),
                cl('Port','cyan', attrs=[]),
                cl('Framework','cyan', attrs=[]),
                cl('Version','cyan', attrs=[]),
                cl('Exceptions','cyan', attrs=[]),
                cl('CVEs','cyan', attrs=[]),
                cl('Tickets','cyan', attrs=[])
            ]
        )

        for _vs_ in _sessions_:
            clc = 'white'
            _vs_.session_date = _vs_.session_date.strftime("%Y-%m-%d %H:%M:%S")
            self.sessions_tbl.append([
                cl(_vs_.session_id, 'green', attrs=attrs),
                cl(_vs_.session_date, clc, attrs=attrs),
                cl(_vs_.session_plugin, 'blue', attrs=attrs),
                cl(_vs_.session_target, clc, attrs=attrs),
                cl(_vs_.target_port, clc, attrs=attrs),
                cl(_vs_.framework, 'yellow', attrs=['dark']),
                cl(_vs_.framework_version, clc, attrs=attrs),
                cl(_vs_.total_exceptions, clc, attrs=attrs),
                cl(_vs_.total_cves, clc, attrs=attrs),
                cl(_vs_.total_tickets, clc, attrs=attrs)
                ]
            )

        print(tabulate(
            self.sessions_tbl,
            headers='firstrow',
            numalign="left",
            tablefmt='pretty',missingval='?'
            )
        )
        print('\n\n') 
    
    def handle_no_sessions(self):
        # {vmnf_log:flag}
        
        case_header()
        cprint(f"\t\t No sessions found!\n\n\n", 'red')
        sys.exit(1)

    def handle_invalid_session(self, value):
        # {vmnf_log:flag}

        print("\033c", end="")
        print(f"\n\n\t\t Session {cl(value, 'red', attrs=['bold'])} was not found")
        mdtt1()
        self.list_sessions(True)

    def load_session(self, session_id, flush_mode=False):

        """ We're going to use `unsafe_load()` here because sessions 
        are basicaly Python objects, names, and expressions, altough 
        all of them are created and controled internally by Vimana, 
        so it offers no risk at all, once it's not based
        on untrusted user inputs and so on...
                                                                    ´
                    *                                                
                                                        .;.,~
                            |                        .       
                          - ø -                        
                            |               *   __´ `__
                                                  '''
                                                   
              *      ç(-|-)ç       
                      _| |_                     
                     /__/  \                 - ø -
                   _(<_   / )_                 ' 
                  (__\_\_|_/__)     .   
                                            . '

        -'-                         
         '
                                    
        In the future we'll play with custom constructors
            to fix it in a elegant way though """
        
        if not isinstance(session_id, VFSessions):
            _session_ = VFDBOps(**self.vmnf_handler).get_by_id(
                self.model,self.obj_id_col,session_id
            )

            if not _session_ or _session_ is None:
                self.handle_invalid_session(session_id)
                return False
        else:
            _session_ = session_id

        session_path = _session_.session_path

        if not os.path.exists(session_path):
            self.handle_invalid_session(session_path)
            return False

        with open(_session_.session_path, 'r') as _sf_:
            '''@except yaml.constructor.ConstructorError'''

            _session_ = yaml.unsafe_load(_sf_)
            _prompt_ = _session_['prompt']

            frame = inspect.currentframe()
            frame = frame.f_back
            code = frame.f_code
            method = code.co_name
            engine = frame.f_locals.get('self', None).__class__.__name__
            _session_['origin'] = f"{engine}.{method}"
            
        return (_session_ if flush_mode else _prompt_(**_session_))

