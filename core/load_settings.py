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

import yaml
from os.path import dirname

with open(f"{dirname(__file__)}/vmnf_settings.yaml") as file:
    vf_settings = yaml.load(
        file, Loader=yaml.FullLoader
    )

    _version_ =  vf_settings['project'].get('version')
    _vfs_     =  vf_settings['settings'] 
    _utils_   =  _vfs_['utils']
    _siddhis_ =  _vfs_.get('siddhis_set')
    _cs_      =  _vfs_.get('case_set')
    _ap_      =  _vfs_.get('arg_parser')

    
