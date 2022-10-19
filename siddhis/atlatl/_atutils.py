


def load():
    s='➳ ➵'
    print('\n\n')

    for c in range(15):
        shot = '''\t   ➴  ➶ ➷➹'''*c + s * c
        print("\033c", end="")
        cprint(shot,choice(
            ['red','blue','white','yellow','magenta','cyan']),
            attrs=['blink','bold']
        )
        print()
        sleep(0.05)

    print("\033c", end="")
    cprint("""

             _|      _|              _|      _|
   _|_|_|  _|_|_|_|  ➵|    _|_|➵|  _|_|_|_|  _| ➵
 ➵|    _|    _|      _|  _|    ➵|    _|      ➵|  ➵
 _|    _|    _|      _|  _|    ➵|    ➵|      _|     ➵ ➵
   _|_|➵|      _|➵|  _|    _|_|➵|      _|_|  _|


        """,'blue',attrs=['bold']
    )

