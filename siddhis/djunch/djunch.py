# -*- coding: utf-8 -*-
"""
             _   _   _   _   _   _  
            / \ / \ / \ / \ / \ / \ 
        ((-( V | 1 | M | 4 | N | 4 )-))
            \_/ \_/ \_/ \_/ \_/ \_/ 

                - DJUNCH v2 -


    Django application fuzzer module for Vimana Framework 
    s4dhu <s4dhul4bs[at]prontonmail[dot]ch
    
"""


import sys, re, os, random, string, platform,signal
from datetime import datetime
from time import sleep
import collections
import argparse

from core.vmnf_shared_args import VimanaSharedArgs
from res import vmnf_banners

from .engines._dju_xparser import DJEngineParser as _djuep_
from .engines._crawler_settings import settings
from .engines._crawler_settings import headers

from siddhis.djunch.engines._dju_utils import DJUtils
from scrapy.utils.log import configure_logging
from scrapy.crawler import CrawlerProcess
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
import twisted



class siddhi:   
    def __init__(self,**vmnf_handler):
    
        self.pattern = '<dmt_trigger>'
        self._trigger_= {
            'html': False,
            'rtxc_mode': False,
            'trigger_start': False,
            'context_filter': False
        }

        self.vmnf_handler = vmnf_handler
        self.base_r = vmnf_handler['target_url'] 
        self.up_collection = vmnf_handler['patterns']
        self.total_patterns = len(self.up_collection)
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
        csrftoken='0' * 100
        headers['Origin']   = self.vmnf_handler['target_url']
        headers['Referer']  = self.vmnf_handler['target_url']
        #headers['Cookie'] = f"csrftoken={DJUtils().gen_csrftoken()}"
        self.vmnf_handler['fuzz_settings'] = settings
        self.vmnf_handler['meta'] = {"max_retry_times": 3,'dont_merge_cookies': True}
        self.vmnf_handler['download_timeout'] = 3
        self.vmnf_handler['method'] = 'GET'
        self.vmnf_handler['headers'] = headers
        self.vmnf_handler['cookie'] = {'csrftoken':'    '}

        # call djunch engine v2
        if self.vmnf_handler.get('sample'):
            settings['RETRY_TIMES'] = 1

        if self.vmnf_handler['disable_cache']:
            settings['HTTPCACHE_ENABLED'] = False

        runner = CrawlerRunner(dict(settings))
        d = runner.crawl(_djuep_, **self.vmnf_handler)
        
        try:
            reactor.run(0)
        except twisted.internet.error.ReactorAlreadyRunning:
            pass
            
            

