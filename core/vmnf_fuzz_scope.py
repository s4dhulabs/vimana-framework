import os
import sys
import pathlib
from time import sleep
from pathlib import Path
from res import vmnf_banners
from res.vmnf_validators import get_tool_scope
from core.vmnf_scope_parser import ScopeParser
from core.vmnf_urls_parser import digest_scope
#from siddhis.dmt.dmt import siddhi as dmt_siddhi
from siddhis.djunch.djunch import siddhi as Djunch
from siddhis.dmt.engines._dmt_parser import DMTEngine




def handle_fuzz_scope(**fuzz_ns):
    
    # fuzz banner
    print(vmnf_banners.circuits_banner('fuzzer'))
    
    view_name = '*'
    views = []
    patterns = []

    for k,v in fuzz_ns.items():
        if v:
            print(f' + {k}: {v}')
    print()

    location = str(pathlib.Path().absolute())

    # check if a file argument was informed to fuzzer
    if fuzz_ns['url_conf']:
        scope_type  = 'Django urls'
        scope_file  = fuzz_ns['url_conf']
        arg_type    = 'django_urls'
        argument    = '--urlconf'

    elif fuzz_ns['patterns_file']:
        scope_type  = 'Django URL patterns'
        scope_file  = fuzz_ns['patterns_file']
        arg_type    = 'django_patterns'
        argument    = '--patterns'

    else:
        print("[fuzzer_scope] Error: Missing scope file")
        sys.exit(1)

    scope_location = location + '/' + scope_file
    
    # check if a scope file exists
    if not os.path.exists(scope_location):
        print(f'[fuzzer_scope] scope file not found: {scope_location}\n')
        sys.exit(1)
    elif not os.path.isfile(scope_location):
        print(f'[fuzzer_scope] It does not appear to be a valid file: {scope_location}\n')
        sys.exit(1)

    # check if a valid scope file was given
    if arg_type == 'django_urls' \
        and not scope_file.split('.')[1] == 'py':
        
        print(f'''
        \r[fuzz_scope] Error: {argument} argument requires a {scope_type} file.
        \rexample: vimana run --fuzzer --target http://mydjpyapp.com --port 8000 --urls-file urls.py''')

        sys.exit(1)

    elif arg_type == 'django_patterns' \
        and scope_file.split('.')[1] == 'py':
        print(f'''
        \r[fuzzer_scope] Error: {argument} argument requires a {scope_type} file.
        \rexample: vimana run --fuzzer --target http://mydjpyapp.com --port 8000 --patterns patterns.txt''')

        sys.exit(1)

    # check if a empty file
    if Path(scope_location).stat().st_size == 0:
        print(f'[fuzzer_scope] Error: Scope file is empty: {scope_location}\n')

        sys.exit(1)
    
    if arg_type == 'django_urls':
        fuzz_scope = digest_scope(scope_location)
    else:
        fuzz_scope = open(scope_location).readlines()

    # parse patterns in full_scope
    # if view name was specified in arguments to filter url patterns
    if fuzz_ns['view_name']:
        view_name = fuzz_ns['view_name']
        for pattern in fuzz_scope:
            if pattern['view_name'].lower() == fuzz_ns['view_name']:
                patterns.append(pattern['url_pattern'])
    else:
        for pattern in fuzz_scope:
            patterns.append(pattern['url_pattern'])

    _scope_ = {
        'location'  : scope_location,
        'scope_type': scope_type,
        'scope_size': len(patterns),
        'view_name' : view_name,
        'arg_type'  : arg_type,
        'argument'  : argument,
        'fuzz_patterns'  : patterns,
    }



    for k,v in _scope_.items():
        if k != 'fuzz_patterns':
            print('|+| {}:\t{}'.format(k,v))
            sleep(0.25)
    sleep(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0',
        'Referer': fuzz_ns.get('target_url'),
        'Origin': fuzz_ns.get('target_url'),
        'Upgrade-Insecure-Requests': '1'
    }

    fuzz_ns.update(**_scope_)
    fuzz_ns.update(**headers)

    confirmation = False
    while not confirmation:
        confirmation = input(f'''\nWere detected {_scope_['scope_size']} input URL Patterns, continue? (Y/n) > ''')

        print()

        if confirmation.lower() == 'y':
            '''
            try:
                requests.get(self.target_url)
            except requests.exceptions.ConnectionError:
                self.target_url = 'https://' + entry

            '''


            fuzz_ns['scope'] = ScopeParser(**fuzz_ns).parse_scope()
            targets_ports_set = get_tool_scope(**fuzz_ns)
            
            for entry in targets_ports_set:
                fuzz_ns['target_url']= 'http://' + entry
                expatterns = DMTEngine(**fuzz_ns).patterns_mapper(True)

                fuzz_ns['patterns']= expatterns
                x = Djunch(**fuzz_ns).start()
                break

                '''
                fuzz_ns['patterns']= expatterns
                fuzz_ns['patterns_table']= xlp_tbl_x
                fuzz_ns['patterns_views']=False
                fuzz_ns['module_run']= 'djunch'

                fuzz_result=Djunch(**fuzz_ns).start()
                '''




