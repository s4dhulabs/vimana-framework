import os
from datetime import datetime
from res.vmnf_banners import case_header
from neotermcolor import cprint,colored as cl

def get_elapsed_time(entry):
    scan_date = entry.scan_date
    time_diff = datetime.now() - entry.scan_date
    hour_ = 'hour'
    minute_ = 'minute'
    day_ = 'day'

    if time_diff.days > 1:
        time_ = time_diff.days
        if time_ > 1:
            day_ += 's'
        exec_ = f'{time_} {day_} ago'
    elif time_diff.days == 1:
        exec_ = 'Yesterday'
    elif time_diff.seconds >= 3600:
        time_ = time_diff.seconds // 3600
        if time_ > 1:
            hour_ += 's'
        exec_ = f'{time_} {hour_} ago'
    elif time_diff.seconds >= 60:
        time_ = time_diff.seconds // 60
        if time_ > 1:
            minute_ += 's'
        exec_ = f'{time_} {minute_} ago'
    else:
        exec_ = 'Just now'

    return exec_

def get_filter_clauses(model,filters):
    return [getattr(model, f['field']).__getattribute__(filter_ops[f['op']])(f['value']) for f in filters]

def handle_OpErr(exception):
    case_header()
    if exception.startswith('no such table:'):
        print()
        cprint(f"        You haven't populated the database yet. Please run the following to fix it:", 'cyan')
        cprint("         vimana load --plugins", 'green', attrs=['bold'])
        print()
    elif exception.startswith('db ready'):
        cprint("        Plugins already loaded. Try vimana list --plugins \n", 'yellow')

    os._exit(os.EX_OK)

filter_ops = {
    '==': '__eq__',
    '!=': '__ne__',
    '>': '__gt__',
    '<': '__lt__',
    '>=': '__ge__',
    '<=': '__le__'
}

