# -*- coding: utf-8 -*-

from . colors import *
from random import choice
from time import sleep
from termcolor import cprint,colored



def audit_report_banner(module=False):
    
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

    #report_type = colored('   Audit Report  ', 'white', 'on_red', attrs=['bold'])
    #mark = colored('█', 'green',attrs=['bold', 'blink'])
    
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

def circuits_banner(proc_type=False):
    proc_type = colored(proc_type, 'red') if proc_type else ''
    banner = colored('''
    ┬  ┬┬┌┬┐┌─┐┌┐┌┌─┐
    └┐┌┘││││├─┤│││├─┤  
     └┘ ┴┴ ┴┴ ┴┘└┘┴ ┴
            {0}
    '''.format(proc_type), 'green', attrs=['blink', 'bold'])

    return banner

def ansi_banner():
    banner = '''
    ██╗   ██╗██╗███╗   ███╗ █████╗ ███╗   ██╗ █████╗
    ██║   ██║██║████╗ ████║██╔══██╗████╗  ██║██╔══██╗
    ██║   ██║██║██╔████╔██║███████║██╔██╗ ██║███████║
    ╚██╗ ██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║
     ╚████╔╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║
      ╚═══╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
    '''
    return banner

def about_text():

    msg='''

      Vimana is an experimental tool that aims to provide resources for
      auditing Python applications (often through vectors and
      unconventional techniques), enabling manual analyzes, automated
      scans and application fuzzing in active mode. In post-analysis
      (passive mode), the framework performs mapping and correlation of
      vulnerabilities related to the identified versions (framework,
      libs, etc.), allowing you to interact with issues and create
      exploitability scenarios where other resources will be triggered.

      The framework is modular, allowing new modules (siddhis) to be
      plugged in to expand the range of available resources, being able
      to support mixed analyzes that start from a black-box approach
      and culminate in a gray-box, increasing the possibilities.

      A lot of code has been written and rewritten, as well as a lot
      left out (for now) since the idea of the tool came about 10
      years ago, however, the framework is still very early and
      considering that until then it was only a sadhu (who is not a
      developer) coding the crazy ideas, certainly a lot needs to be
      improved, as well as many new features can be added (soon).

      So feel free to get in touch, suggest ideas and improvements.
                https://github.com/s4dhul4bs/vimana-framework

                                                s4dhu
    '''

    return msg


def s4dhu0nv1m4n4(vmnf_about=''):
    
    if vmnf_about:
        vmnf_about = about_text()
        
    about=("""                                         

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

    {}
    """.format(vmnf_about))

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
    
    if not mode_uvb:
        print("\033c", end="")
    
    banner = colored('VIMANA FR4MEWORK', 'blue', attrs=['blink'])
    print(r"""{}
        *                       
                   _^_               .
        (( ( ____.´-v-`.____  ))) ){}  *         *  
         {}        `.¨ô¨.´           {}    .
 .   ~|~ {}  .      |^!^|            {}      
         {}           ¨          .   {} -
                 . * .'e .           *
         `*´    .      . xce   .pt      -o-        .
            *               *         io>
            {}
  
    """.format(Rn_c,P_c,Rn_c,Pn_c,Rn_c,P_c,Rn_c,P_c,banner))
    print("\n")

def vmn_progress():
    print("""

      o                    
o   o   o-O-o  oo o-o   oo 
 \ /  | | | | | | |  | | | 
  o   | o o o o-o-o  o o-o-
                            
    """)

def vmn_abduct():
    print("\033c", end="")
    print(r"""{}
      .__                              {}    ___    {}
___  _|__| _____ _____    ____ _____   {}___´_'_`___{}        
\  \/ /  |/     \\__  \  /    \\__  \  {}   ``-´´   {} 
 \   /|  |  Y Y  \/ __ \|   |  \/ __ \_{}    |||    {}
  \_/ |__|__|_|  (____  /___|  (____  /{}    '''    {}
               \/     \/     \/     \/ {}     '     {} 
                   {}Abducting ...{}             
    """.format(Cn_c,Rn_c,Cn_c,Rn_c,Cn_c,Rn_c,Cn_c,Rn_c,Cn_c,Rn_c,Cn_c,Rn_c,Cn_c,Yn_c,D_c))          


def default_vmn_banner1():
    print("\033c", end="")
    print("""{}
      .__                              
___  _|__| _____ _____    ____ _____   
\  \/ /  |/     \\\\__  \  /    \\\\__  \\  
 \   /|  |  Y Y  \/ __ \|   |  \/ __ \_
  \_/ |__|__|_|  (____  /___|  (____  /
               \/     \/     \/     \/{} 
        author: s4dhu
        version alpha
        2017{}\n
    """.format(Y_c,Wn_c,D_c))


def load(target=''):
    import os 
    from random import choice

    colors = [
        ("\033[0m"   ), ("\033[0;30m"), ("\033[0;31m"),
        ("\033[0;32m"), ("\033[0;33m"), ("\033[0;34m"),
        ("\033[0;35m"), ("\033[0;36m"), ("\033[0;37m"),
        ("\033[1;37m"), ("\033[1;30m"), ("\033[1;31m"),
        ("\033[1;32m"), ("\033[1;33m"), ("\033[1;34m"),
	("\033[1;35m"), ("\033[1;36m"), ("\033[1;37m"),
        ("\033[1;37m")
    ]
    c = 0
    while c != 30:
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

