from time import sleep
from subprocess import run
from datetime import datetime


def get_runner_args(_args_):
    skp = []
    keep = [
        '--exit-on-trigger',
        '--auto',
        '--debug',
        '--verbose',
        '--usernames',
        '--passwords'
    ]
    skip_args = [
        '--docker-scope',
        '--target-list',
        '--save-case',
        '--port-list',
        '--namp-xml',
        '--target',
        '--file',
        '--port'
    ]
    auto_load = [
        '--docker-scope'
    ]

    for index, item in enumerate(_args_):
        if item in skip_args:
            skp.append(item)

            # autoload options such as --docker-scope
            # doesn't take arguments, so the next will
            # not be a related item
            if item in auto_load:
                continue

            nexta = _args_[index+1]

            if nexta not in keep:
                skp.append(_args_[index+1])

    [_args_.remove(arg) for arg in skp]
    
    return _args_

def rudrunner(**session):
    base_handler=get_runner_args(session['args'])

    for task in session['runner_tasks']:
        runner_handler = base_handler[:]
        runner_handler.append("--target-url")
        runner_handler.append(task)
        runner_handler.append("--runner-mode")

        rstt = run(runner_handler)
        # 'check_returncode', 'returncode', 'stderr', 'stdout'
    

