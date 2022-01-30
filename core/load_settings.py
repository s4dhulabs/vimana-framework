import yaml
from os.path import dirname

with open(dirname(__file__) + '/vmnf_settings.yaml') as file:
    vf_settings = yaml.load(
        file, Loader=yaml.FullLoader
    )

    _version_ = vf_settings['project'].get('version')
    _cs_ = vf_settings['settings'].get('case_set')
    _ap_ = vf_settings['settings'].get('arg_parser')
    
