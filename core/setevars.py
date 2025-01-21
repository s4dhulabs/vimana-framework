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
import subprocess



def set_vimana_path(env_var_value):
    env_var_name = "vimana_path"
    user_shell = os.path.basename(os.environ['SHELL'])
    config_files = [".bashrc", ".zshrc", ".bash_profile", ".profile"]
    config_file = None

    for file in config_files:
        potential_config_file = os.path.expanduser(f"~/{file}")
        if os.path.isfile(potential_config_file):
            config_file = potential_config_file
            break

    if config_file:
        source_config = f'source {config_file} && exec $SHELL'
        export_vfvar = f'export {env_var_name}="{env_var_value}"\n'

        with open(config_file, "a") as f:
            f.write(export_vfvar)

        subprocess.run(
            [user_shell, "-c", source_config], shell=True
        )


