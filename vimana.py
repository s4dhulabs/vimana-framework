#!/usr/bin/env python3

import sys
from time import sleep
from datetime import datetime


if __name__ == '__main__':
    from core.vmnf_engine import abduct
   
    try:
        abduct()
    except KeyboardInterrupt:
        print("\033[0m")
        print(f'\n[{datetime.now()}] Exiting Vimana framework...\n')
        
        sleep(1)
        sys.exit(0)
