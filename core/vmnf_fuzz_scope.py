import os
import sys
import pathlib
from time import sleep
from pathlib import Path
from core.vmnf_scope_parser import ScopeParser
from core.vmnf_urls_parser import digest_scope
from siddhis.dmt.dmt import siddhi as dmt_siddhi
from siddhis.djunch.djunch import siddhi as Djunch
from res import vmnf_banners
from res.vmnf_validators import get_tool_scope



def handle_fuzz_scope(**fuzz_ns):
    
    # fuzz banner
    print(vmnf_banners.circuits_banner('fuzzer'))
    
    view_name = '*'
    views = []
    patterns = []

    for k,v in fuzz_ns.items():
        if v:
            print(' + {}: {}'.format(k,v))
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
        print('[fuzzer_scope] scope file not found: {}\n'.format(scope_location))
        sys.exit(1)
    elif not os.path.isfile(scope_location):
        print('[fuzzer_scope] It does not appear to be a valid file: {}\n'.format(scope_location))
        sys.exit(1)

    # check if a valid scope file was given
    if arg_type == 'django_urls' \
        and not scope_file.split('.')[1] == 'py':
        print('''
        \r[fuzz_scope] Error: {} argument requires a {} file.
        \rexample: vimana run --fuzzer --target http://mydjpyapp.com --port 8000 --urls-file urls.py
        '''.format(argument, scope_type))
        sys.exit(1)

    elif arg_type == 'django_patterns' \
        and scope_file.split('.')[1] == 'py':
        print('''
        \r[fuzzer_scope] Error: {} argument requires a {} file.
        \rexample: vimana run --fuzzer --target http://mydjpyapp.com --port 8000 --patterns patterns.txt
        '''.format(argument, scope_type))
        sys.exit(1)

    # check if a empty file
    if Path(scope_location).stat().st_size == 0:
        print('[fuzzer_scope] Error: Scope file is empty: {}\n'.format(scope_location))
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
        'patterns'  : patterns
    }

    for k,v in _scope_.items():
        if k != 'patterns':
            print('|+| {}:\t{}'.format(k,v))
            sleep(0.25)
    sleep(1)

    confirmation = False
    while not confirmation:
        confirmation = input('''\nWere detected {} input URL Patterns, continue? (Y/n) > '''.format(
                (_scope_['scope_size'])
            )
        )
        print()

        if confirmation.lower() == 'y':
            expanded_patterns,xlp_tbl_x = dmt_siddhi(**fuzz_ns).expand_UP(_scope_['patterns'])
            
            fuzz_ns['scope'] = ScopeParser(**fuzz_ns).parse_scope()
            targets_ports_set = get_tool_scope(**fuzz_ns)
            
            for entry in targets_ports_set:
                fuzz_ns['target_url']= 'http://' + entry
                fuzz_ns['patterns']= expanded_patterns
                fuzz_ns['patterns_table']= xlp_tbl_x
                fuzz_ns['patterns_views']=False
                fuzz_ns['module_run']= 'djunch'
                fuzz_result=Djunch(**fuzz_ns).start()





