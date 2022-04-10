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

    
