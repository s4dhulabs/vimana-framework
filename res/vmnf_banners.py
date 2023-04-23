# -*- coding: utf-8 -*-
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

import os
from . colors import *
import random
from time import sleep
from random import choice
from neotermcolor import cprint,colored
from core.load_settings import _version_


def circuits_banner(proc_type=False):
    proc_type = colored(proc_type, 'red') if proc_type else ''
    banner = colored('''
    ┬  ┬┬┌┬┐┌─┐┌┐┌┌─┐
    └┐┌┘││││├─┤│││├─┤
     └┘ ┴┴ ┴┴ ┴┘└┘┴ ┴
            {0}
    '''.format(proc_type), 'green', attrs=['blink', 'bold'])

    return banner

def vmn07(): 

    print("\033c", end="")

    cosmo = """˙                    ٭       ⠛          .    ˖
              .             :. *                    ,

      ٭                ٭   ˖ . :  .         ⠛
                         .               '          ٭
        ⣄   ٭   .'   ˖     ~            - ˖ -
       ٭            ˖ ˖         ˖ *     '
         ⣄      ˖       ˖                           ,
                            ⠛
                                        ⠛
    """

    print(msg)

def vmn05(): 

    print("\033c", end="")
    msg = f'''{G_c} ˙              ٭                   .    ˖
              .             :. *
                :  └┐'┌┘          . :  .
                └┐// ' \\\┌┘
        ¨⣠⠛⠛⠛⠛⠛---=======---⠛⠛⠛⠛⠛⣄      .'
       .::::__\├ ┤/⠛⠛⣄⣇⣷\├ ┤/__::::.
               '-'\_____/'-' {R_c + _version_ + G_c}         ⣄
               :: '│.│.│' .{D_c}'''

    print(msg)

def create_status(case_name):
        msg = ("""
                  |
           .     -O-
.                 |

        __'__'__    {}
          ``´´

        """.format('Case {} successfully created'.format(
                colored(case_name, 'red')
                )
            )
        )
        print(msg.ljust(os.get_terminal_size().columns - 1), end="\r")

def case_header():
        print("\033c", end="")
        print()
        cprint("""       *              `'´    *
                    {}          ˙   ٭.    ˖     
                      __'__'__         ,
             ˖          `''´ {}  ˙              ٭   .    ˖
            -o-
             '          .*       o       .       *
        o   ˖     |
           .     -O-            `ç´    
.                 |        *     '  .     -0-
       *  o     .    '       *      .        
       ˖                ˖
       \n\n""".format(G_c, b_c),'blue')


def sample_mode(mod_stat,_attrs_=['bold','blink']):
    c = ['green','cyan','blue']

    vmn=colored("""
         └┐┌┘││
         │││├─┤
         └┐┌┘││
          ││││       
    """, 'blue', attrs=['blink', 'bold'])
    
    fversion = colored(_version_, 'red')

    banner = '''
    ┬  ┬┬┌┬┐┌─┐┌┐┌┌─┐
    ┬  ┬┬┌┬┐┌─┐┌┐┌┌─┐
    └┐┌┘││││├─┤│││├─┤{}
    └┐┌┘││││├─┤│││├─┤
    └┐┌┘││││├─┤│││├─┤
     └┘ ┴┴ ┴┴ ┴┘└┘┴ ┴
     └┘ ┴┴ ┴┴ ┴┘└┘┴ ┴'''.format(fversion)
       
    for i in banner.split('\n'):
        cprint(i,choice(c), attrs=[choice(['bold','dark'])])
    print('     '+ mod_stat)

    if 'sample' in mod_stat or 'caught' in mod_stat:
        [cprint(i,choice(c),attrs=_attrs_) for i in vmn.split('\n')]
    
def audit_report_banner(module='', report_type='',cl=Wn_c):
    vmc = Rn_c
    bmc = Wn_c
    m_color = 'green'
    report_type = '   Audit Report  '
    r_attrs = ['bold', 'blink']

    if not module:
        vmc = b_c
        #bmc = bn_c 
        r_attrs=[]
        m_color = 'blue'
        report_type = ''
        module = ''

    module = colored(module, 'blue', attrs=['bold'])

    report_type = colored(report_type, 'white', 'on_red', attrs=['bold'])
    mark = colored('█', m_color,attrs=r_attrs)
    print(r"""
    
    {}    ___    {}  {}
    {}___´_'_`___{}  ┬  ┬┬┌┬┐┌─┐┌┐┌┌─┐        
    {}   ``-´´   {}  └┐┌┘││││├─┤│││├─┤
    {}    |||    {}   └┘ ┴┴ ┴┴ ┴┘└┘┴ ┴
    {}    '''    {}  {}
    {}     '     {}         {}
    """.format(
            vmc,bmc, mark,
            vmc,bmc,
            vmc,bmc,
            vmc,bmc,
            vmc,bmc,
            report_type,
            vmc,D_c,
            module
        )
    )

