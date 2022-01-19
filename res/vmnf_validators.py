import os
from termcolor import colored,cprint
from tabulate import tabulate
import yaml
import sys


def update_handler(case_file,handler):
    with open(case_file) as file:
        abd_set = yaml.load(file, Loader=yaml.FullLoader)

        try:
            vars(handler).update(abd_set)
        except TypeError:
            return False

    return handler



def check_saved_exec(file, handler):
    with os.scandir('core/execs/') as saved_execs:
        saved_files = [entry.name for entry in saved_execs if entry.is_file()]

    for entry in saved_files:
        if entry.endswith(file):
            reloaded_handler = update_handler('core/execs/' + entry, handler)
            if not reloaded_handler:
                print('\n[run]→ Malformed file: {}. Check it out and try again.\n'.format(
                    entry
                    )
                )
                sys.exit(1)

            return reloaded_handler

    os.system("clear")
    cprint("\n→ Cases available:\n",'blue')

    print('{:>25}{:>35}{:>47}\n'.format(
        colored('module','white',attrs=['bold']),
        colored('date','white',attrs=['bold']),
        colored('file','white',attrs=['bold'])
        )
    )

    for entry in saved_files:
        entry = entry.split('_')
        module = entry[0]
        date = entry[1]
        time = entry[2].split('.')[0].strip()
        exec_time = date + ' ' + time
        file_name = '_'.join(entry[3:]).split('.')[0]
         

        print('{:>20}{:>40}{:>40}'.format(
            colored(module,'green'),
            colored(exec_time, 'cyan'),
            colored(file_name, 'blue')
            )
        )
    print()
    sys.exit(1)

def check_file(file):
    scope_error = colored(' - scope_error - ', 'white', 'on_red', attrs=['bold'])

    if not os.path.exists(file):
        print('''\r{} File not found: {}. Check the file location and try again.\n'''.format(
            scope_error, file
            )
        )
        return False

    if not os.path.isfile(file) \
        or not file.endswith('.yaml'):
        
        arg_msg=''
        arg_msg = 'Requires a configuration file with .yaml extension\n'
        print('''\r{} Invalid YAML file: {}. {}'''.format(
            scope_error, file, arg_msg
            )
        )
        return False

    if os.path.getsize(file) == 0:
        print('''\r{} The file is empty: {}\n'''.format(
            scope_error, file
            )
        )
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
            print('[{}] Missing target scope'.format(datetime.now()))
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
                    targets_ports_set.append('{}:{}'.format(
                        target.strip(),
                        port.strip()
                        )
                    )

    return targets_ports_set

