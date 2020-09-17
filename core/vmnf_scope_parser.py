
from core.vmnf_check_target import CheckTargetScope
from netaddr.core import AddrFormatError
from libnmap.parser import NmapParser
from termcolor import colored, cprint
from datetime import datetime
from netaddr import valid_ipv4
from netaddr import IPNetwork
from time import sleep
import pathlib
import socket
import sys
import os


class ScopeParser:
    def __init__(self, **handler_ns):
        self.handler_ns = handler_ns
        self.target_scope = {}

        self.scope_error = colored(' - scope_error - ', 'red', 'on_white', attrs=['bold'])
        self.target_defined = True if handler_ns['single_target'] \
            or handler_ns['file_scope'] \
            or handler_ns['ip_range'] \
            or handler_ns['cidr_range'] \
            or handler_ns['list_target'] else False

    def scope_validate(self):        
        valid_scope_port = False
        targets = []
        ports   = []
        invalid_targets = []

        for target in self.target_list:
            target = target.replace('http://','').replace('https://','')
            
            if ":" in target:
                target = target[:target.find(':')]
            try:
                if (valid_ipv4(target)):
                    targets.append(target)
                elif valid_ipv4(socket.gethostbyname(target)):
                    targets.append(target)
                else:
                    invalid_targets.append(target)
            except AddrFormatError:
                continue
            except socket.gaierror as sge:
                continue 

        for port in self.port_list:
            try:
                port = int(port)
                ports.append(port)
            except ValueError:
                pass

        for target in targets:
            self.port_status = None
            self.port_status = CheckTargetScope(target,ports,**self.handler_ns).start_scan()
            
            if self.port_status and self.port_status is not None:
                valid_scope_port = True
                self.target_scope[str(target)] = self.port_status

        if self.target_defined and not valid_scope_port:
            arg = colored('--ignore-state', 'green', attrs=[])
            print('''{} No active port has been identified. Check the target's IP with a network scanner or use {} argument on vimana command line.'''.format(self.scope_error,arg))
            
            print(valid_scope_port)
            sys.exit(1)

    def parse_scope(self):
        _scope_ = {}
        self.target_list = []
        self.port_list = []
                
        if self.handler_ns['nmap_xml']:
            xml_scope_file = self.handler_ns['nmap_xml']
            xml_location = str(pathlib.Path().absolute()) + '/' + xml_scope_file
            
            if not os.path.exists(xml_location):
                print('''\r{} XML file not found: {}. Check the file location and try again.\n'''.format(
                    self.scope_error,xml_location))    
                
                return False

            # check if its a file
            if not os.path.isfile(xml_location) \
                or not xml_location.endswith('.xml'):
                arg = colored('--nmap-xml', 'green')
                print('''\r{} Invalid XML file: {}. {} argument requires an nmap results file with an .xml extension\n'''.format(
                    self.scope_error, xml_scope_file, arg
                    )
                )
                return False

            nmap_scan_result = NmapParser.parse_fromfile(xml_location)
            for target in nmap_scan_result.hosts:
                target_status = str(target).split('-')[1][+1:-1].rstrip()
                if target_status == 'up':
                    target_list = []
                    for _ts_ in target.services:
                        if _ts_.state == 'open':
                            target_list.append(str(target.address) + ':' + str(_ts_.port))
                    if target_list:
                        self.target_scope[str(target.address)] = target_list

        # ***   scope: single target   *** 
        elif self.handler_ns['single_target']:
            if "," in str(self.handler_ns['single_target']):
                arg = colored('--target-list', 'green', attrs=[])
                print('''\r{} Invalid format for the --target argument, try this with {} or specify a single target.\n'''.format(self.scope_error,arg)) 
                sys.exit(1)  
            target = self.handler_ns['single_target']
            try:
                if (valid_ipv4(target)):
                    self.target_list.append(target)
                elif valid_ipv4(socket.gethostbyname(target)):
                    self.target_list.append(target)
                else:
                    print('[parse_scope → {}] Invalid target format'.format(target)) 
                    return False
            except socket.gaierror:
                print('[parse_scope] Target validation failure: {}'.format(target))
                return False

        # ***   scope: target list  *** 
        elif self.handler_ns['list_target']:
            for target in self.handler_ns['list_target'].split(','):
                if target.count('.') == 3:
                    self.target_list.append(target)
        
        # ***   scope: "file" with targets   ***
        elif self.handler_ns['file_scope']:
            scope_file = self.handler_ns['file_scope']
            scope_location = str(pathlib.Path().absolute()) + '/' + scope_file

            # check if a scope file exists
            if not os.path.exists(scope_location):
                arg = colored('--file-scope', 'green', attrs=[])
                print('''\r{} File scope not found: {}\n'''.format(self.scope_error, scope_location))
                sys.exit(1)

            # check if a valid scope file
            elif not os.path.isfile(scope_location):
                print('''\r{} Invalid scope file: {}\n'''.format(self.scope_error, scope_location))
                sys.exit(1)

            fh = open(self.handler_ns['file_scope'], 'r')
            fh = fh.readlines()
            for target in fh:
                if target.count('.') == 3:
                    target = target.rstrip()
                    self.target_list.append(target)
            if not (self.target_list):
                print('''\r{} No valid target was identified in the file scope: {}\n'''.format(self.scope_error, scope_location))
                sys.exit(1) 

        # ***   scope: network "range"    ***
        elif self.handler_ns['ip_range']: 
            r = self.handler_ns['ip_range']
            stop = self.handler_ns['ip_range'].split('-')[1]
            counter = int(r[:r.index('-')].split('.')[-1])
            base_ip = str('.'.join(r[:r.index('-')].split('.')[:-1]))

            try:
                while counter < int(stop) + 1:
                    IP = base_ip + '.' + str(counter)
                    self.target_list.append(IP)
                    counter += 1
            except ValueError as VU:
                    print('Invalid format {}'.format(VU)) 

        # ***   scope: CIDR "range" of targets   ***
        elif self.handler_ns['cidr_range']:
            cidr = str(self.handler_ns['cidr_range'])
            for IP in IPNetwork(cidr): 
                self.target_list.append(str(IP))

        # ***   scope: single port   ****
        if self.handler_ns['single_port']:
            if "," in str(self.handler_ns['single_port']):
                arg = colored('--target-list', 'green', attrs=[])
                print('''\r{} Invalid format for the --port argument,try this with {} or specify a single port.\n'''.format(self.scope_error,arg))
                sys.exit(1)
            self.port_list.append(self.handler_ns['single_port'])

        # ***   scope: port range    ****
        elif self.handler_ns['port_range']:
            if not "-" in str(self.handler_ns['port_range']):
                arg = colored('--port-range', 'green', attrs=[])
                print('''\r{} Invalid format for the {} argument. Range must be separated by dash: 8000-8010\n'''.format(self.scope_error,arg))
                sys.exit(1)
            
            plist = []
            start, stop = self.handler_ns['port_range'].split('-')
            for port in range(int(start), int(stop) + 1):
                self.port_list.append(port)

        # ***   scope: port list    ****
        elif self.handler_ns['port_list']:
            
            if not "," in str(self.handler_ns['port_list']):
                arg = colored('--port-list', 'green', attrs=[])
                print('''\r{} Invalid format for the {} argument. Ports must be separated by a comma.\n'''.format(self.scope_error,arg))
                sys.exit(1)
            
            plist = ' '.join(self.handler_ns['port_list'])
            for port in plist.split(','):
                self.port_list.append(port)
        
        if not self.handler_ns['nmap_xml']:
            if not self.handler_ns['ignore_state']:
                self.scope_validate()
            else:
                self.target_scope = {
                    'targets': self.target_list,
                    'ports'  : self.port_list
                }

        return self.target_scope
    
        
        
