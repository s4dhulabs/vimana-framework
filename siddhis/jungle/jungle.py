# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                - jungler v1 -


    Brute-force utility for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch
    
"""
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

from twisted.internet.error import ReactorAlreadyRunning
import sys, re, os, random, string, platform,signal
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from time import sleep
import collections
import argparse
import twisted

from .engines._jungle_engine import jungle_engine
from core.vmnf_shared_args import VimanaSharedArgs
from .engines._crawler_settings import settings
from res.vmnf_banners import load_viwec
from res import vmnf_banners


class siddhi:   
    module_information = collections.OrderedDict()
    module_information = {
        "Name":            "Jungle",
        "Info":            "Brute force utility to attack Django admin portal",
        "Category":        "Framework",
        "Framework":       "Django",
        "Type":            "Attack",
        "Module":          "siddhis/jungle",
        "Author":          "s4dhu <s4dhul4bs[at]prontonmail.ch",
        "Brief":           "Brute force utility to audit Django admin portal",
        "Description":     """ 
        
        \r  Utility to brute force Django administration portal. 
        \r  In the present version, the tool adheres to the Django administration endpoint. 
        \r  Future versions may add other features, such as session auditing and other 
        \r  authentication endpoints.
        
        """
    }

    module_arguments = VimanaSharedArgs().shared_help.__doc__

    def __init__(self,**vmnf_handler):
        self.vmnf_handler = vmnf_handler
    
    def parse_args(self):
        ''' ~ siddhi needs only shared arguments from VimanaSharedArgs() ~'''
        parser = argparse.ArgumentParser(
            add_help=False,
            parents=[VimanaSharedArgs().args()]
        )
        return parser
    
    def start(self):
        if not self.vmnf_handler.get('target_url',False):
            print(VimanaSharedArgs().shared_help.__doc__)
            sys.exit(1)
  
        target_url = self.vmnf_handler.get('target_url')
        if not target_url.startswith('http'):
            self.vmnf_handler['target_url'] = f'http://{target_url}'

        runner = CrawlerRunner(dict(settings))
        daemon = runner.crawl(jungle_engine, **self.vmnf_handler)
        reactor.run(0) 

        

