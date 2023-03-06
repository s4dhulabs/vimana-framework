import os
import sys
import argparse
import importlib
from time import sleep
from datetime import datetime
from django.urls import include, path
from res.vmnf_banners import case_header
from neotermcolor import cprint,colored as cl

from .tools.vs_tools import get_views
from .parsers.vs_vparser import parse_view
from .engines.vs_authentication import vs_authentication
from .engines.vs_authorization import vs_authorization
from .engines.vs_sensitive_data import vs_sensitive_data


class siddhi:
    def __init__(self,**vmnf_handler):
        self.vmnf_handler = vmnf_handler
        
        if not vmnf_handler.get('project_dir',False):
            cprint("\n Missing project directory: vimana run --plugin viewscan --project-dir mydjangoapp/\n", "red")
            sys.exit(1)
        
        self.no_views = []
        self.target_dir = vmnf_handler.get('project_dir',False)

        self.engines_set = (
            os.path.join(os.path.dirname(__file__), 'engines')
        )
        self.engines = [os.path.splitext(f)[0] \
                for f in os.listdir(self.engines_set) \
            if f.endswith('.py') and f.startswith('vs_')]

    def run_engines(self, vast:dict):
        for engine in self.engines:
            if engine.startswith('__'):
                continue

            module_name = f'siddhis.viewscan.engines.{engine}'
            module = __import__(module_name, fromlist=[engine])
            engine_class = getattr(module, engine)
            engine_instance = engine_class(**vast)
            engine_instance.__start_scan__()

    def scan(self, views_file:str):
        target_app = views_file.split("/")[-2].strip()
        print(f'\n\n * App: {cl(target_app,44, 867, attrs=["underline", "bold"])}\n')
        
        module_obj = parse_view(views_file)
        
        if not module_obj:
            self.no_views.append(target_app)
            return False
        print()
        
        for view, vast in module_obj.items():
            self.run_engines(vast)

    def get_content(self,file_path):
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return False

    def start(self):
        if not os.path.isdir(self.target_dir):
            case_header()
            print(f"\n\t[viewscan] → Invalid target directory: {cl(self.target_dir, 'red')}!\n")
            sys.exit(1)

        views = get_views(self.target_dir)
        
        if not views:
            case_header()
            print(f'\n\t[viewscan] → No views found in: {cl(self.target_dir, "red")}\n')
            sys.exit(1)

        os.system("clear")
        cprint(f'\n[{datetime.now()}] → Starting viewscan against {len(views)} view modules...',188, 867, attrs=['bold'])
        sleep(1)

        for views_file in views:
            status = 'done'
            if os.path.getsize(views_file) == 0:
                if len(views) == 1:
                    status = 'aborted'
                    case_header()
                print(f'\n\t[viewscan] → Empty views file: {cl(views_file, "red")}\n')
                continue
            
            self.scan(views_file)

        print(f"\n\n[{datetime.now()}]: ViewScan {status}!\n\n")
        
        if self.vmnf_handler['debug']:
            if self.no_views:
                print(f'\nNo views found for apps:')
                for v in self.no_views:
                    print(f'    * {cl(v,44,867)}')
                print()


