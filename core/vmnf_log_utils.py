import logging
import os

def configure_logging(plugin_name):
    plugin_name = plugin_name.split('.')[0]
    log_dir = os.path.expanduser('~/vimana/log')
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