def about_text():
    msg='''
      Vimana is an experimental tool that aims to provide
      resources for auditing Python applications (often
      through vectors and unconventional techniques),
      enabling manual analyzes, automated scans and
      application fuzzing in active mode. In post-analysis
      (passive mode), the framework performs mapping
      and correlation of vulnerabilities related to the
      identified versions (framework, libs, etc.), allowing
      you to interact with issues and create exploitability
      scenarios where other resources will be triggered.

      The framework is modular, allowing new modules
      (siddhis) to be plugged in to expand the range of
      available resources, being able to support mixed
      analyzes that start from a black-box approach
      and culminate in a gray box, increasing the
      possibilities.

      https://github.com/s4dhulabs/vimana-framework
                                        s4dhu

    '''
    
    return msg

def s4dhu0nv1m4n4(vmnf_about=''):
    
    if vmnf_about:
        vmnf_about = about_text()
        
    about=f"""                                         

                        (((          )))    )   
                              ⠚⠶⠶                        
         ⠗                     ⠶'                 ⠶    )     
                            ⠖ ¨ħ¨ "             '⠚⠶⠶
                     ''   ,|"       "-.         /¬⠶'
                    ⠼⠉   ⠖           "  ~ -    /¬⠶'            '  /
                   ⠚⠶⠶  ⠦     ___     \\ ~. ~ ~/¬⠶'          ` \|/ ´
                    þ| ⠖   __' ł '__   \\-~   /¬⠶'            --⠚ - - -
                    ||⠖     ' ø æ '     \\   /¬⠶'              ´'` `
                    |⠖       \ ̉̉- /       \\ /¬⠶'             ´  ' `  `
                    ⠖         |=|         \\¬⠶'  
                   ⠖  -ø-  .--"-"--.   *   \\⠚⠶⠶
                  ⠖    I  / -\ Ŋ /- \  I    \\..⠚⠶⠶...  . .,,,, ---
  --⠦⠖------------(    (']y/'  ↓    '\[_)    )⠼⠁⠚⠚ ⠉⠍------- -.~ - ⠶ ⠶ - - 
     -----⠐⠜- -   " .___ł\/__\____/__\/ł___," -----⠼⠚-- --~  --   -) ) ' -
        ~  ~ ⠖-  '̣˙~         ((æ))        ⠚⠶⠶; .'-.- -⠼⠙⠼⠚⠚⠶⠶ ´ -
          ' ~~⠖⠖''|||||||ħ||⠖ ⠠⠤ ||||| |⠜| ~~ -- -⠼⠙⠼⠚⠚⠶⠶ -- 
          -  ..--  ø→æø/→?|⠐⠜⠐⠜|'øþ⠴/ø¹|²¹²⠶--- .~ ⠐⠜ ⠚⠶⠶ 
              ----⠐⠜⠐⠜ħŧŧþ˙̣˙˙˙Ææ˙˙˙˙˙'˙| '----~ --
                      ⠇⠇|||˙˙̣̣⠐⠜opŁŁ»»«| |⠇⠇--- ~       ⠶
                     ''   ,,,,"⠴|Lł  →→Ŧ'-
                      'ŋ "l⠚⠶⠶ |||³"" '|
                         '↓  æ |'ŦŦŦ⠼⠙' '~                      )) 
                          ~⠼⠋⠶ ⠼⠁⠚⠶⠶~
                           ⠼⠑⠽⠛:ŧ⠥⠥*
                             ⠇⠇⠇⠇⠇⠼⠙
                              ⠼⠉⠼⠶


                    ⠶    VIMANA FRAMEWORK α   ⠶
                          s4dhulabs 2020
            
                              
                                ⠶

    {vmnf_about}
    """
    return about

