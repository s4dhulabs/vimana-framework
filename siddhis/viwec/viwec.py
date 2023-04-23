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

from core.vmnf_engine_exceptions import engineExceptions as vfx
from neotermcolor import cprint,colored as cl

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
                self.vmnf_handler.get('target_url')
            ]
            
            vmnf_banners.load_viwec()

        if not self.vmnf_handler.get('scope',False):
            print(VimanaSharedArgs().shared_help.__doc__)
            sys.exit(1)

        if self.vmnf_handler.get('disable_cache',False):
            settings['HTTPCACHE_ENABLED'] = False

        runner = CrawlerRunner(dict(settings))
        daemon = runner.crawl(vwce, **self.vmnf_handler)
        reactor.run(0) 
        
