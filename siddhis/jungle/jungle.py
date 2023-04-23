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

        

