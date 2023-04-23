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

import sys
import docker 
from time import sleep
from res.vmnf_banners import vmn05 
from neotermcolor import cprint, colored as cl



def DockerDiscovery(**opts):
    vmnf_scope = []
    d={}

    try:
        dclient = docker.APIClient(base_url='unix://var/run/docker.sock')
    except docker.errors.DockerException:
        vmn05()
        cprint(f"\n\tYou need sudo to use this feature!\n\n", 'red')
        sys.exit(1)

    print()
    for container in (dclient.containers()):
        for key,val in container.items():
            
            if key not in [
                'NetworkSettings',
                'Labels',
                'Mounts',
                'Ports',
                ]:
                
                if opts.get('debug',False):
                    print(f"{key:>15}:    {val}")
                    sleep(0.02)

            net_settings = container['NetworkSettings']['Networks']
            ports = [p.get('PrivatePort') for p in container['Ports']]

        target = [(net_settings[k].get('IPAddress')) \
            for k in net_settings.keys()
        ]
        scope  = [(target[0] + ':' + str(port)) \
            for port in ports
        ]
       
        d = {
            'IPAddress': target,
            'target_list': list(set(scope)),
            'container_info': container
        }

        vmnf_scope.append(d) 
    
    return vmnf_scope
    


