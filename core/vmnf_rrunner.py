from time import sleep
from subprocess import run
from datetime import datetime

'''
def rudrunner(session):
    exec_mode = 'sample --xscope\n' \
        if session.sample \
            else 'debug --auto\n'

    try:
        [run(f"{session.runner}\
            --module {session.module_run} \
            --target-url {task} \
            --runner-mode \
            --search-issues\
            --{exec_mode}".split()
            ) for task \
                in session.runner_tasks
        ]
    except KeyboardInterrupt:
        print(f'[{datetime.now()}]Canceling runner task...')
        pass
'''


def get_runner_args(_args_):
    skip_args = [
        '--target-list',
        '--port-list',
        '--target',
        '--file',
        '--port'
    ]

    skp = []
    for index, item in enumerate(_args_):
        if item in skip_args:
            skp.append(item)
            skp.append(_args_[index+1])

    [_args_.remove(arg) for arg in skp]
    return _args_

def rudrunner(session):
    base_handler=get_runner_args(session.args)

    for task in session.runner_tasks:
        runner_handler = base_handler[:]
        runner_handler.append("--target-url")
        runner_handler.append(task)
        runner_handler.append("--runner-mode")
        #print(f"=== running handler {runner_handler}")
        run(runner_handler)


