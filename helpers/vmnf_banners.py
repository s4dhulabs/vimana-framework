from termcolor import colored, cprint


class vmnf_banners:
    def __init__(self):
        ''' Vimana banners resource '''

    def circuits_banner(self,proc_type=False):
        proc_type = colored(proc_type, 'red') if proc_type else ''
        banner = colored('''
        ┬  ┬┬┌┬┐┌─┐┌┐┌┌─┐
        └┐┌┘││││├─┤│││├─┤  
         └┘ ┴┴ ┴┴ ┴┘└┘┴ ┴
                {0}
        '''.format(proc_type), 'green', attrs=['blink', 'bold'])

        return banner

    def ansi_banner(self):
        '''
        ██╗   ██╗██╗███╗   ███╗ █████╗ ███╗   ██╗ █████╗
        ██║   ██║██║████╗ ████║██╔══██╗████╗  ██║██╔══██╗
        ██║   ██║██║██╔████╔██║███████║██╔██╗ ██║███████║
        ╚██╗ ██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║
         ╚████╔╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║
          ╚═══╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
        '''


