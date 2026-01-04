#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# JColt banner variants with jazzy hacking themes
# Inspired by John Coltrane's improvisational style

from neotermcolor import colored, cprint
import random

def jcbanner_classic():
    """The original JColt banner"""
    return """
            _
         -='-ø'`
              \ \\
               ø JCølt
              .ø |.---,
              :ø ||  |
               \ ~   |
                '._.'
                VimanaFramework v1.0
                        @s4dhulabs
    """

def jcbanner_saxophone():
    """Saxophone-themed banner"""
    return """
             .--.
           .'    `.      JC⚡lt
          /   .-"'-\\     API Security
         .   /      \\ 
         |  /        ;  The Blue Train
         |  |        |  of API Exploitation
         .'`'``'``'``'._
         _____________   @s4dhulabs
        / / /    \\_\\  \\  VimanaFramework v1.0
       / / // /\\ \\\\ \\ \\
      / / // /  \\ \\\\ \\ \\
     / / // / __ \\ \\\\ \\ \\
    / / //  \\_  /  \\\\ \\ \\
   / / //    --    \\\\ \\ \\
  / / //            \\\\ \\ \\
 / / //              \\\\ \\ \\
/./_//                \\\\_.\\\\
    """

def jcbanner_hackjazz():
    """Minimal hacker-jazz fusion banner"""
    return """
      _______               __  __
     /  _____|       .---. \\ \\/ /
     | |            / .-. \\ \\  /
     | |       .--.| |   | |/  \\
    _| |____  ( () ) |   | / /\\ \\    The jazz of API
   /________\\  `--'  \\_.' /_/  \\_\\   exploitation
                            
   4  |\\  |  4|3|1
   0  | \\ |  1|1|1  < VimanaFramework >
   4  |  \\|  3|2|0  < @s4dhulabs >
    """

def jcbanner_improvisational():
    """Improvisational hacking banner"""
    return """
     .~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
     |    ___     ___      _      _____   |
     |   |_  |   / __|    / \\    |_   _|  |
     |    _| |  | /      / _ \\     | |    |
     |   |___/  | \\__   / ___ \\    | |    |
     |          \\____| /_/   \\_\\   |_|    |
     |                                    |
     |   ≈≈≈ Improvise. Exploit. ≈≈≈      |
     |   ≈≈≈ Like Coltrane. ≈≈≈           |
     |                                    |
     '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
                Vimana Framework v1.0
                      @s4dhulabs
    """

def jcbanner_vinyl():
    """Vinyl record-themed banner with hacking elements"""
    return """
          _.--._  _.--.
       .-'      `'      '-.
     ,'                    `.
    ;    JC⚡lt                :
   ;                          ;
   |      .---.                |
   |     /     \\               |
   ;    |  0  |               ;
    ;    \\     /              ;
     `.   `---'              .'
       _`-._              _.-'_
        "-.._          _..-"  
             `""-----------"'

       < FastAPI Security Testing >
      Improvised API Exploitation
        VimanaFramework v1.0
              @s4dhulabs
    """

def jcbanner_circuit():
    """Circuit-themed banner with jazz notes"""
    return """
     ♪ .-'--.--.--.--.--.--.-'-. ♫
     ♩ |  J--C--0--l--t  | ♪
     ♫ |  |  |  |  |  |  |  |  | ♩
     ♪ |--|--|--|--|--|--|--|--| ♫
     ♫ |S__|E__|C__|U__|R__|I__|T__|Y__| ♩
     ♩ |--|--|--|--|--|--|--|--| ♫
     ♪ |__|__|__|__|__|__|__|__| ♪
       
       Exploiting APIs with the rhythm of jazz
       and the precision of code
                 
           VimanaFramework v1.0
                @s4dhulabs
    """

def jcbanner_shell():
    """CLI shell-themed banner with jazz theme"""
    return """
     ┌─────────────────────────────────────┐
     │ root@jcolt:~# ./exploit_api.sh      │
     │ Loading JColt Module...             │
     │ Initializing API Security Test...   │
     │ [+] FastAPI vulnerabilities detected │
     │ [+] Serialization exploits ready     │
     │ [+] Jazz-mode exploitation: ENABLED  │
     │                                     │
     │ Improvising through API security     │
     │ like Coltrane on a saxophone...     │
     └─────────────────────────────────────┘
              VimanaFramework v1.0
                    @s4dhulabs
    """

def get_random_banner():
    """Returns a randomly selected banner"""
    banner_functions = [
        jcbanner_classic,
        jcbanner_saxophone,
        jcbanner_hackjazz,
        jcbanner_improvisational,
        jcbanner_vinyl,
        jcbanner_circuit,
        jcbanner_shell
    ]
    
    return random.choice(banner_functions)()

# Dictionary of available banners for direct selection
jcolt_banners = {
    'classic': jcbanner_classic,
    'saxophone': jcbanner_saxophone,
    'hackjazz': jcbanner_hackjazz,
    'improv': jcbanner_improvisational,
    'vinyl': jcbanner_vinyl,
    'circuit': jcbanner_circuit,
    'shell': jcbanner_shell,
    'random': get_random_banner
}

def print_banner(style='classic'):
    """Print a banner based on the style name"""
    if style in jcolt_banners:
        print(jcolt_banners[style]())
    else:
        print(jcolt_banners['classic']())

if __name__ == "__main__":
    # Display all banners when run directly
    for name, banner_func in jcolt_banners.items():
        if name != 'random':
            print(f"\n=== {name.upper()} BANNER ===")
            print(banner_func())