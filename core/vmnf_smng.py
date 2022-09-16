from siddhis.djunch.engines._dju_settings import table_models
from siddhis.djunch.engines._dju_utils import DJUtils 
from ._dbops_.vmnf_dbops import VFSiddhis as VFS
from neotermcolor import cprint, colored as cl
from ._dbops_.vmnf_dbops import VFDBOps
from res.vmnf_banners import case_header
from .vmnf_sessions import VFSession
from .vmnf_utils import describe
from .vmnf_asserts import vfasserts
import sys
import os


class VFManager:
    def __init__(self,**handler:False):
        self.handler = handler
        
        if not handler.get('module_run'):
            ''' We're not going to use query filters with vf run -m '''

            self.query_filters = self.get_filters()

    def no_match(self):
        case_header()
        cprint("\tNo modules were found with the given criteria:\n", 'red')

        [print(f"\t{filter.get('field'):>15}: {filter.get('value')}") \
            for filter in self.query_filters ]

        print()
        print()

    def get_filters(self):
        filters = []

        for field,value in self.handler.items():

            if not value or value is None:
                continue
            
            if field in ['module_list', 'args']:
                continue
            
            if field in ['module_info']:
                self.handler['module'] = \
                        self.handler['module_info']

                self.handler['module_info'] = False
                field = 'module'
            
            elif field == 'module_guide':
                self.handler['module'] = \
                        self.handler['module_guide']

                self.handler['module_guide'] = False
                field = 'module'

            elif field == 'module_run':
                self.handler['module'] = \
                        self.handler['module_run']

                self.handler['module_run'] = False
                field = 'module'
            
            filters.append({
                'field': field,
                'op': '==',
                'value': value.lower()
                }
            )

        return filters

    def show_guide(self, sguide, sections:list):
       
        if '-e' in sections:
            # command line examples 
            for ie in sguide['examples'].split('\n'):
                print(f"\t\t{cl(ie,'white')}")

        if '-a' in sections:
            # only args 
            for arg in sguide['args'].split('\n'):
                print(f"\t\t{cl(arg,'white')}")
        
        if '-l' in sections:
            # lab test setup
            for lset in sguide['lab_setup'].split('\n'):
                print(f"\t\t{cl(lset,'white')}")
    
    def get_siddhi_guide(self):
        siddhi = self.get_siddhi()
        _vfassert_ = vfasserts(**self.handler)
        
        if siddhi is None:
            self.no_match()
            return False

        sguide = siddhi.guide
        
        print("\033c", end="")
        print()
        
        # full guide -> examples, args, labs
        #if vfACK(**self.handler).default_guide_mode():
        if _vfassert_.default_guide_mode():
            self.show_guide(sguide,['-e', '-a', '-l'])

        # command line examples
        elif self.handler.get('guide_examples'):
            self.show_guide(sguide,['-e'])

        # only args
        elif self.handler.get('guide_args'):
            self.show_guide(sguide,['-a'])
    
        # lab test setup
        elif self.handler.get('guide_labs'):
            self.show_guide(sguide,['-l'])

        return sguide

    def show_siddhi_info(self):
        siddhi = self.get_siddhi()

        if siddhi is None:
            self.no_match() 
            return False

        describe().siddhi(siddhi)

    def query_siddhis(self):
        return (VFS().list_siddhis_db(self.query_filters))
        
    def get_siddhi(self):
        return VFS().get_siddhi(self.handler['module'])

    def get_siddhis_stats(self):
        from core.vmnf_payloads import VMNFPayloads
        payloads = VMNFPayloads()._vmnfp_payload_types_(True,False)

        siddhis = VFS().get_all_siddhis()       
        stats = [s.type.lower() for s in siddhis]
        stats = {st:stats.count(st) for st in stats}
        stats['payloads'] = len(payloads)

        for k,v in stats.items():
            print(f"{cl(k, 'cyan'):>32}: {cl(v,'green')}")
        
        print()
        print()

