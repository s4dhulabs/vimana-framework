from neotermcolor import cprint,colored as cl
from string import ascii_uppercase, digits
from random import choices,uniform
from tabulate import tabulate
from mimesis import Generic
from datetime import datetime
from time import sleep
import textwrap
import requests
import json
import os

from .config import *
from core.vmnf_utils import (
    load_plugin_cache,
    gen_issues_table
)

class siddhi:
    def __init__(self, **vmnf_handler) -> None:
        if not vmnf_handler.get('django_version'):
            print("\033[0m")
            print(f'[prana: {datetime.now()}] Django version is required: --django-version.')
            sys.exit()

        self.caller = vmnf_handler['module_run']
        self.vmnf_handler = vmnf_handler
        self.register = []
        self.django_version = vmnf_handler.get('django_version')
        issue_type = 'cves'
        plugin_scope = f'django/{issue_type}'
        self.cache_dir = f'siddhis/__cache__/{plugin_scope}'
        self.issues_path = f"{self.cache_dir}/{self.django_version}.json"
        self.engineitself = True if (self.caller == 'prana') else False
        
        self.cache_load_enabled = True \
            if (not self.vmnf_handler['ignore_cache']) else False
        self.cache_enabled = True \
            if (not self.vmnf_handler['disable_cache']) else False
        
        self.vmnf_handler.update(
            {
                'issues_path': self.issues_path,
                'django_version': self.django_version,
                'issue_type': issue_type
            }
        )
        
    def get_session(self):
        session_id = ''.join(choices(ascii_uppercase + digits, k=10))
        session = requests.Session()
        session.headers.update({
            "User-Agent": Generic().internet.user_agent(),
        })
        session.cookies.set("Session-ID", session_id)
        return session

    def parse_cves(self):
        for cve in self.cves:
            base_score = "N/A"
            cvss_vector = "N/A"
            cve_id = cve["cve"]["CVE_data_meta"]["ID"]
            description = cve["cve"]["description"]["description_data"][0]["value"]
            formatted_description = '\n'.join(textwrap.wrap(description, width=60))
            cwes = [desc["value"] for desc in cve["cve"]["problemtype"]["problemtype_data"][0]["description"]]
            cpes = [cpe["cpe23Uri"] for node in cve["configurations"]["nodes"] for cpe in node["cpe_match"]]
            url = f"{cve_detail_url}/{cve_id}"

            external_references = [ref["url"] \
                    for ref in cve["cve"]["references"]["reference_data"] \
                if ref["tags"] == ["External"]
            ]

            if len(cwes) == 1 and cwes[0] == 'NVD-CWE-Other':
                cwes = ['N/A']

            try:
                base_score = cve["impact"]["baseMetricV3"]["cvssV3"]["baseScore"]
                cvss_vector = cve["impact"]["baseMetricV3"]["cvssV3"]["vectorString"]
            except KeyError:
                pass

            dec_ref = f"""\n\n\n{url}\nCVSS Vector: {cvss_vector}\n"""
            self.register.append(
                {
                    'id': cve_id,
                    'description': formatted_description,
                    'cwes': cwes,
                    'cpes': cpes,
                    'ref_url': url,
                    'references': external_references,
                    'base_score': base_score,
                    'cvss_vector': cvss_vector
                }
            )

    def parse_pages(self):
        session = self.get_session()

        while self.start_index < self.total_results:
            self.start_index += self.resper_page
            if self.start_index >= self.total_results:
                break

            endpoint = api_endpoint.format(
                self.start_index,
                self.resper_page,
                self.keyword
            )
            response = session.get(endpoint)
            sleep(uniform(3,6))
            if response.status_code != 200:
                break

            json_data = response.json()
            self.cves += json_data["result"]["CVE_Items"]

    def get_cves_for_version(self,django_version:str=False):
        if django_version:
            self.django_version = django_version

        if self.cache_load_enabled:
            try:
                cves, issues_table = load_plugin_cache(self.vmnf_handler)
                if self.engineitself:
                    print(f"[{cl(self.caller,'red')}]→ {cl(len(cves),'green')} CVEs for Django {cl(self.django_version,'green')}")
                    input() if self.vmnf_handler.get('pause_steps') else sleep(1)
                    print(issues_table)
                    return True
                return cves, issues_table
            except TypeError:
                # acquire 
                pass

        session = self.get_session()
        sleep(uniform(3,10))
        self.start_index = 0
        self.resper_page = 30
        self.keyword = f'django+{self.django_version}'

        endpoint = api_endpoint.format(
            self.start_index,
            self.resper_page, 
            self.keyword
        )
        response = session.get(endpoint)
        cve_data = response.json()

        if "result" not in cve_data:
            print(f"No CVEs found for Django {django_version}")
            return

        self.cves = cve_data["result"]["CVE_Items"]
        self.total_results = cve_data["totalResults"]
        
        if self.total_results > self.resper_page:
            self.parse_pages()

        self.parse_cves()

        if self.cache_enabled:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
       
            if not os.path.exists(self.issues_path):
                with open(self.issues_path, 'w') as f:
                    json.dump(self.register, f, indent=4)
        
        issues_table = gen_issues_table(self.register, 'CVEs')
        
        if self.engineitself:
            (f"[{cl(self.caller,'red')}]→ {cl(len(cves),'green')} CVEs for Django {cl(self.django_version,'green')}")
            input() if self.vmnf_handler.get('pause_steps') else sleep(1)
            print(issue_table) 
            return True

        return self.register,issues_table

    def start(self):
        self.get_cves_for_version()


