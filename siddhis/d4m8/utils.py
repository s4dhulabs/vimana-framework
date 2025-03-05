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

from neotermcolor import cprint, colored as cl
from urllib.parse import urlparse
from time import sleep
import json
import os

from pygments.lexers import HtmlLexer
from pygments.formatters import TerminalFormatter
from pygments import highlight


def is_django_exception(response):
    djx_patterns = ["Exception Type", "Django Version", "Django settings file"]
    return all(pattern in response.text for pattern in djx_patterns)

def get_form_dict(response):
    _fi_ = response.css('input::attr(name)').getall()
    return dict(zip(_fi_, ['' for z in _fi_]))

def is_valid_url(URL):
    try:
        result = urlparse(URL)
        return all([result.scheme, result.netloc])  # Check if scheme and netloc are present
    except ValueError:
        return False

def parse_rule_scope():
    SCOPE = []
    ACTIVE_RULES = {}

    RULES = get_rules()

    for rule_path in RULES:
        RULE_NAME = rule_path.split('/')[-1].split('.')[0]
        
        with open(rule_path, 'r') as f:
            try:
                RULE = json.load(f)
            except json.decoder.JSONDecodeError:
                print(f"    [d4m8]→ Something is wrong with {colored(RULE_NAME,'red')} rule. Check the JSON syntax and try again.\n")
                sys.exit(1)

            # Build a consolidate scope with active rules
            ACTIVE_RULES[RULE_NAME] = RULE
            ACTIVE_RULES[RULE_NAME]['SCOPE'] = []

            # Rule Request (optional)
            RULE_REQUEST = RULE.get('REQUEST', False)

            if RULE_REQUEST:

                # Rule request urls (optional): List
                RULE_REQUEST_URLs = RULE_REQUEST.get('request_urls',False)

                if RULE_REQUEST_URLs:
                    SCOPE = []

                    # Feed D4M8 scope with Rule request urls
                    for URL in RULE_REQUEST_URLs:
                        SCOPE.append(URL)

                        # feed current active rule scope
                        ACTIVE_RULES[RULE_NAME]['SCOPE'].append(URL)
                
                # data to be used in the specified target input (optional): Dict
                FORM_INPUT_DATA = RULE_REQUEST.get('form_target_input_data',False)

                if FORM_INPUT_DATA:
                    ACTIVE_RULES[RULE_NAME]['DATA'] = {}

                    for form_input,file_data in FORM_INPUT_DATA.items():
                        if not os.path.exists(file_data):
                            print(f"    [d4m8]→ File {cl(file_data,'red')} not found. Check `form_input_file_data` in {cl(RULE_NAME,'red')} rule\n")
                        else:
                            ACTIVE_RULES[RULE_NAME]['DATA'][form_input] = []

                            with open(file_data) as f:
                                DATA = [d.strip() for d in f.readlines()]

                                # ConnectionRefusedError_AccountsDump['DATA']['email'] 

                                ACTIVE_RULES[RULE_NAME]['DATA'][form_input] = DATA
                    
    return ACTIVE_RULES

def dlexer(_fields_):
    for field in _fields_:
        hl_f = highlight(str(field),HtmlLexer(),TerminalFormatter())
        print('\t   ' + hl_f.strip().ljust(os.get_terminal_size().columns - 1), end="\r")
        sleep(0.07)

    for field in _fields_:
        _item_ = ('\t   ' + highlight(str(field),HtmlLexer(),TerminalFormatter()).strip())
        print(_item_)
        sleep(0.01)
    sleep(0.10)

def get_rules():
    current_path = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(current_path, 'rules')
    file_list = os.listdir(rules_path)
    return [os.path.join(rules_path, r) for r in file_list if r.endswith(".json")]

    #for json_file in json_files:
        #print(os.path.join(directory_path, json_file))

def parse_request_data(request_text):
    lines = request_text.strip().split('\n')
    formatted_request = "\n".join(line.strip() for line in lines if line.strip())
    request = formatted_request.split('\n')

    endpoint=False
    for l in request:
        split_header = l.split(': ')
        if split_header[0] == 'Referer':
            endpoint = split_header[1]

    body = request[-1]
    if not '&' in body and not '=' in body:
        return False,False

    data_set = {}
    for param in body.split('&'):
        key, value = param.split('=')
        data_set[key] = value

    return endpoint, data_set

def parse_request_data_v2(request_text):
    lines = request_text.split('\n')
    headers_done = False
    body_lines = []
    endpoint = False
    content_type = None
    boundary = None

    for line in lines:
        if not headers_done:
            if line.startswith('Referer:'):
                endpoint = line.split(': ', 1)[1]
            if line.startswith('Content-Type:'):
                content_type = line.split(': ', 1)[1]
                if 'boundary=' in content_type:
                    boundary = '--' + content_type.split('boundary=')[1]
            if line == '':
                headers_done = True
        else:
            body_lines.append(line)

    body = "\n".join(body_lines)

    if content_type and 'multipart/form-data' in content_type and boundary:
        data_set = {}
        parts = body.split(boundary)
        for part in parts:
            if 'Content-Disposition' in part:
                try:
                    headers, content = part.split('\n\n', 1)
                    content_disposition = headers.split('\n')[0]
                    if 'name="' in content_disposition:
                        name = content_disposition.split('name="')[1].split('"')[0]
                        data_set[name] = content.strip()
                except ValueError:
                    continue
        return endpoint, data_set

    if not '&' in body and not '=' in body:
        return False, False

    data_set = {}
    for param in body.split('&'):
        key, value = param.split('=')
        data_set[key] = value

    return endpoint, data_set

