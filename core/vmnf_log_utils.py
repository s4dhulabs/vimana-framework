import logging
import os

def configure_logging(plugin_name):
    plugin_name = plugin_name.split('.')[0]
    
    # Use new .vimana directory structure
    vimana_home = os.getenv('VIMANA_HOME', os.path.expanduser('~/.vimana'))
    log_dir = os.path.join(vimana_home, 'logs')
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'log.vf')
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - %(levelname)s - {plugin_name} - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=log_file,
        filemode='a'
    )