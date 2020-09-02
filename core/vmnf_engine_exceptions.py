from resources import colors
import sys



class engineExceptions:

    def __init__(
        self, 
        args=False, 
        exception=False
        ):

        self.args = args
        self.exception = exception

    def argument_error(self):

        if 'run' and '--module' in self.args:
            siddhi = self.args[self.args.index('--module') + 1].strip()
            siddhi_path = 'siddhis.{}.{}'.format(siddhi, siddhi)

        conflict_msg = """
        \r Vimana exits with an argparse.ArgumentError() exception

        \r This exception usually occurs when an argument present in the shared args
        \r has also been specified in the parser of the module to be run .

        \r If you're using Vimana shared arguments, make sure {} argument doesn't exist
        \r in module parser in {}.args()
        """.format(
            self.exception.argument_name, 
            siddhi_path 
        )

        print("\033c", end="")
        print(conflict_msg)
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
        \r{}: {}
        \r{}
        \r{}
        '''.format(mark, VIE, ERROR, mark.strip('\n'), MSG))
1
