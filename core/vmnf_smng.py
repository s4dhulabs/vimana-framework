from siddhis.djunch.engines._dju_settings import table_models
from siddhis.djunch.engines._dju_utils import DJUtils 
from ._dbops_.vmnf_dbops import VFSiddhis as VFS
from neotermcolor import cprint, colored as cl
from ._dbops_.vmnf_dbops import VFDBOps
from res.vmnf_banners import case_header
from .vmnf_sessions import VFSession
from .vmnf_utils import describe
from .oms import vfACK
import sys
import os


class VFManager:
    def __init__(self,**handler:False):
        self.handler = handler
        
        if not handler.get('module_run'):
            ''' We're not going to use query filters with vf run -m '''

            self.query_filters = self.get_filters()

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

