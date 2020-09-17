from resources.colors import *
import requests
from time import sleep
from html.parser import HTMLParser
from . vmn_ua import switchAgent   
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def createSession(**vmnf_handler):
    
    target_url = vmnf_handler['target_url']
    random_ua = vmnf_handler['random']
    #debug = vmnf_handler['debug']
    debug = False

    retries = 3
    b_factor = 0.3
    force_list = (500, 502, 504)
    timeout = 10

    try:
        User_Agent = switchAgent()
        if debug:
            header = '{}→{}'.format(Gn_c, D_c) 
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
            raise_on_status  = False       
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        response = session.get(
            target_url, 
            stream=True, 
            timeout=timeout
        )
        
        # ------------------------------------
        # debug settings 
        # ------------------------------------
        if debug:
            target = target_url[:60]
            print("-"*(len(target)+30))
            print("Response: {} / Target: {}".format(response.status_code, target_url))
            print("-"*(len(target_url)+30))
            for k,v in response.headers.items():
                print("{}: {}".format(k,v))
            print("-"*(len(target)+30) + "\n")

        return response 
    
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
