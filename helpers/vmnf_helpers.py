# encoding=utf8

from res.colors import *
from res.vmnf_banners import s4dhu0nv1m4n4,vmn05
from neotermcolor import colored, cprint
from core.load_settings import _version_


class VimanaHelp():
    '''
           .__
    ___  _|__| _____ _____    ____ _____
    \  \\/ /  |/     \\\\__  \\  /    \\\\__  \\
     \   /|  |  Y Y  \\/ __ \\|   |  \\/ __ \\_
      \_/ |__|__|_|__(____  /___|  (____  /
                         \\/      \\/     \\/   
        @s4dhulabs           {}
        
    '''

    def __init__(self):
        '''@'''

    def overview(self):
        ovw = {
            'about' : "About the framework",
            'args'  : "Show module arguments",
            'info'  : "Show information about modules",
            'list'  : "List available modules",
            'run'   : "Run a specific module or case directly",
            'start' : "Start Vimana in a interactive mode",
        }
        
        print()
        print()

        for cmd, desc in ovw.items():
            print('{:>22}  \t  {}'.format(
                colored(cmd, 'green'),
                colored(desc, 'white')
                )
            )
        print()
        print()

    def proxy(self):
        '''
        [proxy] 

        --set-proxy         Enable the default proxy for all requests: SOCKS5://127.0.0.1:9050
        --proxy             Configure the proxy specified by the ip:port string 
        --proxy-type        Specify the proxy protocol to be used: SOCKS4, SOCKS5, HTTP (required --proxy option)
        '''

    def about(self):
        s4dhu0nv1m4n4()

    def set_scope(self):
        '''

    [target settings]

    Options bellow are used to set target scope: 

        --target             Single target IP/URL of Django application  
        --file               File with a list of IPs/URLs to check Django 
        --ip-range           Range of target IPs to check Django 
        --cidr-range         CIDR range of targets to check Django
        --target-list        List of targets (comma-separated)
       
    [port settings]

    Options to set port scope to test targets:

        --port               Port where Django is running 
        --port-list          List of ports to check Django 
        --port-range         Port range to check Django         
        --ignore-state       Disable IP and port status verifications 
        '''

    def save_case(self):
        '''

    [save_case]
        
        this option saves the command line to a YAML file. 
        Making it easy to be executed again using the argument --abduct with command run,
        or simply vimana run <case_name>

        This option is especially useful when command lines become huge to remember 
        or when too many lines were already executed polluting with the terminal history.
        
        example: 

        vimana run \\
            --module dmt \\
            --target-list mydjangodash.com,mydjapp1.com \\
            --port-list 4440,5001,8000,8888 \\
            --debug \\
            --threads 10 \\
            --save-case app1_dev

        Cases can also be executed during the creation process:

        vimana run \\
            --module dmt \\
            --target-list mydjangodash.com,mydjapp1.com \\
            --port-list 4440,5001,8000,8888 \\
            --debug \\
            --threads 10 \\
            --save-case app1_dev \\
            --exec-case

        '''

    def abduct(self):
        '''

    [abduct]

        this option allows an analysis to be performed from the settings of the specified yaml file. 
        The expected model can be seen in the abd.yaml example.
        
        example: vimana run --abduct abd.yaml

        '''
    
    def general_options(self):
        '''

    [general settings]

        --debug              Display debugging information and findings in realtime
        --verbose            Enable verbose mode (incremental)
        --random             Enable random mode for suported tasks
        --wait               Wait for 'n' seconds beetwen steps 
        --threads            Set number of threads to use (default: 3)
        --timeout            Set timeout for HTTP requests  (default: 5 seconds)
        --pause-steps        Run tests pausing between steps
        '''

    def fuzzer_args(self):
        '''

    [fuzzer arguments]

        --urlconf            Django URLconf with URL patterns
        --patterns           File with a list of URL patterns
        --view-name          Filter scope by viewname
        '''

    def args(self):
        '''
        [args]

    Show module arguments 
    → Usage: vimana args --module <module name>
        '''

    def start(self): 
        '''
    [start]
    
    Start Vimana in a interactive mode

    → usage: vimana start

    This option starts Vimana in interactive mode. All (required/optionals) 
    modules commands and arguments should be configured step by step before running.
        '''
        
    def info(self): 
        '''

    [info]
    
    Shows information about siddhi module

    → usage: vimana info --module <module name>

    This module retrieve full details about a given Vimana siddhi, including: 
        
        * Module description
        * Author 
        * Type
        * Category
        '''
    
    def list(self):
        '''

    [list]
    
    List available modules

    → usage: list --modules/--cases <options>

    Without <option filters> 'list' command will retrieve all modules available in
    current version of Vimana Framework.

    options:

    This command accepts a set of options to filter what kind of module will
    be listed. Suported options are:

        -t  --type
        -c  --category
        -f  --framework

    The set of arguments accepted for these options are detailed bellow:

    -t  --type  <module type>

    This option is used for search for a specific module type according
    with its function on Framework. Supported types:

        0   tracker
        1   fuzzer
        2   attack
        3   leaker
        4   exploit

    In this case could be specified a option name or a identifier number.
    Usage example: vimana list --modules --type tracker

    -c  --category  <category name>

    This option filter modules by category, accepting follow options:

        0   framework
        1   library
        2   package
        3   function

    Like 'type' option 'category' also accepts name or identifier letter (f,l,p,f)
    Usage example: vimana list --modules --category framework

    -f  --framework <framework name>

    This option allows to filter modules by framework or choose a generic type.
    Supported types in this version:

        0   Django
        1   Flask
        2   Generic

    Usage example: vimana list --modules --framework Django

    * Use cases:

    Below are shown some use cases with all the options of the list command together:

    vimana list
        Lists all available modules

    vimana list --modules --type tracker --category framework -f django
        Lists all tracker modules for Django applications

    vimana list --modules -t fuzzer -c f
        Lists all fuzzer modules for framework

    vimana list --modules --type 2 -f flask
        Lists all generic brute force modules for flask
        '''

    def run(self):
        '''

    [run]
    
    Run specific plugin/case directly by command line 

    → usage: run <case_id|name>/--module <module/resource> <arguments> <options>

    examples:

             vf run !               run the last case created
             vf run --case djapp8   run case djapp8
             vf run djapp8          run case djapp8
             vf run @cf12           run case id @cf12 (12th case created)    
             vf run \\
                --module dmt \\
                --target mydjapp4.com \\
                --sample
                                    run DMT plugin against target application mydjapp4.com
                                        on port 8889 in sample mode 
           
                     
    options:

    This command is used to run a specific module or resource type. 
    Current suported options are:

        -m  --module
        -f  --fuzzer
        -d  --discovery

    The set of arguments accepted for these options are detailed bellow:

    -m  --module  <module name> <module arguments>

    This option is used for run specific module with a set of arguments.
    The supported arguments depend on each module, to check the required 
    and optional arguments run the module without arguments or with help.
    Usage example: vimana run --module dmt --target http://pyapp.com --debug 

    Common arguments to all modules will be explained at the end.

    --fuzzer <target> <options>

    Starts fuzzing tests against target application 

    --discovery <target> <options>

    Starts application discovery. 

    scope set:

    As stated, although each module executed has its own arguments, 
    there are some common arguments to all of them that are listed below:
    
        -t  --target
        -p  --port
        -d  --debug 
        '''

    def basic_help(self):
        vmn05()
        self.overview()

    def full_help(self):
        print("\033c", end="") 
        print(VimanaHelp().__doc__.format(_version_))
        self.overview()
        print(    
            #self.overview.__doc__,
            self.start.__doc__,
            self.list.__doc__,
            self.run.__doc__,
            self.info.__doc__,
            self.set_scope.__doc__,
            self.general_options.__doc__
        )


