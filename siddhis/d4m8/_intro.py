from neotermcolor import cprint,colored as cl
from time import sleep
import os


p1 = cl('debug  fuzz → forms', 'blue')
p2 = cl('defuse form ← bugs', 'blue')
version = cl('v1.0', 'red', attrs=[])

def final_banner():
    os.system("clear")
    print(f'''

                       D 3 ↓ B U G D 3
                     \\ 3           \\ 3
                   DD33F↓BBUUGGDD33  F
                  \\33  U        \\33  U
                D 3FF BSU G D 3  FF  S                  {version}
                3  UU  3      3  UU  3    ___     _   _      ___
                F  SS  D      F  SS  D   | | \ /_| | | |\/| ( (_)
                U  33  3      U  33  3   |_|_/   |_| |_|  | (_(_)
                S  DD  D 3 ↓ BSU GDD 3
                3  33\\        3  33\\     {p1}
                D  DD33↓↓BBUUGGDD33      {p2}
                3 \\           3 \\
                D 3 ↓ B U G D 3



    ''')


def default():
    h1 = cl("DD33F↓BBUUGGDD33", "green")
    h2 = cl("DD33↓↓BBUUGGDD33", "green")
    c2 = cl("D 3FF BSU G D 3", "blue")
    c3 = cl("D 3 ↓ B U G D 3", "blue")

    os.system("clear")
    print(f"""

                       D 3 ↓ B U G D 3
                     \\ 3           \\ 3    
                   {h1}  F          
                  \\33  U        \\33  U        
                {c2}  FF  S                  {version}
                3  UU  3      3  UU  3    ___     _   _      ___       
                F  SS  D      F  SS  D   | | \ /_| | | |\/| ( (_)  
                U  33  3      U  33  3   |_|_/   |_| |_|  | (_(_)  
                S  DD  D 3 ↓ BSU GDD 3   
                3  33\\        3  33\\     {p1}
                D  {h2}      {p2}
                3 \\           3 \\
                {c3}


            
    """)

    sleep(0.20)
    final_banner()

