# -*- coding:utf-8 -*-

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
from res.colors import *
from time import sleep 
import requests
import pathlib
import scrapy
import sys,os
import re


from pathlib import Path



class vwce(scrapy.Spider):
    name = 'vwce'
    
    def __init__(self, *args,**handler):
        super(vwce, self).__init__(*args,**handler)
        self.handler = handler
        self.caller_plugin = handler.get('module_run')
        self.caller_path = f'{Path().absolute()}/siddhis/{self.caller_plugin}'
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
        self.started = True
        
        print()        
        if response.url in self.url_pool:
            return 

        self.url_pool.append(response.url)

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
                    callback=self.parse
                )
            cprint(f"    + {_url_item_['url'].strip()}", 'blue', attrs=attrs)
            yield _url_item_

        #print()

    def closed(self,reason):
        from scrapy.crawler import CrawlerProcess
        from scrapy.crawler import CrawlerRunner
        from twisted.internet import reactor
        from siddhis.d4m8.engines._d4m8_engine import d4m8
        from siddhis.d4m8.engines._crawler_settings import settings
    
        if self.caller_plugin != 'viewc':

            with open(f'{self.caller_path}/output.txt', 'w+') as f:
                [f.write(u + '\n') for u in self.discovered_urls]
                f.close()
            
            self.handler['scope'] = self.discovered_urls
            self.handler['scope'].extend(
                [urljoin(self.handler['target_url'], p) \
                    for p in self.handler['patterns'] \
                        if p and p is not None 
                ]
            )
           
            runner = CrawlerRunner(dict(settings))
            daemon = runner.crawl(d4m8, **self.handler)
            reactor.run(0)

        if self.single_target and not self.started:
            cprint("[{}] Connection failure: check the HTTP scheme and try again.\n".format(
                datetime.now()), 'red')
            
        print() 
        if self.started and self.handler.get('callback_session',False):
            vmnf_callback_session = self.handler.get('prompt',False)

            # disable callback session flag
            #self.handler['callback_session'] = False

            if not self.handler.get('siddhi_callbacks',False):
                self.handler['siddhi_callbacks'] = []

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
        
            
        #if self.caller_plugin != 'viewc':
        #    return True
        
        os._exit(os.EX_OK)
        
        
