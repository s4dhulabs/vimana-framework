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

from ._dbops_.models.siddhis import Siddhis
from pygments.lexers import JsonLexer
from pygments.lexers.python import PythonLexer
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.lexers import PygmentsLexer

from prompt_toolkit.widgets import Frame, TextArea, Box, SearchToolbar
from prompt_toolkit.shortcuts import print_container,button_dialog
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit import print_formatted_text
from neotermcolor import cprint,colored as cl
from prompt_toolkit.styles import Style
from res.vmnf_banners import *
from time import sleep
from random import choice
import termios
import sys
import tty
import os

from .vmnf_navioptions import *

def navi_set_args(plugin:Siddhis) -> dict:
    plugin_name = plugin.name
    
    if not 'naviargs' in plugin.guide:
        print('\033[2J\033[1;1H')
        case_header()
        input(f"""\t{colored(plugin_name,'green')} does not support scans in navigation mode yet.""")
        return False
    
    naviargs = plugin.guide['naviargs']

    custom_style = Style.from_dict({
        'dialog': 'bg:#000000',
        'dialog.body': 'bg:#000000 #ffffff',
        'dialog frame.label': 'bg:#000000 #00ff00',
        'dialog.body label': '#00ff00',
        'dialog.body text-area': '#000000',
        'dialog frame.border': '#00ff00',
    })

    d = {}
    for i, (param, value) in enumerate(naviargs.items(), start=1):
        field_set = input_dialog(
            title=f"{plugin_name} scope setup {i}/{len(naviargs)}",
            text=f"{param.replace('_',' ')}:", style=custom_style
        ).run()

        d[param] = field_set

    return d

def print_scan_tree(
    dir_path, 
    padding=' ...', 
    is_last=False, 
    scan_id=False
    ):
    
    max_key_width = 0
    files = os.listdir(dir_path)
    kv_like = [file.split('_vs_') for i,file in enumerate(files) if '_vs_' in file]
    objects = [_[0] for _ in kv_like]

    if objects:
        max_key_width = max(len(o) for o in objects) 

    if not scan_id:
        print('\033[2J\033[1;1H')
        case_header()
        print()
        print()
        scan_details = dir_path.split('/') 
        project = scan_details[-2]
        scan_id = scan_details[-1]
        cprint(f"   {project}",'blue')
        print(padding + '|' + ' .')
        print(padding + '|' + f'.. {scan_id}')
        print(' ...| .....|.')

    for i, file in enumerate(files):
        file_path = os.path.join(dir_path, file)
        is_last_file = i == len(files) - 1
        is_last_file = i == len(files) - 1
        
        if file.endswith('.sarif') and not '_vs_' in file:
            continue

        max_key_width = 40
        if '_vs_' in file:
            file,rule_id = file.split('_vs_')
            obj_line = '.' * (max_key_width - len(file))

            file = f"{file} {obj_line} {rule_id.split('.')[0]}"

        if os.path.isdir(file_path):
            print(padding + '|' * (not is_last) + '... ' + file + '/')
            print_scan_tree(file_path, padding + '|' + padding * (not is_last) + '..', is_last_file, scan_id)
        else:
            print(padding + '|' * (not is_last) + '... ' + file)
    
    print(padding + '|' + ' .')

def navioptions_menu(menu_type:str, menu_title:str='Navigation Options'):
    print('\033[2J\033[1;1H')
    default_naviban()
    print()
    
    try:
        menu_option = menu_options[menu_type]
    except KeyError:
        menu_option = menu_type

    print_container(
        Box(Frame(
            TextArea(text=menu_option),
                    title=menu_title,width=70
            ),
            padding_left=0,
            padding_top=0,
            padding_bottom=1
        )
    )
    input()


def navialert(alert_msg):

    #print('\033[2J\033[1;1H')
    #print()
    
    banner = f"""
                        
                       _V_V_
                    [\/__-__\/]
                    [(|~ø ø~|)]
                    [/ \`-'/ \]
                      _/`-'\_

                  {alert_msg}
    """

    print_container(
        Box(Frame(
            TextArea(text=banner),
                title='',width=70
            ),
            padding_left=0,
            padding_top=0,
            padding_bottom=1
        )
    )
    input()


