# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
#from scrapy.spiders import CrawlSpider, Rule
#from scrapy.linkextractors import LinkExtractor



class CrawlerPool(scrapy.Item):
    urls = scrapy.Field()


