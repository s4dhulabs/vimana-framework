'''
    ~===================~
    ~ Vimana ParseScope ~
    ~===================~

    This is a simple module to parse url.py files of Django applications 
    to be used as scope to fuzzer options, when called directly: 

    $ vimana run --fuzzer --scope mydjangoapp/urls.py --target http://www.mydjangoapp.com 

    This works fine in most situations but its not a perfect trick
    so, if you found a bug let me know sending me an email or commit the fix 
    to vimana repository: https://github.com/s4dhulabs/vimana


                    ~ s4dhu
'''

import sys
import re
from time import sleep
from prettytable import PrettyTable
from res import colors



def replace_chars(line, full=False):
    
    line = line.replace(
        '"','' ).replace(
        "'",'' ).replace(
        '$','' ).replace(
        '\\','').replace(
        '={','').replace(
        '^','' )

    if full:
        line = line.replace(
        ']','' ).replace(
        '[','' ).replace(
        '{','' ).replace(
        '}','' ).replace(
        '(','' ).replace(
        ')','' )

    return line


def digest_scope(urls_file_location):
    
    input_file = open(urls_file_location, 'r').readlines()
    urls = urls_file_location.split('/')[-1] 
    full_scope = []
    _patterns_ = []

    u_pattern = re.compile('.*?[url|path]\((.*)\)?', re.I)

    # creates a prettytable to store results
    urls_tbl = PrettyTable()
    urls_tbl.field_names = ['id', 'url pattern', 'view name', 'urlconf'] 
    urls_tbl.align = 'l'
    
    p_count = 1

    print("{} Parsing fuzzer scope via URLconf: {}...\n".format(
        colors.Gn_c + "⠿⠥" + colors.C_c,
        colors.Y_c  + urls + colors.D_c
        )
    )
    sleep(1)

    for line in input_file:
        line = line.strip()
        url_file    = urls + ' *'
        view_name   = '?'
        url_pattern = ''

        pattern_match = re.findall(u_pattern, line)
    
        # ~ if a compiled regex pattern matchs with current line of url file
        if pattern_match:    
            pm = str(pattern_match)

            # ~ get url pattern
            url_pattern = replace_chars(str(pm[pm.find('^') +1 : pm.find(',')]))
            if url_pattern.find('(') != -1:
                url_pattern = url_pattern[:url_pattern.find('(')]
            
            # ~ clean all no not expected chars in url_pattern
            url_pattern = replace_chars(url_pattern, True)

            if not url_pattern or url_pattern == '':
                url_pattern = '?'

            # ~ get included url file 
            if pm.find('include') != -1:
                url_file = pm[pm.find("include(") + 8:]
                url_file = replace_chars(str(url_file[:url_file.find(')') -1]))
            
                # strip url_file when it has more than one value with ','
                if len(url_file.split(',')) >=2:
                    url_file = url_file.split(',')[0]
            
            # ~ get view name (when 'name' is in the line of url_pattern)
            if pm.find('name=') != -1:
                view_name = pm[pm.find("name=") + 6:]
                view_name = replace_chars(str(view_name[: view_name.find(")") -1]))
            else:
                # ~ When view name was not found (doesnt exists or url file has a newline with name of view)
                if url_pattern != '' and url_pattern != '?':
                    
                    # just a copy of values to use in schema bellow
                    _up_ = url_pattern
                    _if_ = str(input_file)
                
                    if _up_.endswith('/'):
                        _up_ = _up_[:-1]

                    view_name = str(_if_[_if_.find(_up_):]).replace(' ','')
                    view_name = view_name[:view_name.find(')')]
                    view_name = replace_chars(str(view_name[view_name.find('name=') + 6:]))
            
                    # if view_name is longest than url_pattern so use url_pattern as view_name
                    if len(view_name) > len(_up_): 
                        view_name = str(_up_).replace('-','_').replace('/','_') + ' *'
                else:
                    url_pattern = '?'
                    view_name = url_pattern

            # ~ strip all not expected characters (full = True)
            view_name   = replace_chars(view_name, True)
            url_file    = replace_chars(url_file, True)
           
            #~ scope object with current URL pattern
            scope = {
                'url_pattern': url_pattern,
                'view_name'  : view_name,
                'url_file'   : url_file
            }
            
            #~ save current object in full_scope list
            if url_pattern not in _patterns_:
                _patterns_.append(url_pattern)
                full_scope.append(scope)
                
                #~ add new entry to prettytable 
                urls_tbl.add_row([p_count, url_pattern, view_name, url_file])
                p_count += 1 
    
   
    # ~ show prettytable with parsed scope
    # ~ this is just to information purpose, the column important to fuzzer is the fist one: 'url_pattern'
    print(urls_tbl)

    return full_scope
