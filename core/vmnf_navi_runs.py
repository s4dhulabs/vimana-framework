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
        with open(f'{dirname(__file__)}/vfns.yaml', 'r') as f:
            vmnf_handler = yaml.load(f,Loader=yaml.FullLoader)

        dast_set = config["DAST_SETTINGS"]
        sast_set = config["SAST_SETTINGS"]
        scan_set = config["SCAN_OPTIONS"]

        vmnf_handler.update(
            **dast_set, 
            **sast_set, 
            **scan_set
        )

        return vmnf_handler

