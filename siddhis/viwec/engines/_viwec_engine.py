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

from twisted.internet import defer
from twisted.internet import reactor

from scrapy.exceptions import CloseSpider
from scrapy.http import HtmlResponse
from neotermcolor import colored,cprint
from urllib.parse import urlparse
from requests.exceptions import *
from urllib.parse import urljoin
from ._items import CrawlerPool
from datetime import datetime
from tabulate import tabulate
from .. res import config
from pathlib import Path
from res.colors import *
from time import sleep 
import hashlib
import requests
import pathlib
import scrapy
import sys,os
import json
import re


class vwce(scrapy.Spider):
    name = 'vwce'
    
    def __init__(self, *args,**handler):
        super(vwce, self).__init__(*args,**handler)
        self.handler = handler
        self.caller_plugin = handler.get('module_run')
        self.caller_path = f'{Path().absolute()}/siddhis/{self.caller_plugin}'

        issue_type = 'dast/output'
        plugin_scope = f'django/{issue_type}'
        self.cache_dir = f"vimana/__cache__/{plugin_scope}"
        self.abs_cache_path = os.path.join(os.path.expanduser("~"), self.cache_dir)

        if self.handler.get('endpoint_set', False):
            self.start_urls = [self.handler.get('endpoint_set')]
        else:
            self.start_urls = list(set(handler.get('scope',False)))

        self.domain_filter = urlparse(self.start_urls[0]).netloc
        self.saved_items = []
        self.url_pool =[]
        self.discovered_urls = []
        self.url_count = 0
        self.started = False
        self.single_target = True \
            if len(self.start_urls) == 1 \
                else False

        if not self.start_urls:
            self.log('[viwec:{}] Missing scope!'.format(datetime.now()))
            print('Missing scope')
            return
        
        self.verbose_enabled = handler.get('verbose', False)
        self.sample_mode = handler.get('sample',False)
        cprint('\n[{}] → Starting viwec against {} inital URLs '.format(
            datetime.now(),
            len(self.start_urls)
            ),'cyan'
        )
        sleep(1)        
    
    def parse(self,response):
        if self.handler.get('set_path_scope'):
            self.started = True
            return

        self.started = True
        depth = response.meta.get('depth', 0)

        #if depth >= 51:
        #    return

        if response.url not in self.discovered_urls:
            self.discovered_urls.append(response.url)
        
        if response.status in [200,301,302]:
            hl_c = 'green'
        elif response.status in [403,404]:
            hl_c = 'red'
        elif response.status == 500:
            hl_c = 'magenta'
        else: 
            hl_c = 'yellow'
        
        print('【{}】{} {}'.format(
            colored(response.status, hl_c),
            colored('⊶ ', hl_c, attrs=['bold']),
            colored(response.url, 'white')
            )
        )

        _url_item_ = {}
        for link in response.xpath('//a'):
            _url_item_['title'] = link.xpath('./text()').get().strip()
            _url_item_['link'] = link.xpath('.//@href').get().strip()
            _url_item_['url'] = response.urljoin(_url_item_['link']).strip()
            
            '''
            seems like there are some bugs with allowed_domains
            related to redirects. In this case, we're gonna do
            it in an explicit way (for now [it's enough])
            '''
            if self.domain_filter not in _url_item_['url']:
                continue 

            attrs=['dark']
            if _url_item_['url'] not in self.discovered_urls:
                attrs=[]
                self.saved_items.append(_url_item_)
                self.discovered_urls.append(_url_item_['url'])
                self.url_count +=1
                sleep(0.01)

                yield scrapy.Request(
                    _url_item_['url'],
                    callback=self.parse,
                    meta={'depth': depth + 1}
                )

            cprint(f"    + {_url_item_['url'].strip()}", 'blue', attrs=attrs)
            yield _url_item_


    def closed(self,reason):
        from scrapy.crawler import CrawlerProcess
        from scrapy.crawler import CrawlerRunner
        from twisted.internet import reactor
        from siddhis.d4m8.engines._d4m8_engine import d4m8
        from siddhis.d4m8.engines._crawler_settings import settings
    
        
        if self.single_target and not self.started:
            cprint("[{}] Connection failure: check the HTTP scheme and try again.\n".format(
                datetime.now()), 'red')
            
            os._exit(os.EX_OK)

        if self.discovered_urls:
            input() if self.handler.get('pause_steps') else None

        if self.started and self.handler.get('callback_session',False):
            vmnf_callback_session = self.handler.get('prompt',False)

            # disable callback session flag
            #self.handler['callback_session'] = False

            if not self.handler.get('siddhi_callbacks',False):
                self.handler['siddhi_callbacks'] = []

            origin = self.handler.get('origin',False)
            self.handler['siddhi_callbacks'].append(
                {
                    'cid': (len(self.handler['siddhi_callbacks']) + 1),
                    'when': datetime.now(),
                    'siddhi_run': self.handler.get('siddhi_run',False),
                    'type': 'crawler',
                    'findings': {
                        'url_items':self.saved_items
                    }

                }
            )

            # return to caller session
            vmnf_callback_session(**self.handler)

        # if not invoked by visual sessions manager
        if self.caller_plugin in ['d4m8']: #and origin not in ['naviSessions.manage']:
            from twisted.internet import reactor
            import ipdb

            with open(f'{self.caller_path}/output.txt', 'w+') as f:
                [f.write(u + '\n') for u in self.discovered_urls]
                f.close()
            
            if not self.handler.get('set_path_scope'):
                self.handler['scope'].extend(self.discovered_urls)
                self.handler['scope'].append(self.handler['target_url'])

                self.handler['scope'].extend(
                    [urljoin(self.handler['target_url'], p) \
                        for p in self.handler['patterns'] \
                            if p and p is not None 
                    ]
                )
            else:
                self.handler['scope'] = [urljoin(self.handler['target_url'], self.handler['set_path_scope'])]

            #from siddhis.jcolt.utils import get_hash
            scan_id = str(self.handler['scope']).encode('utf-8')
            scan_id = (hashlib.sha256(scan_id).hexdigest())

            #scan_id = get_hash(str(self.handler['scope']))[:10]
            full_output_path = f"{self.abs_cache_path}/{scan_id}.txt"
            os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
            
            
            with open(full_output_path, 'w') as f:
                for url in list(set(self.handler['scope'])):
                    f.write(f"{url}\n" )
                f.close()

            settings = self.handler.get('_settings_')
            runner = CrawlerRunner(dict(settings))
            daemon = runner.crawl(d4m8, **self.handler)
            d = defer.Deferred()
            daemon.addBoth(lambda _: d.callback(None))
     
            try:
                reactor.run()
            except KeyboardInterrupt:
                if reactor.running:
                    d.addBoth(lambda _: reactor.stop())
                    d.addBoth(lambda _: sys.exit(1))

        os._exit(os.EX_OK)
        
        
