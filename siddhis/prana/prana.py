# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                    - PRANA -


    Django CVE tracker module for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch

"""


from time import sleep
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
import collections
import requests
import re
import sys

from neotermcolor import colored,cprint
from ._putils import pranaset

class siddhi:
    def __init__(self, **vmnf_handler):
       
        # django_version in __init__ class [argument required]
        if not vmnf_handler.get('django_version'):
            print("\033[0m")
            print(f'[prana: {datetime.now()}] Django version is required: --django-version.')
            sys.exit()

        self.vmnf_handler = vmnf_handler
        self.django_version = vmnf_handler.get('django_version').strip()
        self.pset = pranaset()
        self.cve_pool =[]
        self.cve_register =[]
        
    def get_cve_details(self,CVE_ID=False):

        # this because this method will be called in other ways in future
        if CVE_ID:
            self.CVE_ID = CVE_ID

        hyperlinks = []
        self.cve_details = {}

        sleep(3)

        response = requests.get(self.pset.nist_endpoint.format(self.CVE_ID)) 
        response_data = response.text
        
        if not response or response.status_code != 200 \
            or 'CVE ID Not Found' in response_data:
            return False

        soup = BeautifulSoup(response_data, "lxml")

        # cve description
        for i in soup.findAll("div", {"id": "vulnAnalysisDescription"}):
            description = str(i.find('p').text).rstrip()

        # get hiperlinks
        for i in soup.findAll("table", {"class": "table table-striped table-condensed table-bordered detail-table"}):
            for a in i.find_all('a', href=True):
                link = (a['href']).rstrip().strip("\n")
                if link not in hyperlinks:
                    hyperlinks.append(a['href'])

        # save details to 'cve_entry'
        self.cve_details = {
            'description': description,     # string
            'hyperlinks': hyperlinks        # list
        }

        return self.cve_details

    def issues_presentation(self):
        from siddhis.djunch.engines._dju_utils import DJUtils

        tables = DJUtils().get_report_tables()
        cves_tbl = tables.get('cves')
        cves_tbl.title = colored(
            f"CVE IDs for Django {self.django_version}",
                "white",attrs=['bold']
        )
        for entry in self.cve_register:
            cves_tbl.add_row(
                [
                    colored(entry['id'],'green'),
                    entry['title'].rstrip(),
                    entry['date'].rstrip()

                ]
            )
        
        print(cves_tbl)

    def get_cves(self):
        '''Get cves from a given Django version'''
        
        response = requests.get(
            self.pset.sec_rel_url.format(self.django_version)
        )

        if response:
            self.soup = BeautifulSoup(response.text,"lxml")  

        for item in self.soup.find(class_='section'):
            try:
                for tag in item.find_next_sibling('div'):
                    try:
                        issue_text = str(tag.text).strip().encode(
                            "ascii", errors="ignore").decode()
                        
                        affected_versions = re.findall('Django \d{1}\.\d{1}', issue_text)
                        
                        if self.django_version in str(affected_versions):
                            self.CVE_ID  = (re.search('(CVE-\d{4}-\d{4,5})',issue_text).group()).strip()
                             
                            if not self.CVE_ID in self.cve_pool:
                                self.cve_pool.append(self.CVE_ID)
                                nist_cve = self.CVE_ID.replace('CVE-','')
                                release_date = issue_text.split('-')[0]
                       
                                try:
                                    adv_date = (issue_text.split('\n')[0])
                                    m = adv_date.split()[0].lower()[:3]
                                    d = adv_date.split()[1].strip(',')
                                    y = adv_date.split()[2]
                                except IndexError:
                                    pass

                                c_adv_date = colored(adv_date, 'white',attrs=['bold'])
                                # there is a little bug in this point, long title with new line will not be shown whole
                                title = str(issue_text.split('\n')[1]).split('.')[0].rstrip('\n')
                                 
                                c_title = colored(title, 'yellow')
                                c_version = colored(self.django_version,'red')
                                
                                issue_text = (issue_text.replace(adv_date, c_adv_date))     
                                issue_text = (issue_text.replace(title,c_title))
                                issue_text = (issue_text.replace(self.django_version,c_version))
                                
                                m,d,y = release_date.split()
                                
                                release_date = '{}/{}/{}'.format(
                                    self.pset.month_num[m.lower().rstrip()],
                                    d.replace(",",'').rstrip(),
                                    y.rstrip()
                                )
                                
                                # register new cve entry
                                cve_entry = {
                                    'id': self.CVE_ID,
                                    'date': release_date,
                                    'c_date': c_adv_date,
                                    'c_title': c_title,
                                    'c_version': c_version,
                                    'title': title,
                                    'text': issue_text,
                                    'full_description': self.pset.desc_url.format(y,m,d),
                                    'references': self.pset.nist_detail.format(nist_cve)
                                }
                               
                                # save entry
                                self.cve_register.append(cve_entry)
                                
                    except AttributeError:
                        pass
            except TypeError:
                pass

        # when running prana by command line vf run -m prana
        if self.vmnf_handler.get('framework_search_version'):
            self.issues_presentation()
            
            return True

        return self.cve_register

    def start(self):
        self.get_cves()

        
        

