from res.vmnf_banners import case_header,mdtt1,vmn05
from pygments.formatters import TerminalFormatter
from pygments.lexers import PythonLexer
from pygments import highlight
from neotermcolor import cprint
from random import choice
from time import sleep






def abduct_items(**session):
    lights = [
        '││├˖┤', '│|│|│',
        ' |│|│', '└┐┌┘│',
        '││˖│ ', '│˖│.│',
        '├˖├˖┤'
    ]

    for k,v in session.items():
        print("\033c", end="")
        vmn05()

        _r_ = 15
        _l_ = True

        if isinstance(v,dict):
            _r_ = 4
        elif isinstance(v,list):
            _r_ = 6
        elif isinstance(v,tuple):
            _r_ = 5
        elif isinstance(v,str):
            _l_ = False
            _r_ = 2
        elif isinstance(v,int):
            _l_ = False
            _r_ = 7
        else:
            _l_ = False

        [cprint(f'{choice(lights):>24}', 'green', attrs=['blink','bold'])\
            for _ in range(_r_)
            ]

        if not _l_:
            print('\n\t\t' + highlight(str(k) + ' -|- ' +  str(v)[:500],PythonLexer(),TerminalFormatter()).strip())
            sleep(0.05)
            continue

        cprint(f"\n\t\t{str(k).upper()} ↓↓↓\n", 'red')

        try:
            for c,obj in enumerate(v[:20]):
                print('\t\t → ' + highlight(str(obj),PythonLexer(),TerminalFormatter()).strip())
                sleep(0.01)
            sleep(0.07)
        except TypeError:
            pass

    print("\033c", end="")
    vmn05()
    print('\n\n')

    return f'<abddone={c}:{obj}>'
    

