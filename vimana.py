#!/usr/bin/env python3

import sys
from time import sleep
from datetime import datetime


if __name__ == '__main__':
    from core.vmnf_engine import abduct
   
    try:
        abduct()
    except KeyboardInterrupt:
        print('\n[{}] Exiting vimana framework...\n'.format(
            datetime.now()
            )
        )
        sleep(1)
        sys.exit(1)
