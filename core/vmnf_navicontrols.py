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

from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit import print_formatted_text
from prompt_toolkit.shortcuts import print_container,button_dialog
from prompt_toolkit.widgets import Frame, TextArea, Box, SearchToolbar
from prompt_toolkit.styles import Style


from pygments.lexers import JsonLexer
from pygments.lexers.python import PythonLexer
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.lexers import PygmentsLexer

from neotermcolor import cprint,colored as cl
from res.vmnf_banners import case_header
from time import sleep
import os

import termios
import sys
import tty

ok_cancel_buttons = [("OK", True), ("Cancel", False)]
default_dark_style = Style.from_dict(
    {
        "dialog": "bg:#000000",
        "dialog frame-label": "bg:#ffffff #000000",
        "dialog.body": "bg:#000000 #00ff00",
        "dialog shadow": "bg:#141414",
    }
)


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

def navioptions_menu():
    print('\033[2J\033[1;1H')
    case_header()
    print()

    txt_menu = """
    Enter      Select item 
    Ctrl-O     This options menu
    Ctrl-D     Delete the selected item
    Ctrl-C     Exit Navigation Mode
    Ctrl-T     Shows the scan tree structure
    Ctrl-R     Repeat the selected scan
    Alt-S      Open SARIF file results
    Esc        Back to the previous menu /or exit
    """
    print_container(
        Box(Frame(
            TextArea(text=txt_menu),
                title='Navigation Options',width=60
            ),
            padding_left=0,
            padding_top=0,
            padding_bottom=1
        )
    )
    input()

def naviscan_delete(scan):
    action_msg = f'''
    You're about to remove the scan below:
      
        object:  {scan}
            id:  {scan.scan_id}
          type:  {scan.scan_type}
       project:  {scan.scan_target_project} ({scan.project_framework} {scan.project_framework_version})
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

def list_files(scan_dir:str) -> list:
    return [file for file in os.listdir(scan_dir)]

def normalize(header,color:str='green', msg:str=False):
    print('\033[2J\033[1;1H')
    case_header()
    
    if not msg:
        msg ='Ctrl-O: Navigation Options'
    
    fmsg = FormattedText([('ansibrightblack',f"{msg:>104}")])
    print_formatted_text(fmsg)
    
    print("\u2500" * 104)
    print(cl(header,color))
    print("\u2500" * 104)
    
def jazzit(header:str,app_dir:str):
    status = header[len(app_dir):]
    for c in range(len(status)):
        print('\033[2J\033[1;1H')
        case_header()
        print()
        print("\u2500" * 104)
        print(cl(app_dir + status[:c+1],'green'))
        print("\u2500" * 104)
        sleep(0.01)
    normalize(header)




class pager:
    def __init__(self, file_path=__file__):
        self.file_path = file_path
        self._initialize()

    def _initialize(self):
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
        self.application.run()