def flush_all(items:list, type:str):
    action_msg = f'''
    You're about to remove {len(items)} {type}:
    '''
    result = button_dialog(
        title=f"NaviScan: {type}",
        text=action_msg,
        buttons=ok_cancel_buttons,
        style=default_dark_style
    ).run()

    return result

def naviscan_delete(scan):
    action_msg = f'''
    You're about to remove the scan below:
      
        object:  {scan}
            id:  {scan.scan_id}
          type:  {scan.scan_type}
       project:  {scan.scan_target} ({scan.project_framework} {scan.project_framework_version})
         scope:  {scan.project_total_view_modules} view modules
          reqs:  {scan.project_total_requirements}
          date:  {scan.scan_date}

    '''
    result = button_dialog(
        title="NaviScan",
        text=action_msg,
        buttons=ok_cancel_buttons,
        style=default_dark_style
    ).run()

    return result

def navix_delete(x):
    action_msg = f'''
    You're about to remove the exception below:

        object: {x}
            id: {x.exception_id}
          type: {x.exception_type}
         class: {x.exception_class}
     framework: {x.framework}
        module: {x.module}
       trigger: {x.trigger}
        method: {x.method}
        plugin: {x.scan_plugin}

    '''

    result = button_dialog(
        title="NaviX",
        text=action_msg,
        buttons=ok_cancel_buttons,
        style=default_dark_style
    ).run()

    return result

def naviobject_delete(object_ref,app_view_objects:list=False):
    scan_id, project, selected_app, selected_object, rule = object_ref.split('.')
    
    if app_view_objects:
        object_type = 'Apps'
        action_msg = f"""
        Your going to delete '{selected_app}' object from scan result:

             views:  {",".join(app_view_objects)}
              scan:  {scan_id}
           project:  {project}

        """
    else: 
        object_type = 'Views'
        action_msg = f"""
        You're about to remove the view below from scan results:

              view:  {selected_app}.{selected_object}
              scan:  {scan_id}
           project:  {project}
           finding:  {rule}

        """

    result = button_dialog(
        title=f" NaviScan:{object_type} ",
        text=action_msg,
        buttons=ok_cancel_buttons,
        style=default_dark_style
    ).run()

    return result

def build_options(data, headers, filters=None):
    rows = []

    if filters:
        # Original data format (list of objects)
        for item in data:
            row = tuple(getattr(item, f) for f in filters)
            rows.append(row)
    else:
        # New data format (list of dictionaries)
        for item in data:
            row = tuple(item[h] for h in headers)
            rows.append(row)

    header_widths = {
        header: max(len(str(r[i])) + 3 for r in rows + [headers])
        for i, header in enumerate(headers)
    }

    header = '   ' + '  '.join("{:<{width}}".format(h, width=header_widths[h]) for h in headers)
    line = '-' * len(header)

    _options_ = []
    for row in rows:
        row_data = [str(value) for value in row]
        formatted_row = ' ' + '  '.join("{:<{width}}".format(value, width=header_widths[header]) 
                for value, header in zip(row_data, headers)
        )
        _options_.append(formatted_row)

    return _options_, header

def build_options1(data, headers, filters):
    rows = []

    for item in data:
        row = tuple(getattr(item, f) for f in filters)
        rows.append(row)

    header_widths = {
        header: max(len(str(r[i])) + 3 for r in rows + [headers])
        for i, header in enumerate(headers)
    }

    header = '   ' + '  '.join("{:<{width}}".format(h, width=header_widths[h]) for h in headers)
    line = '-' * len(header)

    _options_ = []
    for row in rows:
        row_data = [str(value) for value in row]
        formatted_row = ' ' + '  '.join("{:<{width}}".format(value, width=header_widths[header]) 
                for value, header in zip(row_data, headers)
        )
        _options_.append(formatted_row)

    return _options_, header


def list_files(scan_dir:str) -> list:
    return [file for file in os.listdir(scan_dir)]

