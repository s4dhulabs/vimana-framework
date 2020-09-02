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

from termcolor import colored,cprint
#from colors import *


class siddhi:
    module_information = collections.OrderedDict()
    module_information = {
        "Name":            "Prana",
        "Acronym":         False,
        "Category":        "Framework",
        "Framework":       "Django",
        "Type":            "Tracker",
        "Module":          "siddhis/prana",
        "Author":          "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":           "Tracks Django CVE ids",
        "Description":
        """

        \r  Simple utility to retrieve CVE ids from official Django security releases page.
        \r  This module receives a django version as argument and retrieve related CVE ids.
        \r  Prana is usually used as a resource by other Vimana modules. For example, 
        \r  DMT (Django Misconfiguration Tracker) uses to correlate the identified 
        \r  framework version (context 'environment') with the respective CVES.\n

        """

    }

    module_arguments = '''
    --django-version    Framework version     
    '''

    def __init__(self, django_version=False):
        
        self.django_version = django_version 
        self.cve_pool =[]
        self.desc_url = 'https://www.djangoproject.com/weblog/{}/{}/{}/security-releases/'
        self.sec_rel_url = 'https://docs.djangoproject.com/en/3.0/releases/security/'
        self.cve_register =[]
        self.nist_endpoint = 'https://nvd.nist.gov/vuln/detail/{}'
        self.month_num = {
            'january': 1,
            'february': 2,
            'march': 3,
            'april': 4,
            'may': 5,
            'june': 6,
            'july': 7,
            'august': 8,
            'september': 9,
            'october': 10,
            'november': 11,
            'december': 12
        }

    def get_cve_details(self,CVE_ID=False):

        # this because this method will be called in other ways in future
        if CVE_ID:
            self.CVE_ID = CVE_ID

        hyperlinks = []
        self.cve_details = {}

        sleep(3)
        response = requests.get(self.nist_endpoint.format(self.CVE_ID)) 
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

    def get_cves(self):
        '''
            Get cves from a given Django version
        '''
        
        response = requests.get(self.sec_rel_url)
        
        if response:
            self.soup = BeautifulSoup(response.text,"lxml")  

        for item in self.soup.find(class_='section'):
            try:
                for tag in item.find_next_sibling('div'):
                    try:
                        issue_text = str(tag.text).strip().encode(
                            "ascii", errors="ignore"
                        ).decode()
                        
                        affected_versions = re.findall('Django \d{1}\.\d{1}',issue_text)
                
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
                                    self.month_num[m.lower().rstrip()],
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
                                    'full_description': self.desc_url.format(y,m,d),
                                    'references': 'https://nvd.nist.gov/vuln/detail?vulnId={}'.format(nist_cve)
                                }
                                
                                # save entry
                                self.cve_register.append(cve_entry)

                    except AttributeError:
                        pass
            except TypeError:
                pass


    def start(self):
        '''
        acctualy prana doesnt need to implement argparser
        this module only required a django version and 
        this argument should be informed by modules 
        calling prana

        implementing argparser can cause problems 
        when the module is called by other siddhis (dunno why [yet)

        
        parser = argparse.ArgumentParser(description='prana parser')
        parser.add_argument(
            "--django-version",
            action='store',
            required=True
        )
        args = parser.parse_args()
        
        '''

        # django_version in __init__ class [argument required]
        if not self.django_version:
            print('[prana: {}] Django version is required'.format(
                datetime.now()
                )
            )
            return False
        
        self.get_cves()

        if self.cve_register:
            return self.cve_register 

        return False
        
        

