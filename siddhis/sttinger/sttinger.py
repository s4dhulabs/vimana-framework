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
    module_information = collections.OrderedDict()
    module_information = {
        "Name":         "sttinger",
        "Info":         "Framework version fingerprint tool",
        "Category":     "Framework",
        "Framework":    "Django",
        "Type":         "Tracker",
        "Module":       "siddhis/sttinger",
        "Author":       "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":        "Identify framework version in passive way",
        "Description":
        """

        \r  This tool was designed to identify Python framework version in a passive way,
        \r  acquiring and analyzing standard files from frameworks installations.
        \r  This first version only supports Django, but soon it'll support another ones.
        \r
        \r  It can be invoked directly from the command line through the `run` command 
        \r  and also incorporated by other tools such as DMT, which invokes it in the 
        \r  initial stages of the analysis.
        
        """
    }

    # help to 'args' command in main vimana board: vimana args --module dmt
    module_arguments = VimanaSharedArgs().shared_help.__doc__

    def __init__(self,**vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.siddhi = colored('sttg', 'magenta')
        self.target_url = vmnf_handler.get('target_url',False)
        self.quiet_mode = vmnf_handler.get('quiet_mode',False)
        self.siddhi_call = vmnf_handler.get('siddhi_call',False)
        self.search_issues = vmnf_handler.get('search_issues',True)
        self.exit_on_success = vmnf_handler.get('exit_on_success',True)
        self.load_config()
        
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
                '/sttg_p/{}_patterns.json'.format(p_type)

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
        #f_hash=f_hash + 'caos'

        if sttg_p.get(f_hash) is None:
            return False

        self.versions_list = sttg_p.get(f_hash)
        flag_v, opt_v = self.versions_list[0].split(':')
        #flag_v, opt_v = sttg_p.get(f_hash)[0].split(':')

        if flag_v == opt_v:
            fmk_v = flag_v
        else:
            fmk_v = '{} or {}'.format(flag_v,opt_v)
            
        fmk_v_hl = colored(fmk_v, 'red',attrs=['bold'])
        hm_vers = sttg_p.get(f_hash)[1:].copy()
         
        for n, i in enumerate(hm_vers[0:]):
            hm_vers[n] = version.parse(i)

        match ={
            'range_v':hm_vers,
            'versions':fmk_v,
            'max': max(hm_vers), 
            'min': min(hm_vers),
            'version_list': self.versions_list[1:]
        }
        
        if self.search_issues:
            self.search_version=flag_v[:-2]
            match['flag_version'] = self.search_version
            match['tcts'] = tictrac.siddhi(self.search_version).start()
            match['cves'] = prana.siddhi(self.search_version).get_cves()
        
        return match 

    def get_response(self,target_url):
        # requests.exceptions.SSLError
        try:
            return (requests.get(target_url,headers=self.headers,verify=False))
        except requests.exceptions.ConnectionError:
            return False

    def check_patterns(self):
        sttg_obj = self.get_sttg_obj()
        for sttg_t, sttg_p in sttg_obj.items():

            if not self.quiet_mode:
                print(f'[{self.siddhi}:{sttg_t}]! Checking {colored(self.target_url, "cyan")}...')
            
            for f_pattern in self.sttg_patterns.get(sttg_t):
                resp = self.get_response(urljoin(self.target_url, f_pattern))                
                
                if not resp:
                    print(f'[{self.siddhi}:{sttg_t}]- {colored("Was not possible to identify the framework version", "yellow")}\n')
                    return False

                if resp.status_code == 200:
                    match_version = self.check_match(
                        self.get_hash(resp.text),**sttg_p
                    )
                   
                    #input(match_version.get('cves'))
                    if match_version:
                        # if search issues mode enabled
                        # if called by another vmnf siddhi
                        if self.siddhi_call:
                            return match_version

                        if not self.quiet_mode:
                            mversion = colored(match_version['versions'], 'red', attrs=['bold'])
                            minv = colored(match_version['min'], 'cyan')
                            maxv = colored(match_version['max'], 'cyan')
                            tags = colored(len(self.versions_list[1:]), 'green') 

                            print(f'[{self.siddhi}:{sttg_t}]+ Running Django {mversion} / ({minv} - {maxv}) \n\t     → {tags} associated tags')

                            if match_version.get('cves') is not None:
                                hl_cves = colored(len(match_version.get('cves')), 'green')
                                print(f'\t     → {hl_cves} CVEs')

                            if match_version.get('tcts') is not None:
                                hl_tcts = colored(len(match_version.get('tcts')), 'green')
                                print(f'\t     → {hl_tcts} Security Tickets')
                            print()

                            #print(self.versions_list[1:])
                            if self.exit_on_success:
                                return True
                        break
                    else:
                        if not self.quiet_mode:
                            print(f'\n[{sttg_t}]→ No issues identified for Django {self.search_version} version.')
                        return False
                
                elif resp.status_code == 404:
                    if not self.quiet_mode:
                        print('Was not possible to identify the framework version')
                    return False
                    
        if not match_version:
            return False

    def start(self):
        if not self.target_url:
            print('[sttg] Scope Error: Missing target URL. Use --target-url ip:port\n')
            return False

        return(self.check_patterns())

