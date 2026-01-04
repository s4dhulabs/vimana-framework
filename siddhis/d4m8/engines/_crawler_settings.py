settings = {
    'LOG_ENABLED':False,
    #'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    'REQUEST_FINGERPRINTER_IMPLEMENTATION':"2.7",
    'LOG_LEVEL': "DEBUG",
    'COOKIES_ENABLED': True,
    'TELNETCONSOLE_ENABLED': False,
    'RANDOMIZE_DOWNLOAD_DELAY': True,
    'RETRY_TIMES': 1,
    'HTTPERROR_ALLOW_ALL':True,
    'HTTPERROR_ALLOWED_CODES': [200,301,302,400,403,404,500],
    'REDIRECT_ENABLED':True,
    'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko)',
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    'AUTOTHROTTLE_MAX_DELAY': 10.0, 
    'DOWNLOAD_TIMEOUT':3,
    #'DOWNLOAD_DELAY':5,
    'HTTPCACHE_ENABLED': False,
    'RANDOMIZE_DOWNLOAD_DELAY': False,
    'CONCURRENT_REQUESTS': 16, # --agressive mode will change this to whatever like 100
    'DEPTH_LIMIT':0
}

