import sys
sys.path.insert(0, '../')

from random import random, choice, randint
from urllib.parse import urlparse
from datetime import datetime
from mimesis import Generic

import re
import os
import signal
import scrapy
import twisted
import requests
from time import sleep
import urllib3.exceptions
from mimesis import Generic
from urllib.parse import urljoin
from scrapy.http import HtmlResponse


from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from scrapy.utils.log import configure_logging
from scrapy.shell import inspect_response
from scrapy.http.headers import Headers
from scrapy.http import HtmlResponse
from scrapy import signals

from neotermcolor import colored,cprint
from pygments import highlight

from siddhis.djunch.engines._dju_xparser import DJEngineParser
from res.vmnf_validators import get_tool_scope as get_scope
from siddhis.sttinger.sttinger import siddhi as sttinger
from core.vmnf_shared_args import VimanaSharedArgs
from siddhis.djunch.djunch import siddhi as Djunch
from res import colors

from rich.prompt import Confirm

