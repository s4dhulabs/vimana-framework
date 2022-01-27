# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                - VIWEC V1 -


    Web Crawler utility for Vimana Framework 
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

from .engines._viwec_engine import vwce
from core.vmnf_shared_args import VimanaSharedArgs
from .engines._crawler_settings import settings
from res.vmnf_banners import load_viwec
from res import vmnf_banners

class siddhi:   
    module_information = collections.OrderedDict()
    module_information = {
        "Name":            "viwec",
        "Info":            "Web crawler utility",
        "Category":        "Framework",
        "Framework":       "Django",
        "Type":            "Crawler",
        "Module":          "siddhis/viwec",
        "Author":          "s4dhu <s4dhul4bs[at]prontonmail.ch",
        "Brief":           "Web crawler utility",
        "Description":     """ 
        
        \r  Simple web crawler utility to work isolated (directly by command line), 
        \r  and also integrated to enrich post-analysis as with DMT. 
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
        if not self.vmnf_handler.get('callback_session'):
            self.vmnf_handler['scope'] = [
                self.vmnf_handler.get('target_url')]
            vmnf_banners.load_viwec()

        if not self.vmnf_handler.get('scope',False):
            print(VimanaSharedArgs().shared_help.__doc__)
            sys.exit(1)
    
        runner = CrawlerRunner(dict(settings))
        daemon = runner.crawl(vwce, **self.vmnf_handler)
        reactor.run(0) 

        

