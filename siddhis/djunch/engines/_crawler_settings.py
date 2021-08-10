
headers = {
    'Host': '127.0.0.1',
    'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0",
    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    'Accept-Language': "en-US,en;q=0.5",
    'Accept-Encoding': "gzip, deflate",
    'Content-Type': "application/x-www-form-urlencoded",
    #'Content-Length': 1,
    'Origin': "http://127.0.0.1:8000",
    'Connection': "close",
    'Referer': False,
    'Cookie': "csrftoken=" + '00000000000000000000000000000',
    'Upgrade-Insecure-Requests': 1
}

settings = {
    'LOG_ENABLED': False,
    'LOG_LEVEL': "DEBUG",
    'COOKIES_ENABLED':True,
    'TELNETCONSOLE_ENABLED': False,
    'RANDOMIZE_DOWNLOAD_DELAY': True,
    'RETRY_TIMES': 3,
    'HTTPERROR_ALLOWED_CODES': [200,302,400,403,404,500],
    'REDIRECT_ENABLED':True,
    'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko)',
    'AUTOTHROTTLE_ENABLED': False,
    #'HTTPCACHE_ENABLED':True
    #'CONCURRENT_REQUESTS': 1
}