def normalize(
    header, 
    color:str='green', 
    msg:str=False, 
    show_banner=True, 
    random_banner_enabled=False,
    keep_banner = False,
    size=104, 
    clean=True
    ):

    if clean:
        print('\033[2J\033[1;1H')
        
    banner = 'default_naviban'

    if show_banner:
        if random_banner_enabled:
            if keep_banner:
                status='@s4dhulabs'
                banner = keep_banner
            else:
                banner = choice(banner_options)
                status='@s4dhu'

            banner = globals().get(banner)
            banner(cl(status,'blue'))
        else:
            default_naviban('')

    if not msg:
        msg ='O: Navigation Options'
    else:
        msg = f" {msg} / O: Navigation Options"
    
    fmsg = FormattedText([('ansibrightblack',f"{msg:>{size - 2}}")])
    print_formatted_text(fmsg)
    
    print("\u2500" * size)
    print(cl(header,color))
    print("\u2500" * size)
    
    try:
        return banner.__name__
    except AttributeError:
        return banner
    
def jazzit(header:str, app_dir:str, keep_banner:str=False):
    status = header[len(app_dir):]
    for c in range(len(status)):
        print('\033[2J\033[1;1H')

        if keep_banner:
            banner = globals().get(keep_banner)
            banner('')
        else:
            default_naviban()
        
        print()
        print("\u2500" * 104)
        print(cl(app_dir + status[:c+1],'green'))
        print("\u2500" * 104)
        sleep(0.01)

    normalize(
        header, 'green', False, True,
        True, keep_banner
    )

def getkey():
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    try:
        while True:
            b = os.read(sys.stdin.fileno(), 3).decode()
            if len(b) == 3:
                k = ord(b[2])
            else:
                k = ord(b)

            key_mapping = {
                51: 'delete',
                10: 'return',
                32: 'space',
                9: 'tab',
                27: 'esc',
                65: 'up',
                66: 'down',
                67: 'right',
                68: 'left',
                69: 'insert',
                70: 'end',
                72: 'home'
            }
            return key_mapping.get(k, chr(k))
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

class pager:
    def __init__(self, file_path=__file__):
        self.file_path = file_path
        self._initialize()

    def _initialize(self):
        if not os.path.exists(self.file_path):
            return False
        
        with open(self.file_path, "rb") as f:
            self.text = f.read().decode("utf-8")

        self.search_field = SearchToolbar(
            text_if_not_searching=[("class:not-searching", "Press '/' to start searching.")]
        )

        self.text_area = TextArea(
            text=self.text,
            read_only=True,
            scrollbar=True,
            line_numbers=False,
            search_field=self.search_field,
            lexer=PygmentsLexer(JsonLexer),
        )

        self.root_container = HSplit(
            [
                Window(
                    content=FormattedTextControl(self._get_statusbar_text),
                    height=D.exact(1),
                    width=D.exact(0),
                    style="class:status",
                ),
                self.text_area,
                self.search_field,
            ]
        )

        self.bindings = KeyBindings()
        @self.bindings.add("c-c")
        @self.bindings.add("q")
        def _(event):
            "Quit."
            event.app.exit()

        self.style = Style.from_dict(
            {
                "status": "reverse",
                "status.position": "#aaaa00",
                "status.key": "#ffaa00",
                "not-searching": "#888888",
            }
        )

        self.application = Application(
            layout=Layout(self.root_container, focused_element=self.text_area),
            key_bindings=self.bindings,
            enable_page_navigation_bindings=True,
            mouse_support=True,
            style=None,
            full_screen=True,
        )

    def _get_statusbar_text(self):
        return [
            ("class:status", f"{self.file_path.split('/')[-1].split('.')[0]} - "),
            (
                "class:status.position",
                f"{self.text_area.document.cursor_position_row + 1}:{self.text_area.document.cursor_position_col + 1}",
            ),
            ("class:status", " - Press "),
            ("class:status.key", "Ctrl-C"),
            ("class:status", " to exit, "),
            ("class:status.key", "/"),
            ("class:status", " for searching."),
        ]

    def run(self):
        try:
            self.application.run()
        except AttributeError:
            return False
            

