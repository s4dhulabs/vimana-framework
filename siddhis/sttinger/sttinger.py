from ..djunch.engines._dju_settings import table_models
from ..djunch.engines._dju_utils import DJUtils

from core.vmnf_shared_args import VimanaSharedArgs
from urllib.parse import urlparse, urljoin
from neotermcolor import colored, cprint
from siddhis.tictrac import tictrac
from siddhis.prana import prana
from collections import Counter
from packaging import version
from hashlib import sha224
from time import sleep
import collections
import requests
import pathlib
import yaml
import json
import sys
import os

from .tools.sttg_tools import get_release



class siddhi:
    def __init__(self,**vmnf_handler):
        
        self.vmnf_handler = vmnf_handler
        self.siddhi = colored('⥂ sttinger ⥂', 'magenta')
        self.target_url = vmnf_handler.get('target_url',False)
        self.quiet_mode = vmnf_handler.get('quiet_mode',False)
        self.siddhi_call = vmnf_handler.get('siddhi_call',False)
        self.exit_on_success = vmnf_handler.get('exit_on_success',True)
        self.issues_lookup = True if vmnf_handler.get('search_issues') \
                or vmnf_handler.get('issues_table') else False

        self.match = False
        self.load_config()
        
        if not self.target_url.startswith('http'):
            self.target_url = f'http://{self.target_url}' 

    def load_config(self):
        yaml_file = str(os.path.dirname(__file__)) + '/config.yaml'
        with open(yaml_file) as file:
            sts = yaml.load(file, Loader=yaml.FullLoader)

        settings = sts.get('sttg_conf')
        self.sttg_patterns = settings.get('sttg_patterns') 
        self.headers = settings.get('headers')
                
    def load_patterns(self,p_type):
        if p_type not in ['base', 'actions']:
            print('invalid type')
            return False
        
        p_dir = os.path.dirname(__file__) +\
                f'/sttg_p/{p_type}_patterns.json'

        with open(p_dir) as f:
            return (json.load(f))

    def get_sttg_obj(self):
        return {
            'base': self.load_patterns('base'),
            'actions':  self.load_patterns('actions')
        }
    
    def get_hash(self,data):
        return (sha224(data.encode()).hexdigest())

    def check_match(self,f_hash, **sttg_p):
        if sttg_p.get(f_hash) is None:
            return False

        generic = False
        self.versions_list = sttg_p.get(f_hash)
        flag_v, opt_v = self.versions_list[0].split(':')
        self.search_version=flag_v[:-2]

        if flag_v == opt_v:
            fmk_v = flag_v
            generic = f"{fmk_v}:{fmk_v}"
        else:
            fmk_v = f'{flag_v} or {opt_v}'

        hm_vers = sttg_p.get(f_hash)[1:].copy()

        if generic: 
            hm_vers = [x for x in hm_vers if x != generic] 

        for n,i in enumerate(hm_vers[0:]):
            hm_vers[n] = version.parse(i)

        minv = min(hm_vers)
        maxv = max(hm_vers)

        self.match ={
            'range_v':hm_vers,
            'versions':fmk_v,
            'max': minv, 
            'min': maxv,
            'version_list': self.versions_list[1:]
        }

        if not self.match:
            if not self.quiet_mode:
                print(f'→ It was not possible to identify the framework version')
                return False

        if not self.quiet_mode:
            fmk_v_hl = colored(fmk_v, 'red',attrs=['bold'])
            tags = len(self.versions_list[1:])
            f_release_date = ''
            
            release_info = get_release(self.search_version)
            
            if release_info:
                release_date = release_info.get('upload_time')
                f_release_date = f"RLS: {release_date}"
                python_version = release_info.get('requires_python')

            print(f"      {colored('◉','green',attrs=['bold'])}  Running Django {fmk_v_hl} ({str(minv).split(':')[-1]}-{maxv}) / {f_release_date}")
            sleep(1)

            if python_version:
                print(f"             ├─ Requires Python {colored(python_version,'green')} ")
            if release_date:
                print(f"             ├─ {colored(tags,'green')} related tag versions")

        self.issues_lookup and self.search_issues()
    
    def search_issues(self):
        from siddhis.prana.prana import siddhi as prana
        from siddhis.tictrac.tictrac import siddhi as tictrac
        
        self.vmnf_handler['django_version'] = self.search_version

        tickets,tickets_table = tictrac(**self.vmnf_handler).get_ticket_ids()
        cves,cves_table = prana(**self.vmnf_handler).get_cves_for_version()
        
        if cves:
            print(f"             ├─ {colored(len(cves),'green')} CVEs")
        if tickets:
            print(f"             └─ {colored(len(tickets),'green')} Security Tickets")
        sleep(1)
        
        input() if self.vmnf_handler.get('pause_steps') else None

        self.match.update(
            {
                'tickets_tbl': tickets_table,
                'cves_tbl': cves_table,
                'tickets': tickets,
                'cves':cves
            }
        )

        if self.vmnf_handler['output_table']:
            cprint(f'» CVEs for Django {self.search_version}:', 'cyan')
            sleep(0.30)

            print(cves_table)
            input() if self.vmnf_handler.get('pause_steps') else None

            cprint(f'\n» Security Tickets for Django {self.search_version}:', 'cyan')
            sleep(0.30)

            print(tickets_table)
            input() if self.vmnf_handler.get('pause_steps') else None

        elif self.vmnf_handler['output_text']:
            DJUtils().show_cve_txt_details(cves)
        
        return True

    def get_response(self, target_url):
        try:
            return (requests.get(target_url,headers=self.headers,verify=False))
        except requests.exceptions.ConnectionError:
            return False

    def check_patterns(self):
        sttg_obj = self.get_sttg_obj()
        t=colored('⥂','green',attrs=['bold'])
        hl_target = colored(self.target_url, 'green')
        cprint(f"\n⥂  Starting passive fingerprint against {self.target_url}...",'cyan')
        for sttg_t, sttg_p in sttg_obj.items():
            if not self.quiet_mode:
                print(f"{colored('⥂','green',attrs=['bold'])}  Checking {colored('patterns:' + sttg_t, 'green')}...")
                sleep(1) 
            for f_pattern in self.sttg_patterns.get(sttg_t):
                resp = self.get_response(urljoin(self.target_url, f_pattern))                
                if not resp:
                    continue 

                if resp.status_code == 200:
                    self.check_match(self.get_hash(resp.text),**sttg_p)
                    return True
                return False

    def start(self):

        if not self.target_url:
            cprint(f'\t → Scope Error: Missing target URL. Use vf guide -m sttinger --args\n', 'red')
            return False

        self.check_patterns()

        if not self.match:
            cprint(f'\t → It was not possible to identify the framework version', 'red')

            if not self.issues_lookup:
                print('-'*70)
            return False

        if not self.issues_lookup:
            print('-'*70)

        return self.match


