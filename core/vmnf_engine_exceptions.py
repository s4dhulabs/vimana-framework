from neotermcolor import colored as cl
from res.vmnf_banners import mdtt1
from res import colors
import sys



class engineExceptions:

    def __init__(self, args=False, exception=False):

        self.args = args
        self.exception = exception

    def PermissionError(self):
        print("\033c", end="")
        mdtt1()
        
        print(f"""

        Vimana engine got a PermissionError-like exception from
        a crawler process. To fix this, you have two alternatives:

        Running Vimana with {cl('sudo','green')} at first to allow the engine to
        create the basic structure of caching and log:

        $ {cl('sudo','green')} {self.args}

        Adding {cl('--disable-cache', 'green')} to the command line:

        $ {self.args} {cl('--disable-cache', 'green')}

        """)
            
        #sys.exit(1)

    def unexpected_keyword(self):
        print("\033c", end="")
        mdtt1()

        print(f'''
        Vimana identified some integrity issues related to
        argparser engine. Check if you have made any changes in
        these core files and try to fix the issue. Or simply set
        Vimana again.

        {cl(self.exception,'red')}
        ''')

    def argument_error(self):

        if 'run' and '--module' or '-m' in self.args:
            siddhi = self.args[self.args.index('--module') + 1].strip()
            siddhi_path = 'siddhis.{}.{}'.format(siddhi, siddhi)

        conflict_msg = """
        Vimana exits with an argparse.ArgumentError()
        exception

        This exception usually occurs when an argument
        present in the shared args has also been
        specified in the parser of the module to be run.

        If you're using Vimana shared arguments, make
        sure {} argument doesn't exist in 
        module parser in {} argparser.

        """.format(
            cl(self.exception.argument_name, 'red'),
            cl(siddhi, 'red')
        )

        print("\033c", end="")
        print(conflict_msg)
        mdtt1()
        sys.exit(1)

    def template_atribute_error(self, AEX, module):

        AEX_ = colors.R_c + str(AEX) + colors.D_c
        mark = '-' * 70
        trackback = colors.Y_c + str(AEX.with_traceback) + colors.D_c

        VIE = colors.Rn_c + '→ VIMANA-IMPORT-ERROR' + colors.D_c
        ERROR =  '{}An error has occurred in the module "{}"{}'.format(colors.Y_c, module, colors.D_c)
        MSG = '''\r
        \rMake sure the code follows the template rules available in:
        \r[vimanapath]/templates/module_template.py

        \r* Your module should be in a directory with the same name inside path siddhis/
        \rlike for a tool called flasky should be in siddhis/flasky/flasky.py

        \r* If your tool require external modules (coded by you), so all these modules must starts with "__"
        \rtwo underscore in the begin, like in example above:

        \nDetails: {}
        '''.format(AEX_)

        print('''
        \r{}
        \r{}
        \r{}
        \r{}
        '''.format(mark,VIE,ERROR,mark.strip('\n'),MSG))

