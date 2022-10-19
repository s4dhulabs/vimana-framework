# encoding=utf8

from res.colors import *
from random import choice
from res.vmnf_banners import s4dhu0nv1m4n4,vmn05
from neotermcolor import colored, cprint
from core.load_settings import _version_


class VimanaHelp:
    '''
           .__
    ___  _|__| _____ _____    ____ _____
    \  \\/ /  |/     \\\\__  \\  /    \\\\__  \\
     \   /|  |  Y Y  \\/ __ \\|   |  \\/ __ \\_
      \_/ |__|__|_|__(____  /___|  (____  /
                         \\/      \\/     \\/   
        @s4dhulabs           
        
    '''

    def __init__(self):
        '''@'''

    def overview(self):
        ovw = {
            'about' : "About the framework",
            'flush' : "Remove a recorded resource", 
            'guide' : "Show plugin usage examples and args",
            'info'  : "Show information about plugins",
            'list'  : "List available plugins",
            'load'  : "Load a recorded session (post-analysis)",
            'run'   : "Run a resource, plugin or case",
            'start' : "Start Vimana in a interactive mode",
        }
        
        board_colors = ['white']
        cmd_hl = choice(['cyan','green','white'])

        print('\n\n\n')
        # ⇀
        for cmd, desc in ovw.items():
            print("{:>27}  {}    {}".format(
                colored(cmd,'magenta'),
                colored(choice(['◍','◎', '◉']) + choice(['◍','◎', '◉']), 
                    choice(board_colors),attrs=[ choice(['dark','bold'])]
                ),
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

    [ save_case ]
      
    This option saves the command line to a YAML
    file. Making it easy to be executed again using
    the argument --abduct with command run, or simply
    vimana run <case_name>

    This option is handy when command lines become
    huge to remember or when too many lines were
    already executed, polluting the terminal history.

    example: 

    $ vimana run \\
        --module dmt \\
        --target-list mydjangodash.com,mydjapp1.com \\
        --port-list 4440,5001,8000,8888 \\
        --debug \\
        --threads 10 \\
        --save-case app1_dev

    Cases can also be executed during the creation process:

    $ vimana run \\
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

    [ abduct ]

        this option allows an analysis to be performed from the settings of the specified yaml file. 
        The expected model can be seen in the abd.yaml example.
        
        example: vimana run --abduct abd.yaml

        '''
    
    def general_options(self):
        '''

    [ general settings ]

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

    [ fuzzer arguments ]

        --urlconf            Django URLconf with URL patterns
        --patterns           File with a list of URL patterns
        --view-name          Filter scope by viewname
        '''

    def args(self):
        '''
    [ args ]

    Show module arguments 
    → Usage: vimana args --module <module name>
        '''

    def guide(self):
        '''

    [ guide ]

    Show usage examples

    → Usage: vimana guide --plugin <plugin name> <options>
    
    Examples:

        # Show full DMT plugin guide
        $ vimana guide --module dmt
        $ vimana guide -m dmt

        # Show DMT plugin arguments with highlights
        $ vimana guide --module dmt -args --highlights:
        $ vimana guide -m dmt -a

        # Show only usage examples
        $ vimana guide --module dmt --examples
        $ vimana guide -m dmt -e

        # Show lab setup tips:
        $ vimana guide -m dmt --labs
        $ vimana guide -m dmt -l

        '''

    def start(self): 
        '''
    [ start ]
    
    Start Vimana in a interactive mode

    → usage: vimana start

    This option starts Vimana in interactive mode. All (required/optionals) 
    modules commands and arguments should be configured step by step before running.
        '''
        
    def info(self): 
        '''

    [ info ]
    
    Shows information about siddhi module

    → usage: vimana info --siddhi <siddhi name>

    Retrieve full details about a given plugin, including: 
        
        * Description
        * Author 
        * Type
        * Category
        * CWEs
        * Tags
        '''
    
    def flush(self): 
        '''

    [ flush ]
    
    Remove a recorded resource: sessions/cases

    → usage: vimana flush <resource type> <parameters>

    Examples:
        
    $ vimana flush --sessions                 Remove all sessions
    $ vimana flush --session 2720b71be1       Remove session 2720b71be1 from database
    $ vimana flush --case newdjango_apps      Remove newdjango_apps case 
    $ vimana flush --cases                    Remove all cases
        '''
   
    def load(self):
        ''' 
        
    [ load ]

    Load recorded resources and plugins.
    
    → usage: vimana load <resource type> 

    --session   Load a given session by its ID
    --plugins   Load plugins on Vimana initial setup

    Examples:
    
    ◈  Load Vimana plugins during framework setup:
    
    $ vimana load --plugins 
    
    ◈  Load recorded session with ID 4a0a5a8c99:
    
    $ vimana load --session 4a0a5a8c99
        '''

    def list(self):
        '''

    [list]
   
    List available resources on the current setup
    and version of the Vimana Framework. This is
    a core command used for all sorts of resources
    such as plugins, cases, sessions, and payloads:

    $ vimana list 
        --plugins  
        --cases
        --sessions
        --payloads 

    --plugins	List all available plugins

    Without filters, the list command with --plugins
    argument will retrieve all plugins available in
    the current version of Vimana Framework.

    Lately, it supports the following filters:

    --framework	    Filter plugins by framework:

		    ‣  django 
		    ‣  flask

    --category	    Filter plugins by category:

		    ‣  framework 
		    ‣  package
		    ‣  discovery

    --type	    Filter plugins by type:

		    ‣  fingerprint
		    ‣  persistence
		    ‣  tracker 
		    ‣  exploit 
		    ‣  fuzzer 
		    ‣  crawler 
		    ‣  audit 
		    ‣  parser
    Examples:

    ◈  List all tracking plugins for Django framework:

    $ vimana list \\
        --plugins \\
        --type tracker \\
        --framework django 

    ◈  List plugins from type fuzzer:

    $ vimana list \\
        --plugins \\
        --type fuzzer

    ◈  List exploit plugins for Python packages:

    $ vimana list \\
        --plugins \\
        --exploit \\
        --category package

    --sessions	    List all recorded sessions
    --cases	    List all recorded cases
    --payloads	    List available payloads
        '''
    
    def run(self):
        '''

    [ run ]
    
    Run specific plugin/case directly by command line 

    → usage: run <case_id|name>/--plugin <name>/resource> 
	
      Examples:

      Start jungle against the Django application admin
      portal using a custom password and username lists,
      setting default proxy (SOCKS5://127.0.0.1:9050)
      and enabling debug:
	
      $ vimana run \\
        --plugin jungle \\
	--target-url http://mydjapp1.com:8887 \\
	--usernames usernames.txt \\
	--passwords passwords.txt \\
	--set-proxy \\      
	--debug
    
    ø------------------------------------------------------------ø

      Run DMT against Django target URL http://djlabs1.com:9001
      disabling external lookups (like CVE, Tickets, etc)
      and exiting on the first exception caught. If you are
      running a Vimana module without sudo, in some cases, if the
      resource needs to write in disk, for cache http objects,
      for instance, the analysis could fail. With that in mind,
      sometimes it is handy to run the same set of arguments
      adding --disable-cache, but usually, the framework will
      warn you about that. In addition, this dmt command line
      enables debug mode and sets confirmations in some steps
      to Yes.

      $ vimana run \\
        --plugin dmt \\
	--target-url http://djlabs1.com:9001 \\
	--disable-external \\
	--exit-on-trigger \\
	--disable-cache \\
	--debug \\
	--auto

    ø------------------------------------------------------------ø

      In the example below, we're starting djunch fuzzer against
      the Django application running on http://mydjapp2.com:8887,
      passing as scope the url.py used by the application. This
      can be taken as a kind of gray box perspective:
		
      $ vimana run \\
	--fuzzer \\
	--target mydjapp.com \\
	--port 8887 \\
	--urlconf app/urls.py

     * Running analysis from Vimana cases:

     $ vimana run !               # run the last case 
     $ vimana run --case djapp8   # run case djapp8
     $ vimana run djapp8          # run case djapp8
     $ vimana run @cf12           # run case id @cf12 


     ◍  Use `vimana guide --plugin <plugin_name> --args`
        for more details such as the required arguments
        and examples for each plugin.

     ◍  Note that the parameter to specify the plugin
        in Vimana is interchangeable. With that, you
        can either use --plugin, --siddhi, or --module,
        they have the same attributes as you will see
        in guides and examples.
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


