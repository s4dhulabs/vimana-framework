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
import sys
import os
from pathlib import Path

from .config import *
from core.vmnf_utils import (
    load_plugin_cache,
    gen_issues_table
)

# vflogging
import logging
from core.vmnf_log_utils import configure_logging
configure_logging(os.path.basename(__file__))

# --- OSV API and Framework Mapping ---
FRAMEWORK_PACKAGES = {
    'django': 'django',
    'flask': 'flask',
    'fastapi': 'fastapi',
    'pyramid': 'pyramid',
    'bottle': 'bottle',
    'tornado': 'tornado',
    'sanic': 'sanic',
    'falcon': 'falcon',
    'quart': 'quart',
    'web2py': 'web2py'
}
OSV_API = "https://api.osv.dev/v1/query"
CACHE_DURATION_HOURS = 24

class siddhi:
    def __init__(self, **vmnf_handler) -> None:
        logging.info("Breathing in...")

        self.caller = vmnf_handler.get('module_run',False)
        self.vmnf_handler = vmnf_handler
        self.register = []
        self.django_version = vmnf_handler.get('django_version')
        
        # Framework/version logic
        self.framework = (vmnf_handler.get('framework') or None)
        self.framework_version = (
            vmnf_handler.get('framework_version') or
            vmnf_handler.get('django_version') or
            None
        )

        if not self.framework:
            print("[prana]→ Please specify a framework with --framework (e.g., --framework django)")
            sys.exit()
        elif not self.framework_version:
            print(f"[prana]→ Please specify a version for {self.framework} with --framework-version")
            sys.exit()
        self.framework = self.framework.lower()
        
        # Cache paths (now framework-aware)
        issue_type = 'cves'
        plugin_scope = f'{self.framework}/{issue_type}'
        self.cache_dir = f'vimana/__cache__/{plugin_scope}'
        self.abs_cache_path = os.path.join(os.path.expanduser("~"), self.cache_dir)
        self.issues_path = f"{self.abs_cache_path}/{self.framework_version}.json"
        
        self.engineitself = True if (self.caller and self.caller == 'prana') else False
        self.cache_load_enabled = not vmnf_handler.get('ignore_cache',False)
        self.cache_enabled = not vmnf_handler.get('disable_cache',False)
        self.force_update = vmnf_handler.get('force_update', False)
        
        self.vmnf_handler.update(
            {
                'issues_path': self.issues_path,
                'django_version': self.django_version,
                'framework': self.framework,
                'framework_version': self.framework_version,
                'issue_type': issue_type
            }
        )

        logging.info("Breathing out...")
        
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

        hl_django_version = cl(self.django_version,'green')

        if self.cache_load_enabled:
            try:
                cves, issues_table = load_plugin_cache(self.vmnf_handler)

                if self.engineitself:
                    print(f"[{cl(self.caller,'red')}]→ {cl(len(cves),'green')} CVEs for Django {hl_django_version}")
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


        if response.status_code != 200:
            print(f"[{cl(self.caller,'red')}]→ Error acquiring CVEs for Django {hl_django_version}")

        try:
            cve_data = response.json()
        except requests.exceptions.JSONDecodeError:
            return False

        if "result" not in cve_data:
            print(f"N[{cl(self.caller,'red')}]→ o CVEs found for Django {hl_django_version}")
            return

        self.cves = cve_data["result"]["CVE_Items"]
        self.total_results = cve_data["totalResults"]
        
        if self.total_results > self.resper_page:
            self.parse_pages()

        self.parse_cves()

        if self.cache_enabled:

            #if not os.path.exists(self.cache_dir):
            if not os.path.exists(self.abs_cache_path):
                os.makedirs(self.abs_cache_path)
       
            if not os.path.exists(self.issues_path):
                with open(self.issues_path, 'w') as f:
                    json.dump(self.register, f, indent=4)
        
        issues_table = gen_issues_table(self.register, 'CVEs')
        
        if self.engineitself:
            print(f"[{cl(self.caller,'red')}]→ {cl(len(self.cves),'green')} CVEs for Django {hl_django_version}")
            input() if self.vmnf_handler.get('pause_steps') else sleep(1)
            print(issues_table) 
            return True

        return self.register,issues_table

    def get_cves(self, framework=None, version=None, use_cache=True, force_update=False):
        framework = (framework or self.framework).lower()
        version = version or self.framework_version
        cache_path = f"{self.abs_cache_path}/{version}.json"
        # Use cache if available and not forced to update
        if use_cache and os.path.exists(cache_path) and not force_update:
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cves = json.load(f)
                return cves
            except Exception as e:
                print(f"[prana]→ Error loading cache: {e}")
        # Fetch from OSV API
        package = FRAMEWORK_PACKAGES.get(framework)
        if not package:
            print(f"[prana]→ Unsupported framework: {framework}")
            return []
        query = {"package": {"ecosystem": "PyPI", "name": package}}
        try:
            resp = requests.post(OSV_API, json=query, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                print(f"[prana]→ Unexpected response from OSV API: {data}")
                return []
            vulns = data.get('vulns', [])
            if not isinstance(vulns, list):
                print(f"[prana]→ Unexpected 'vulns' format from OSV API: {vulns}")
                return []
            # Filter by version if possible
            filtered = self._filter_by_version(vulns, version)
            # Save to cache
            if self.cache_enabled:
                os.makedirs(self.abs_cache_path, exist_ok=True)
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(filtered, f, indent=2, ensure_ascii=False)
            return filtered
        except Exception as e:
            print(f"[prana]→ Error acquiring CVEs for {framework} {version}: {e}")
            try:
                print(f"[prana]→ Raw response: {resp.text}")
            except Exception:
                pass
            return []

    def _filter_by_version(self, vulns, version):
        import traceback
        from packaging import version as pkg_version
        filtered = []
        for vuln in vulns:
            if not isinstance(vuln, dict):
                print(f"[prana]→ Skipping non-dict CVE entry: {vuln}")
                continue
            try:
                affected = False
                for aff in vuln.get('affected', []):
                    for rng in aff.get('ranges', []):
                        if rng.get('type') == 'ECOSYSTEM':
                            for event in rng.get('events', []):
                                if 'introduced' in event:
                                    try:
                                        if pkg_version.parse(version) >= pkg_version.parse(event['introduced']):
                                            affected = True
                                    except Exception:
                                        pass
                                if 'fixed' in event:
                                    try:
                                        if pkg_version.parse(version) < pkg_version.parse(event['fixed']):
                                            affected = True
                                    except Exception:
                                        pass
                if affected:
                    try:
                        filtered.append(self._process_osv_vuln(vuln))
                    except Exception as e:
                        print(f"[prana]→ Exception in _process_osv_vuln for entry: {vuln}")
                        traceback.print_exc()
                        continue
            except Exception as e:
                print(f"[prana]→ Exception while processing CVE entry: {vuln}")
                traceback.print_exc()
                continue
        return filtered

    def _process_osv_vuln(self, vuln):
        # Normalize OSV vuln to prana format
        vuln_id = vuln.get('id', '')
        summary = vuln.get('summary', '')
        details = vuln.get('details', '')
        description = summary or details or 'No description available'
        severity = 'UNKNOWN'
        cvss_score = 'N/A'
        severity_info = vuln.get('database_specific', {}).get('severity')
        if isinstance(severity_info, dict):
            severity = severity_info.get('type', 'UNKNOWN').upper()
            if 'score' in severity_info:
                cvss_score = severity_info['score']
        elif isinstance(severity_info, str):
            severity = severity_info.upper()
        # else: leave as UNKNOWN
        affected_versions = []
        fixed_versions = []
        for aff in vuln.get('affected', []):
            for rng in aff.get('ranges', []):
                if rng.get('type') == 'ECOSYSTEM':
                    for event in rng.get('events', []):
                        if 'introduced' in event:
                            affected_versions.append(f">={event['introduced']}")
                        if 'fixed' in event:
                            fixed_versions.append(event['fixed'])
                            affected_versions.append(f"<{event['fixed']}")
        year = datetime.now().year
        if vuln_id.startswith('CVE-'):
            try:
                year = int(vuln_id.split('-')[1])
            except (IndexError, ValueError):
                pass
        elif 'published' in vuln:
            try:
                year = datetime.fromisoformat(vuln['published'].replace('Z', '+00:00')).year
            except:
                pass
        references = []
        for ref in vuln.get('references', []):
            url = ref.get('url')
            if url:
                references.append(url)
        return {
            'id': vuln_id,
            'description': description,
            'severity': severity,
            'cvss_score': cvss_score,
            'affected_versions': affected_versions,
            'fixed_versions': fixed_versions,
            'year': year,
            'source': 'OSV',
            'published': vuln.get('published', ''),
            'modified': vuln.get('modified', ''),
            'references': references
        }

    def start(self):
        cves = self.get_cves()
        hl_framework = cl(self.framework, 'green')
        hl_version = cl(self.framework_version, 'green')
        if self.engineitself:
            print(f"[prana]→ {cl(len(cves),'green')} CVEs for {hl_framework} {hl_version}")
            sleep(1)
            if cves:
                print(tabulate(
                    [[c['id'], c['severity'], c['cvss_score'], c['description'][:60] + ('...' if len(c['description']) > 60 else '')] for c in cves],
                    headers=["CVE ID", "Severity", "CVSS", "Description"],
                    tablefmt="fancy_grid"
                ))
            else:
                print(f"[prana]→ No CVEs found for {hl_framework} {hl_version}")
        return cves

# For import by other plugins
get_cves = lambda framework, version, use_cache=True, force_update=False: siddhi(framework=framework, framework_version=version).get_cves(framework, version, use_cache, force_update)


