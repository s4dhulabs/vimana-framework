from neotermcolor import colored,cprint
from tabulate import tabulate
from datetime import datetime
import os,glob
import yaml
import sys


def check_file(file, quiet=False):
    scope_error = colored(' - scope_error - ', 'white', 'on_red', attrs=['bold'])

    if not os.path.exists(file):
        if not quiet:
            print(f"\r{scope_error} File not found: {file}. Check the file location and try again.\n")
        return False

    if not os.path.isfile(file) \
        or not file.endswith('.yaml'):
            
        if not quiet:
            arg_msg=''
            arg_msg = 'Requires a configuration file with .yaml extension\n'
            print(f"\r{scope_error} Invalid YAML file: {file}. {arg_msg}")
        return False

    if os.path.getsize(file) == 0:
        if not quiet:
            print(f"\r{scope_error} The file is empty: {file}\n")
        return False

    return True

def get_tool_scope(**args):
    
    siddhi_args = args
    targets_ports_set = []
    targets = []
    ports = []

    # ignore-state enabled: all targets and ports are going to be tested
    if 'targets' in siddhi_args['scope']:
        
        # get targets
        if siddhi_args['scope']['targets']:
            for target in siddhi_args['scope']['targets']:
                if target not in targets:
                    targets.append(target.strip())
            
        # get ports
        if siddhi_args['scope']['ports']:
            for port in siddhi_args['scope']['ports']:
                if port not in ports:
                    ports.append(port.strip())
        else:
            print(f'[{datetime.now()}] Missing target scope')
            return False

    # ignore-state disabled: port arguments will be tested
    else:
        for k,v in siddhi_args['scope'].items():
            for target in list(v):
                if target not in targets_ports_set:
                    targets_ports_set.append(target.strip())

    # final scope object
    if not targets_ports_set:
        if targets and ports:
            for target in targets:
                for port in ports:
                    targets_ports_set.append(
                        f'{target.strip()}:{port.strip()}'
                    )

    return targets_ports_set

