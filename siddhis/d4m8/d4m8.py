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


from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor,defer

from twisted.internet.error import ReactorAlreadyRunning
import sys, re, os, random, string, platform,signal
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from time import sleep
import collections
import argparse
import twisted

from .engines._d4m8_engine import d4m8
from core.vmnf_shared_args import VimanaSharedArgs
from .engines._crawler_settings import settings
from res.vmnf_banners import load_viwec, default_naviban

from pathlib import Path
from .utils import parse_request_data, get_rules
import json


# vflogging
import logging
from core.vmnf_log_utils import configure_logging
configure_logging(os.path.basename(__file__))

class siddhi:   
    def __init__(self,**vmnf_handler):
        logging.info("Initializing D4M8 siddhi class...")
        self.vmnf_handler = vmnf_handler
        
        logging.info("D4M8 class initialized successfully!")

    def parse_args(self):
        ''' ~ siddhi needs only shared arguments from VimanaSharedArgs() ~'''
        parser = argparse.ArgumentParser(
            add_help=False,
            parents=[VimanaSharedArgs().args()]
        )
        return parser
    
    def start(self):

        from siddhis.dmt.engines._dmt_parser import DMTEngine as dmt
        from res.vmnf_fuzz_data import VMNFPayloads as vfp
        from siddhis.viwec.viwec import siddhi as viwec
        from neotermcolor import colored,cprint
        from ._intro import default
        from urllib.parse import urlparse

        #############################
        # -> D4M8 ANALYSIS SETTINGS
        #############################
        if self.vmnf_handler.get('agressive_mode', False):
            C_REQUEST = settings['CONCURRENT_REQUESTS'] * 5
            settings['CONCURRENT_REQUESTS'] = C_REQUEST
            settings['AUTOTHROTTLE_ENABLED'] = True
            settings['DOWNLOAD_TIMEOUT'] = 1
            settings['DUPEFILTER_CLASS'] = 'scrapy.dupefilters.BaseDupeFilter'
            settings['AUTOTHROTTLE_TARGET_CONCURRENCY'] = 2.0
            settings['AUTOTHROTTLE_MAX_DELAY'] = 0.5

        elif self.vmnf_handler.get('slow_mode'):
            settings['CONCURRENT_REQUESTS'] = 1
            settings['DEPTH_LIMIT'] = 1
            settings['AUTOTHROTTLE_MAX_DELAY'] = 40.0
            settings['AUTOTHROTTLE_TARGET_CONCURRENCY'] = 0.5

        URL_patterns = []
        self.vmnf_handler['patterns'] = ['admin/']
        framework_defined = 'django' # self.vmnf_handler.get('framework')
        self.vmnf_handler['auto'] = True
        RULE_SCOPE_SET = False

        #############################
        # -> D4M8 RULE SCANS
        #############################
        # rules just requires a JSON rule in d4m8/rules, no enrichment steps
        if self.vmnf_handler['rule_scan']:
            # IN RULE SCAN MODE WE ALREADY HAVE EVERYTHING
            runner = CrawlerRunner(dict(settings))
            daemon = runner.crawl(d4m8, **self.vmnf_handler)
            d = defer.Deferred()
            daemon.addBoth(lambda _: d.callback(None))
     
            try:
                reactor.run()
            except KeyboardInterrupt:
                if reactor.running:
                    d.addBoth(lambda _: reactor.stop())
                    d.addBoth(lambda _: sys.exit(1))
                    reactor.stop()
        
        #############################
        # -> D4M8 USE REQUEST FILE
        #############################
        # use request from a text file (copied from burp proxy, for example)
        if self.vmnf_handler['request_data_set']:
            request_file = self.vmnf_handler['request_data_set']
            
            if os.path.isabs(request_file):
                full_path = request_file
            else:
                full_path = os.path.join(os.getcwd(), request_file)

            if not os.path.exists(full_path):
                os.system('clear')
                default_naviban('')
                print(f"    [d4m8]→ Request file not found: {colored(full_path,'red')}")
                print()
                sys.exit(1)
            
            with open(full_path, 'r') as f:
                request_data = f.read()
                endpoint, data_set = parse_request_data(request_data)
                
                if not data_set:
                    os.system('clear')
                    default_naviban('')
                    print(f"    [d4m8]→ No parameters found on request file: {colored(request_file,'red')}")
                    print()
                    sys.exit(1)

                self.vmnf_handler['target_url'] = f"{urlparse(endpoint).scheme}://{urlparse(endpoint).netloc}"
                self.vmnf_handler['request_data_set'] = data_set
                self.vmnf_handler['endpoint_set'] = endpoint

        if framework_defined:
            if framework_defined.lower() == 'django':
                from ..dmt.engines._crawler_settings import headers

                headers['Origin']   = self.vmnf_handler['target_url']
                headers['Referer']  = self.vmnf_handler['target_url']
                self.vmnf_handler['headers'] = headers
                
                # Call DMT to extend scope retrieving URL Patterns (if Debug is True)
                URL_patterns.extend(
                    dmt(**self.vmnf_handler).get_app_patterns(False)
                )

        if self.vmnf_handler['extended_scope']:
            URL_patterns.extend(
                vfp(**self.vmnf_handler).get_common_url_patterns()
            )

        self.vmnf_handler['patterns'] = URL_patterns

        #############################
        # -> VIWEC ENRICHMENT STEP 
        #############################
        # call vimana web crawler to enrich the previous scope [extended, dmt patterns]
        self.vmnf_handler['_settings_'] = settings
        viwec(**self.vmnf_handler).start()
        

        
