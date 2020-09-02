from resources.colors import *

global status



def createSession(target_url, random_ua = False, debug = False, d2t_mode = False):

    import requests
    from time import sleep
    from html.parser import HTMLParser
    from . vmn_ua import switchAgent   
    from requests import Session
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    global request
    global status
	
    retries = 3
    b_factor = 0.3
    force_list = (500, 502, 504)
    timeout = 10

    try:
        User_Agent = switchAgent()
        if debug:
            header = '{}→{}'.format(Gn, D_c) 
            ua = '{}{}{}'.format(Y_c, User_Agent, D_c)
            print("\n{} Using random user-agent: {}".format(header, ua))

        session = Session()
        session.headers.update({'User-Agent': User_Agent})
        retry = Retry(
            total   = retries,
            read    = retries,
            connect = retries, 
            backoff_factor   = b_factor, 
            status_forcelist = force_list,
            raise_on_status  = False       #without this flag exceptions in Django will be passed out with 500 status
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        request = session.get(
            target_url, 
            stream=True, 
            timeout=timeout
        )
        HParser = HTMLParser()
        raw_html = HParser.unescape(request.text)
        status = request.status_code

        # ------------------------------------
        # debug settings 
        # ------------------------------------
        if debug:
            target = target_url[:60]
            print("-"*(len(target)+30))
            print("Response: {} / Target: {}"%(status, target))
            print("-"*(len(target)+30))
            #for header in request.headers:
            for k,v in request.headers.items():
                print("{}: {}".format(k,v))
            print("-"*(len(target)+30) + "\n")


        # needs to retrieve not only with 200 status code
        # not found page in Django its important to check 404 
        return raw_html 
        #if status == 200 or d2t_mode:       
        #   return raw_html 
    
    except requests.exceptions.HTTPError as HE:
        if debug:
            _target_ = '{}{}{}'.format(Wn_, target_url, D_c)
            print("-> Not Found: '{}'".format(R_c, Rn_c, R_c, D_c, target))
            sleep(0.25)
            return False
    except requests.exceptions.InvalidURL:
        if debug: 
            _target_ = '{}{}{}'.format(Wn_, target_url, D_c)
            print("-> Invalid URL: '{}' Unable to establish connection"%(_target_))
            sleep(0.25)
            return False
    except requests.exceptions.ConnectionError as CE:
        if debug:
            print("-> Connection Error: {}".format(CE))
            sleep(0.25)
            return False
    except requests.exceptions.Timeout as TE:
        if debug:
            print("-> Timeout Error: {}".format(TE))
            sleep(0.25)
            return False
    except requests.exceptions.RequestException as RE:
        if debug:
            print("-> Something went wrong"%(RE))
            sleep(0.25)
            return False







