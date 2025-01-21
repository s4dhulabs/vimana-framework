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

from prompt_toolkit.styles import Style

banner_options = [
    'vmnfgalaxy', 'sample_mode', 'case_header', 
    'vmn05', 'sample_mode', 'default_naviban', 
    'rukmavimana', 'audit_report_banner', 'load'
]
cursor_options = ['⠿ ', '➤ ', '◍ ', '◎ ', '◉ ','❖ ', '✣ ', '⚈ ', '✺ ', '⯀ ', '/ ' ]

srandlexers = [
    'Ooc',
    'Dart',
    'Ioke',
    'Kotlin',
    'Vim', 
    'Rust',
    'Idris',
    'Puppet',
    'Moonscript',
    'Html',
    'AmbientTalk',
    'Logtalk',
    'Monkey',
    'Cirru',
    'Boa',
    'Befunge',
    'BrainFuck',
    'Bash',
    'Asc',
    'VBScript',
    'Perl6',
    'Mosel',
    'Lean',
    'Golo',
    'BBCode'
]

ok_cancel_buttons = [("OK", True), ("Cancel", False)]
default_dark_style = Style.from_dict(
    {
        "dialog": "bg:#000000",
        "dialog frame-label": "bg:#ffffff #000000",
        "dialog.body": "bg:#000000 #00ff00",
        "dialog shadow": "bg:#141414",
    }
)
menu_options = {
######################
# SCANS MANAGER
######################
'scans_main_menu':"""

         D  Decrease details
         F  Flush selected resource
         I  Increase details
         O  Show this options menu
         P  Enable resource preview 
         R  Repeat the selected scan
         S  Open SARIF file
         T  Show the scan tree structure
    Ctrl-Y  Change dashboard style (random)
    Ctrl-C  Exit Navigation Mode
     Enter  Select item 
       Esc  Back to the previous menu /or exit

""",
######################
# SIDDHIS MANAGER
######################
'plugins_main_menu':"""
         D  Decrease preview details
         I  Increase preview details  
         O  This options menu
         P  Enable resource preview 
         C  Configure plugin scope
         G  Show plugin guide (info, labs, examples, args)
         R  Run plugin (config scope)
    
     '/'    Enables search 
    Ctrl-Y  Change dashboard style (random)
     Enter  Select item 
     Esc    Back to the previous menu /or exit

""",
######################
# CASES MANAGER
######################
'cases_main_menu':"""

         C  Show case command line
         O  This options menu
         F  Flush selected case
         R  Run selected case
    Ctrl-Y  Change dashboard style (random)
    Ctrl-C  Exit Navigation Mode
    Enter   Select item
    Esc     Back to the previous menu /or exit

""",
######################
# DASHBOARD MAIN MENU
######################
'dash_main_menu':"""

         D  Decrease preview details
         F  Flush selected resource
         I  Increase preview details  
         O  Show this options menu
       Esc  Back to the previous menu /or exit
     Enter  Manage resource items  
    Ctrl-Y  Change dashboard style (random)
    Ctrl-H  Hide selected resource
    Ctrl-R  Reset dashboard to default
    Ctrl-C  Exit Navigation Mode


""",
######################
# SESSIONS MANAGER
######################
'sessions_main_menu':"""

         D  Decrease preview details
         F  Flush selected resource
         I  Increase preview details  
         O  This options menu
         P  Enable resource preview 
         L  Load selected session
    Ctrl-Y  Change dashboard style (random)
    Ctrl-C  Exit Navigation Mode
    Enter   Select item
    Esc     Back to the previous menu /or exit

""",
######################
# T00LS MANAGER
######################
'tools_main_menu':"""

         D  Decrease preview details
         I  Increase preview details  
         O  This options menu
         P  Enable resource preview 
    Ctrl-Y  Change dashboard style (random)
    Ctrl-C  Exit Navigation Mode
    Enter   Run selected tool
    Esc     Back to the previous menu /or exit

""",
######################
# T00LS MANAGER
######################
'collections_main_menu':"""

         R  Run tools against select collection
    Ctrl-Y  Change dashboard style (random)
    Ctrl-C  Exit Navigation Mode
    Enter   Show collection items
    Esc     Back to the previous menu /or exit

"""

}