def load_viwec():
    print("\033c", end="")
    print("""{}
      .   .   .
    . ^ . ^ . ^ .     
  _/|\_/|\_/|\_/|\_   
 / \./ \./ \./ \./ \  {}vimana{}
(-{}V{}-|-{}1{}-|-{}W{}-|-{}3{}-|-{}C{}-) {}web{}
 \_/.\_/.\_/.\_/.\_/  {}crawler{}
   \|/*\|/*\|/*\|/
    .   .   .   .
       
  {}\n

    """.format(Rn_c, Wn_c, Rn_c,
        Yn_c, Rn_c, Yn_c,
        Rn_c, Yn_c, Rn_c,
        Yn_c, Rn_c, Yn_c,
        Rn_c, Wn_c, Rn_c,
        Wn_c, Rn_c,D_c ))
    sleep(1)

def default_vmn_banner(mode_uvb = False):
    from core.vmnf_smng import VFManager as vfmng
    from core.vmnf_payloads import VMNFPayloads
    payloads = VMNFPayloads()._vmnfp_payload_types_(True,False)

    if not mode_uvb:
        print("\033c", end="")
    
    hl_V = colored('''\r
            _ _              
            \\\\/''', 'green', attrs=['bold'])
    hl_F = colored('''\r
            [|-''','green', attrs=['bold'])

    banner=colored(f'''\r      
            {hl_V}imana {colored(_version_, 'red')} {hl_F}ramewørk ''', 'blue')            

    print(f"""
        *         ⠛                     ⠛ 
                   _^_               .
        (( ( ____.´└┘┐`.____  )) ) )  *         *  
                 `.⠞⠓⠎.´               .
                  |││||
                  
                    ¨          .    -
                 . * .'e .           *
         `*´    .      . xce   .pt      -o-        .
            *               *         io>
            {banner}
    """)

    vfmng(**{}).get_siddhis_stats()

def load(target='',maxl=20):
    import os 
    from random import choice

    colors = [
        ("\033[0m"   ), ("\033[0;30m"), ("\033[0;31m"),
        ("\033[0;32m"), ("\033[0;33m"), ("\033[0;34m"),
        ("\033[0;35m"), ("\033[0;36m"), ("\033[0;37m"),
        ("\033[1;37m"), ("\033[1;30m"), ("\033[1;31m"),
        ("\033[1;32m"), ("\033[1;33m"), ("\033[1;34m"),
	("\033[1;35m"), ("\033[1;36m"), ("\033[1;37m"),
        ("\033[1;37m"), ("\033[0m"   ), ("\033[1;30m")
    ]
    c = 0
    while c != maxl:
        c1 = choice(colors)
        c2 = choice(colors)
        c3 = choice(colors)
        c4 = choice(colors)
        c5 = choice(colors)
        c6 = choice(colors)
        c7 = choice(colors)
        c8 = choice(colors)
        c9 = choice(colors)
        d1 = choice(colors)
        d2 = choice(colors)
        d3 = choice(colors)
        d4 = choice(colors)
        d5 = choice(colors)
        d6 = choice(colors)
        d7 = choice(colors)
        d8 = choice(colors)
        d9 = choice(colors) 

        print("\033c", end="")
        print(r"""{}
        *                        {}~{}|{}~{}
                   _^_               .
        (( ( ____.´-v-`.____  ))) ){}  *         {}*  
         {}        `.¨ô¨.´           {}    .
 .   ~|~ {}  .      |^!^|            {}     {} 
         {}           ¨          .   {} -
                 . * .'e .           *
         `*´    .      . {}xce{}   .pt      -o-        .
            *               *         io>
             {}  abducting {}{}...        
   

        """.format(
            c1 , c2, c3, c4, c5, 
            c6, c7, c8, c9, d1, d2, 
            d3, d4, d5, d6, d7, d8, 
            d9, target
            )
        )
        sleep(0.10)
        c += 1

def mdtt1(cl='blue',attrs=[]):
    ey=colored('-', 'green', attrs=['blink'])
    print(f"""
                      ({ey}_{ey})      
                ٭     _| |_         
                     /__/  \            
                   _(<_   / )_          
                  (__\_\_|_/__)        

                 {colored('vimanaframework', 'green', attrs=['dark'])}
                 {colored('@s4dhulabs', 'blue', attrs=['dark'])} {colored(_version_, 'green', attrs=['dark'])}

    """)

