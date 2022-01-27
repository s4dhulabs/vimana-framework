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
import argparse

from core.vmnf_shared_args import VimanaSharedArgs
from res import vmnf_banners

import collections

from .engines._crawler_settings import settings
from .engines._crawler_settings import headers
from .engines._dju_xparser import DJEngineParser as _djuep_

from scrapy.crawler import CrawlerProcess
#from twisted.internet.error import ReactorAlreadyRunning
import twisted

class siddhi:   
    module_information = collections.OrderedDict()
    module_information = {
        "Name":            "Djunch",
        "Info":            "Django (Unchained) fuzzer",
        "Category":        "Framework",
        "Framework":       "Django",
        "Type":            "Fuzzer",
        "Module":          "siddhis/djunch",
        "Author":          "s4dhu <s4dhul4bs[at]prontonmail[dot]ch",
        "Brief":           "Django application fuzzer ",
        "Description":
        """
        \r  This tool was designed to audit applications running with the Django
        \r  framework. Acts as an input module for Vimana to collect base data. 
        \r  DMT works seamlessly with other framework tools such as Djonga, DJunch,
        \r  which are respectively brute force and fuzzing tools. Among the various
        \r  actions taken are: Identification of the state of Debug extraction
        \r  and mapping of application URL Patterns. This first step will serve as
        \r  input to the fuzzer process (performed by DJunch) where tests will be
        \r  conducted to handle and map unhandled exceptions, extract and identify
        \r  sensitive information in the leaks, implementation failure testing. With
        \r  the same initial DMT input the brute force process will be performed on
        \r  the API authentication endpoints (if available) and also on the Django
        \r  administrative interface (if available).

        \r  At the end of the analysis it is possible to query the data obtained
        \r  by DMT, using the commands to access contexts, view information about
        \r  the identified exceptions, view the source code leaked by the affected
        \r  modules, track CVEs and Security Tickets.

        \r  Use 'args' cmdto see all available options: 
        \r  $ vimana args --module dmt 

        """

    }

    module_arguments = '''
    ==========
    # Djunch #
    ==========

    \r* Creating a fuzzer instance to use in another siddhi:

    \rTo create a djunch instance it is necessary to pass the target in the format: 
    \rscheme:ip/domain:port, a list with URL Patterns and the namespace with the command line arguments, 
    \rin this way, the fuzzer can be invoked:

    \rfuzz = Djunch(base_r, self.expanded_patterns,**self.vmnf_handler)
    \rfuzz.start()

    \rthe 'fuzz' object will be a list containing two entries: the issues identified and the contexts (envleak contexts).

    \r* to simplify, in this version fuzzer will run against one target at a time
    
    '''

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
        self.vmnf_handler['fuzz_settings'] = settings
        self.vmnf_handler['meta'] = {"max_retry_times": 3,'dont_merge_cookies': True}
        self.vmnf_handler['download_timeout'] = 3
        self.vmnf_handler['method'] = 'GET'
        self.vmnf_handler['headers'] = headers
        self.vmnf_handler['cookie'] = {'csrftoken':'    '}

        # call djunch engine v2
        if self.vmnf_handler.get('sample'):
            settings['RETRY_TIMES'] = 1
            #settings['HTTP_CACHE'] = True

        from scrapy.crawler import CrawlerRunner
        from twisted.internet import reactor
        
        runner = CrawlerRunner(dict(settings))
        d = runner.crawl(_djuep_, **self.vmnf_handler)
        reactor.run(0)
