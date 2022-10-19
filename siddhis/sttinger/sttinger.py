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
import collections
import requests
import pathlib
import yaml
import json
import sys
import os





class siddhi:
    def __init__(self,**vmnf_handler):
        
        self.vmnf_handler = vmnf_handler
        self.siddhi = colored('sttinger', 'magenta')
        self.target_url = vmnf_handler.get('target_url',False)
        self.quiet_mode = vmnf_handler.get('quiet_mode',False)
        self.siddhi_call = vmnf_handler.get('siddhi_call',False)
        self.exit_on_success = vmnf_handler.get('exit_on_success',True)
        self.issues_lookup = True if vmnf_handler.get('search_issues') \
                or vmnf_handler.get('issues_table') else False

        self.match = False
        self.load_config()

        self.fingerprint_tbl = DJUtils().get_pretty_table(
	    **table_models().sttinger_findings_set
        )
        
        if not self.target_url.startswith('http'):
            self.target_url = f'http://{self.target_url}' 

    def load_config(self):
        yaml_file = str(os.path.dirname(__file__)) + '/config.yaml'
        with open(yaml_file) as file:
            sts = yaml.load(
                    file, Loader=yaml.FullLoader)

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

        self.versions_list = sttg_p.get(f_hash)
        flag_v, opt_v = self.versions_list[0].split(':')

        if flag_v == opt_v:
            fmk_v = flag_v
        else:
            fmk_v = f'{flag_v} or {opt_v}'
            
        hm_vers = sttg_p.get(f_hash)[1:].copy()
         
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
                print(f'[{self.siddhi}]→ It was not possible to identify the framework version')

                return False

        if not self.quiet_mode:
            fmk_v_hl = colored(fmk_v, 'red',attrs=['bold'])
            minv_hl = colored(str(minv).split(':')[-1], 'cyan')
            maxv_hl = colored(maxv, 'cyan')
            tags = colored(len(self.versions_list[1:]), 'green')

            print(f"[{self.siddhi}]→ Running Django {fmk_v_hl} / ({minv_hl} - {maxv_hl})")
            
            self.fingerprint_tbl.add_row(
                [
                    self.target_url,
                    fmk_v_hl,
                    f"{minv_hl} - {maxv_hl}",
                    0,
                    0,
                ]
            )

        if self.issues_lookup:
            self.search_version=flag_v[:-2]
            self.search_issues()
            
    def search_issues(self):
        from siddhis.djunch.engines._dju_utils import DJUtils
        
        sample={
            'INSTALLED_ITEMS': False,
            'EXCEPTION_SUMMARY': {
	        'Django Version': self.search_version
            }
        }
        
        issues = DJUtils().get_version_issues(**sample)
        
        if not issues or issues is None:
            if not self.quiet_mode:
                print(f'\n[{self.siddhi}]→ No issues identified for Django {self.search_version} version.')
            return False
        
        self.match.update(**issues)

        hl_cves = colored(len(issues.get('cves')), 'green')
        hl_tcts = colored(len(issues.get('tickets')), 'green')
        hl_tags = colored(len(self.versions_list[1:]), 'green')
        
        print(f'\t     + {hl_tags} Related tags')

        if not self.vmnf_handler.get('issues_table'):
            print(f'\t     + {hl_cves} CVEs')
            print(f'\t     + {hl_tcts} Security Tickets')
        else:
            print(f' → {hl_cves} CVEs')
            print(issues.get('cves_tbl'))
            
            print(f' → {hl_tcts} Security Tickets')
            print(issues.get('tickets_tbl'))

    def get_response(self, target_url):
        try:
            return (requests.get(target_url,headers=self.headers,verify=False))
        except requests.exceptions.ConnectionError:
            return False

    def check_patterns(self):
        sttg_obj = self.get_sttg_obj()

        print()
        for sttg_t, sttg_p in sttg_obj.items():

            if not self.quiet_mode:
                print(f'[{self.siddhi}]! Checking {colored(self.target_url, "cyan")}...')
            
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

        #print(self.fingerprint_tbl)
        if not self.issues_lookup:
            print('-'*70)

        return self.match


