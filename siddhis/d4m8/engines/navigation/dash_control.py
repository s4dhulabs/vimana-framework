
from __future__ import print_function, unicode_literals
from PyInquirer import style_from_dict, Token, prompt, Separator
from PyInquirer import prompt, print_json
#from ..navigation import navigation
#from .dashboard import dashboard
from neotermcolor import colored
from pprint import pprint
import getch
import os


class navigation:
    def __init__(self, *choices):
        self.choices = choices
        
    def dashboard(self):
        key=''
        while key != 27:
            # '\x1b'
            typeQ = [
                {
                    'type' : 'list',
                    'name' : 'type',
                    'message' : 'Duration or Time based?',
                    'choices': self.choices
                }
            ]

            time = [
                {
                    'type' : 'input',
                    'name' : 'time',
                    'message' : 'Specify time:'
                }
            ]
            
            key=ord(getch.getch())
            if key == 27:
                self.options_board()
                break


            typeA = prompt(typeQ)
            if not typeA.get('type'):
                self.options_board()
                break

            '''
            if (typeA == 'time'):
                print('TYPEA:')
                print(typeA)
                print('----')
                #time = prompt(time)
            else:
                continue
            '''
    def options_board(self):
        os.system("clear")
        p1 = colored('debug  fuzz → forms', 'blue')
        p2 = colored('defuse form ← bugs', 'blue')
        version = colored('v1.0', 'red', attrs=[])
        
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

        style = style_from_dict({
            Token.Separator: '#cc5454',
            Token.QuestionMark: '#673ab7 bold',
            Token.Selected: '#cc5454',  # default
            Token.Pointer: '#673ab7 bold',
            Token.Instruction: '',  # default
            Token.Answer: '#f44336 bold',
            Token.Question: '',
        })
    
        space = '                   '
        questions = [
            {
                'type': 'list',
                'message': '',
                'name': 'category',
                'choices': [
                    Separator('\n                        \n'),
                    {
                        'name': space + 'dashboard'
                    },
                    {
                        'name': space + 'rebuild'
                    },
                    {
                        'name': space + 'rawsocket'
                    },
                ],
                'validate': lambda answer: 'You must choose at least one topping.' \
                    if len(answer) == 0 else True
            }
        ]
        
        answers = prompt(questions, style=style)

        if answers['category'].strip() == 'dashboard':
            self.dashboard()
 
