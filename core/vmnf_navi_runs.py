# -*- coding: utf-8 -*-
#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[at]prontonmail[dot]ch
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

import os
import yaml
from os.path import dirname
from ._dbops_.models.siddhis import Siddhis
from .vmnf_navicontrols import navi_set_args

class navi_siddhi_run:
    def __init__(self, plugin: Siddhis):
        self.plugin = plugin

    def manage(self) -> list:
        
        with open(f'{dirname(__file__)}/autorun.yaml', 'r') as f:
            config = yaml.load(f,Loader=yaml.FullLoader)
        """
        # If configured via settings file
        if not any(v for s in config.values() for v in s.values()):
            print('You need set the scope before running plugins')
            return False
        """

        with open(f'{dirname(__file__)}/vfns.yaml', 'r') as f:
            vmnf_handler = yaml.load(f,Loader=yaml.FullLoader)

        dast_set = config["DAST_SETTINGS"]
        sast_set = config["SAST_SETTINGS"]
        scan_set = config["SCAN_OPTIONS"]

        vmnf_handler.update(**dast_set, **sast_set, **scan_set)

        # needs to be handled just in dast scans
        vmnf_handler['scope'] = {
            'target_url': [
                dast_set['target_url']
            ]
        }
        vmnf_handler['module_run'] = self.plugin.name
        vmnf_handler['module'] = self.plugin.name
        vmnf_handler['save_session'] = True
        vmnf_handler['exit_on_trigger'] = True

        true_params = [k for k,v in vmnf_handler.items() if v]
        set_args = navi_set_args(self.plugin)

        # if plugin doesn't support fully navigation or if the required args were not set
        if not set_args or all(value in (False, None, '') for value in set_args.values()):
            return False

        vmnf_handler.update(**set_args)

        module_path = f"siddhis.{self.plugin.name}.{self.plugin.name}"
        siddhi = __import__(module_path, globals(), 'siddhi', 1).siddhi
        try:
            print('\033[2J\033[1;1H')
        # TypeError: 'bool' object is not iterable
            result = list(siddhi(**vmnf_handler).start())
        except TypeError:
            return False
        
        return result

