#!/usr/bin/env python3
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
#
# This file is part of Vimana Framework Project.


import sys
from time import sleep
from datetime import datetime


if __name__ == '__main__':
    from core.vmnf_engine import abduct
   
    try:
        abduct()
    except (KeyboardInterrupt):
        print("\033[0m")
        print(f'\n[{datetime.now()}] Exiting Vimana framework...\n')
        print('\x1b[0m',end='') 
        sleep(0.30)
        sys.exit(0)
