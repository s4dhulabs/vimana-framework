
import getch
from PyInquirer import prompt, print_json
from ..navigation import navigation

def dashboard(*choices):
    key=''
    while key not in [27, 'quit']:
        key=ord(getch.getch())
        if key == 27:
            print('---- ESCAPE ----')
            navigation(*choices)
            
            
        # '\x1b'
        typeQ = [
            {
                'type' : 'list',
                'name' : 'type',
                'message' : 'Duration or Time based?',
                'choices': choices
            }
        ]

        time = [
            {
                'type' : 'input',
                'name' : 'time',
                'message' : 'Specify time:'
            }
        ]

        typeA = prompt(typeQ)

        if (typeA == 'time'):
            time = prompt(time)
        else:
            print('--> Not time')

