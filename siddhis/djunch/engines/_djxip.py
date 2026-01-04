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

from siddhis.djunch.engines._dju_utils import DJUtils
from pygments.formatters import TerminalFormatter
from neotermcolor import colored, cprint
from pygments.lexers import PythonLexer
from pygments import highlight

import django.core.exceptions as django_cx
import builtins



class ParseXItem:
    def __init__(self, xresponse):
        self.response = xresponse
        self.djx_definitions = self.get_djx_defs()

    def get_djx_defs(self):
        djx_def = {}
        djx_def['database'] = {
            'DatabaseError': 'NOT DEFINED',
            'DataError': 'NOT DEFINED',
            'Error': 'NOT DEFINED',
            'IntegrityError': 'A violation of a Django database relation occurred',
            'InterfaceError': 'NOT DEFINED',
            'InternalError': 'NOT DEFINED',
            'NotSupportedError': 'NOT DEFINED',
            'OperationalError': 'NOT DEFINED',
            'ProgrammingError': 'NOT DEFINED'
        }
        djx_def['core'] = {
            attr: getattr(django_cx, attr).__doc__
            for attr in dir(django_cx)
            if not attr.startswith('__')
        }
        djx_def['builtin'] = {
            attr_name: attr.__doc__
            for attr_name, attr in vars(builtins).items()
            if isinstance(attr, type) and issubclass(attr, BaseException)
        }
        return djx_def

    def parse_xsummary(self):
        EXCEPTION_SUMMARY = {}
        EXCEPTION_SUMMARY['Reason'] = None
        EXCEPTION_SUMMARY['Category'] = None

        for s in self.response.xpath('//div[@id="summary"]//tr'):
            key = s.xpath('.//th/text()').get().strip(':')
            value = s.xpath('.//td/text()').get()

            value_base = s.xpath('.//td//span')
            span_flag = bool(value_base)

            if span_flag:
                value = s.xpath('.//td/text()').get().replace('</span>', '').replace('</td>', '').strip()

            if not value:
                value = [
                    v.replace('[', '').replace(']', '').replace("'", '').replace(',', '').strip()
                    for v in s.xpath('.//td//pre/text()').getall()
                ]

            EXCEPTION_SUMMARY[key] = value

        XType = EXCEPTION_SUMMARY.get('Exception Type',None)
        if not XType:
            return EXCEPTION_SUMMARY

        for category, exceptions in self.djx_definitions.items():
            if XType in exceptions:
                EXCEPTION_SUMMARY['Reason'] = exceptions[XType]
                EXCEPTION_SUMMARY['Category'] = f"{category.title()} Exceptions"

        return EXCEPTION_SUMMARY

    def dump_environment(self):
        ENVIRONMENT = {}
        REQS_TABLES = self.response.xpath('//*[@class="req"]//tbody')
        TABLES_ROWS = REQS_TABLES.xpath('.//tr')
        
        for ROW in TABLES_ROWS:
            if not ROW:
                continue

            key, value = (ROW.xpath('td//text()').getall())
            ENVIRONMENT[key] = value
        
        return ENVIRONMENT

    def dump_traceback(self):
        trace_count = 0
        EXCEPTION_PARSED_TRACEBACK = []
        MODULE_TRIGGER_INFO = {}
        TRACEBACK_OBJECTS = []
        SUMMARY = self.parse_xsummary()
        module_args = {} 
        ENVIRONMENT = {}
        TRACEBACK_COLLECTOR = []
        FRAME_USER = self.response.xpath('//div[@id="traceback"]//li[@class="frame user"]')
        EXCEPTION_TRACEBACK = self.response.xpath('//div[@id="traceback"]//li[@class="frame django"]')
        EXCEPTION_TRACEBACK.extend(FRAME_USER)
        LINE_NUMBER = None
        LINE_TRIGGER = None

        if FRAME_USER:
            VIEW_TRIGGER = [ f.xpath('.//code/text()').getall() for f in FRAME_USER ][0]
            VIEW_PATH = VIEW_TRIGGER[0]
        else:
            VIEW_TRIGGER = []
            VIEW_PATH = None
        VIEW_OBJECT = VIEW_TRIGGER[1] if len(VIEW_TRIGGER) > 1 else None

        for entry in EXCEPTION_TRACEBACK:
            highlight_code_snippets = []
            raw_code_snippets = []
            object_mapping = {}
            trace_count +=1

            try:
                ''' Django Version: 1.*.* (p:1.4.5)
                    Python Version: 2.*.* (p:2.6.6)
                    [module_path, function()]
                '''
                module, function = (entry.xpath('.//code/text()').getall())
            except ValueError:
                ''' Django Version: 3.*.* (p:3.1.12)
                    Python Version: 3.*.* (p:3.6.9)
                    [module_path]
                '''
                module = entry.xpath('.//code/text()').getall()[0].strip().replace(',','')
                function = entry.xpath('.//text()').getall()[2].strip().replace(',','').replace('in ','').split()[-1]
            
            code_snippet = [l for l in entry.xpath('.//div[@class="context"]//ol//li//pre').getall()]
            context_line_number = int(entry.xpath('.//div//ol[@class="context-line"][1]').get()[11:20].split()[0].strip('"'))
            context_line = entry.xpath('.//div//ol[@class="context-line"]//li//pre/text()').get()
            ref_line_number = int(entry.xpath('.//div//ol').get().split('\n')[0].split()[1].split('=')[1].strip('"'))
            trigger_point = str(context_line_number)  + '   ' + context_line.strip()
            args_keys = entry.xpath('.//table[@class="vars"]/tbody/tr/td/text()').getall()
            args_values = entry.xpath('.//table[@class="vars"]//tbody//tr//td[@class="code"]//pre/text()').getall()
            module_args = dict(zip(args_keys,args_values))

            trigger = {
                "Module": module,
                "Function":function,
                "Line trigger":trigger_point
            }
            
            if module == VIEW_PATH:
                LINE_NUMBER = trigger_point.split()[0]
                LINE_TRIGGER = trigger_point

            cs_count = 0
            for l in code_snippet:
                cs_count +=1
                if l.strip() == '<pre></pre>':
                    l=' '
                line = highlight(l, PythonLexer(),TerminalFormatter())
                line = line.strip().replace('<pre>','').replace('</pre>','').replace('\n','')
                l = l.strip().replace('<pre>','').replace('</pre>','').replace('\n','')

                raw_line = (' {}  {}'.format(str(ref_line_number),l))
                hl_line = ('    {}    {}'.format(
                    colored(str(ref_line_number).strip('\n'), 'green', attrs=['bold']),line
                    )
                )
                raw_code_snippets.append(raw_line)
                highlight_code_snippets.append(hl_line)
                ref_line_number +=1

            for key,value in module_args.items():
                if 'object at' in value and \
                        '<django.' in value:

                    obj = value.split()
                    object_mapping = {
                        'variable'  : key.strip(),
                        'object'    : obj[0].replace('<','').strip(),
                        'address'   : obj[3].replace('>','').strip()
                    }
                    TRACEBACK_OBJECTS.append(object_mapping)

            # need to change siddhis/djunch/engines/_dju_utils.py +859 to except_objs[0]['APP_RESPONSE'].text)
            # since we changed APP_RESPONSE to receive the response itself, not just text
            # When other modules start using this resource, it should be changed at _dju_utils as well
            response_headers = {}
            response_headers = {
                k.decode('utf-8'): v[0].decode('utf-8') 
                    for k, v in self.response.headers.items()
            }

            MODULE_TRIGGER_INFO = {
                'APP_RESPONSE': self.response.text,
                'RESPONSE_HEADERS': response_headers,
                'RAW_CODE_SNIPPET': raw_code_snippets,
                'HL_CODE_SNIPPET': highlight_code_snippets,
                'MODULE_ARGS': module_args,
                'MODULE_TRIGGERS': trigger
            }
            
            TRACEBACK_COLLECTOR.append(MODULE_TRIGGER_INFO)

        DUMP = {
            'app_response': self.response.text,
            'summary': SUMMARY,
            'traceback': TRACEBACK_COLLECTOR,
            'view_trigger': {
                'fullpath': VIEW_PATH,
                'shortpath': '.'.join(VIEW_PATH.split('/')[-2:]).replace('.py','') if VIEW_PATH else None,
                'object': VIEW_OBJECT,
                'line_number': LINE_NUMBER,
                'trigger_line': LINE_TRIGGER
            }
        }

        return DUMP
