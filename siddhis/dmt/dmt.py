# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                    - DMT v2- 


    Django Misconfiguration Tracker module for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch

"""

from res.vmnf_validators import get_tool_scope as get_scope
from twisted.internet.defer import inlineCallbacks
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import CloseSpider
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
import collections
import twisted

import sys, re, os, random, string, platform, signal
from datetime import datetime
from time import sleep
import argparse

from core.vmnf_shared_args import VimanaSharedArgs
from res import vmnf_banners

from .engines._crawler_settings import settings
from .engines._crawler_settings import headers
from .engines._dmt_parser import DMTEngine as _dmt_




class siddhi:   
    def __init__(self,**vmnf_handler):
   
        self.vmnf_handler = vmnf_handler
        self.target_url = vmnf_handler['target_url'] 
        self.threads = self.vmnf_handler['threads']
        self.default_threads = 4
        self.debug = self.vmnf_handler['debug'] 
        self.verbose = self.vmnf_handler['verbose']
        self.quiet_mode = True if not self.verbose else False
        self.catched_exceptions = []

    def parse_args(self):
        ''' ~ siddhi needs only shared arguments from VimanaSharedArgs() ~'''
        parser = argparse.ArgumentParser(
                add_help=False,
                parents=[VimanaSharedArgs().args()]
        )
        return parser
    
    def start(self):
        '''in fact most modules do not need to implement their own parser, 
        because vimana already sends the command line handler with all 
        the arguments for the modules executed with the 'run' command
        so this is just a test'''

        djunch_handler= argparse.Namespace(
            ignore_state = False,       # ignore state - disable IP and port state verification
            single_target = False,      # single target scope
            scope  = False,             # file with a list of targets
            range  = False,             # ip range, 192.168.12.0-20
            cidr   = False,             # cidr range: 192.168.32.0/26
            port   = False,             # single port verification
            single_port   = None,       # single port verification
            portr  = False,             # port range: 8000-8010
            portl  = False,             # port list: 8999, 5001, 9000, 7120
            debug  = False              # debug mode
        )

        options = self.parse_args()
        djunch_handler.args = options.parse_known_args(
            namespace=djunch_handler)[1]
        
        # adjustments to the arguments for an engine
        headers['Origin']   = self.vmnf_handler['target_url']
        headers['Referer']  = self.vmnf_handler['target_url']
        self.vmnf_handler['fuzz_settings'] = settings
        self.vmnf_handler['meta'] = {
            "max_retry_times": 3,
            'dont_merge_cookies': True
        }
        self.vmnf_handler['download_timeout'] = 3
        self.vmnf_handler['method'] = 'GET'
        self.vmnf_handler['headers'] = headers

        if self.vmnf_handler['disable_cache']:
            settings['HTTPCACHE_ENABLED'] = False

        try:
            process = CrawlerProcess(dict(settings))
            process.crawl(_dmt_, **self.vmnf_handler)
            process.start(stop_after_crawl=False) 
        except twisted.internet.error.ReactorAlreadyInstalledError:
            runner = CrawlerRunner(dict(settings))
            d = runner.crawl(_dmt_, **self.vmnf_handler)
            reactor.run(0)
