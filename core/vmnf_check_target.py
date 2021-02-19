from resources.session.vmnf_proxies import _set_socks_
from settings.siddhis_shared_settings import common
from termcolor import colored,cprint
import threading, socket, sys, time
from resources import colors
from time import sleep
from queue import Queue



class CheckTargetScope:

    def __init__(self,target=False,ports=False,**vmnf_handler):

        self.vmnf_handler = vmnf_handler
        if not ports:
            ports = common().homolog_ports

        self.port_status = False
        self.target = target
        self.port_list  = ports
        self.t = []
        self.p = []
        self.s = []
        self.open_ports   = []
        self.valid_scope  = []
        self.closed_ports = []
        self.thread_list  = []
        self.queue = Queue()
    
    def port_is_open(self,port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(int(self.vmnf_handler['timeout']))
            sock.connect((self.target, port))
            return True
        except:
            return False

    def worker(self):
        while not self.queue.empty():
            port = int(self.queue.get())

            if self.port_is_open(port):
                self.valid_scope.append(str(self.target + ':' + str(port)))
                _status_ = colored('Open', 'green', attrs=['bold'])
            else:
                self.closed_ports.append(port)
                _status_ = colored('Closed', 'red', attrs=[])

            _target_ = colored(self.target.strip(), 'yellow')
            _port_   = colored(port, 'yellow')
            self.t.append(_target_)
            self.p.append(_port_)
            self.s.append(_status_)

    def thread_handler(self):

        thread_list = []
        for _ in range(int(self.vmnf_handler['threads'])):
            thread = threading.Thread(target=self.worker)
            thread_list.append(thread)

        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()

    def start_scan(self):

        '''It is certainly not the most elegant way to do this, but for now its enough.'''
        proxy_set = _set_socks_(**self.vmnf_handler).test_conn()
        if proxy_set:
            exit_ip = str(proxy_set['response'].content).replace("b",'').replace("'",'')
            status = colored('OK','green', attrs=['bold'])
            eip = colored(exit_ip, 'green')
            msg = colored('Connection going out {}'.format(eip),'cyan')
            proxy_type = colored(proxy_set['proxy_type'].rstrip().upper() + ' proxy', 'blue')
            _s_ = colored('{}: {} → {}'.format(proxy_type, status, msg ,'cyan'))
            print('{} {}'.format(colored('⡯⠥','green', attrs=['bold']),_s_))
            sleep(0.25)

        print("{} Validating port status for target {}{}{}...\n".format(
            colors.Gn_c + "⠿⠥" + colors.C_c,
            colors.G_c,
            self.target,
            colors.D_c
            )
        )
        sleep(0.10)

        for port in self.port_list:
            self.queue.put(port)
             
        self.thread_handler()

        gen_status = list(zip(self.p,self.s))
        for i, d in enumerate(gen_status):
            line = ' '.join(str(x).ljust(17) for x in d)
            print('     {}'.format(line))
            if line == 0:
                print('-' * len(line))
            sleep(0.10)
        print()

        return self.valid_scope
