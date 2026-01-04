#!/usr/bin/env python
"""
A simple example of a few buttons and click handlers.
"""
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout import HSplit, Layout, VSplit
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea
from prompt_toolkit.keys import Keys


class navi_siddhi_guide:
    def __init__(self, plugin):
        self.plugin = plugin
        self.guide = plugin.guide

    def show_args(self):
        args = self.guide['args']
        self.text_area.text = "\n".join(" " + line for line in args.split('\n'))

    def show_examples(self):
        args = self.guide['examples']
        self.text_area.text = "\n".join(" " + line for line in args.split('\n'))

    def show_labs(self):
        args = self.guide['lab_setup']
        self.text_area.text = "\n".join(" " + line for line in args.split('\n'))

    def show_info(self):
        tags = f"\n* Tags: {','.join(self.plugin.tags)}"
        brief = "{{ " + self.plugin.brief + " }}\n\n"
        info = brief + self.plugin.description + tags
        self.text_area.text = "\n".join(" " + line for line in info.split('\n'))

    def exit(self):
        get_app().exit()

    def manage(self):
        self.text_area = TextArea(focusable=True)
        args_button = Button("Args", handler=self.show_args,right_symbol='', left_symbol='◉')
        refs_button = Button("Refs", handler=self.show_examples,right_symbol='', left_symbol='◎')
        labs_button = Button("Labs", handler=self.show_labs,right_symbol='', left_symbol='◍')
        info_button = Button("Info", handler=self.show_info,right_symbol='', left_symbol='❖')
        exit_button= Button("Exit", handler=self.exit,right_symbol='', left_symbol='⠗')
        
        root_container = Box(
            HSplit(
                [
                    Label(text="Press `Tab` to select"),
                    VSplit(
                        [
                            Box(
                                body=HSplit([args_button, refs_button, labs_button, info_button, exit_button], padding=1),
                                padding=1,
                                style="class:left-pane",
                            ),
                            Box(body=Frame(self.text_area), padding=1, style="class:right-pane"),
                        ]
                    ),
                ]
            ),
        )

        layout = Layout(container=root_container, focused_element=args_button)
        kb = KeyBindings()
        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        style = Style(
            [
                ("left-pane", "bg:#42eb00 #000000"),
                ("right-pane", "bg:#000000 #42eb00"),
                ("button", "#000000"),
                ("button-arrow", "#000000"),
                ("button focused", "bg:#000000"),
                ("text-area focused", "bg:#000000 #000000"),
            ]
        )

        vf_naviguide = Application(layout=layout, key_bindings=kb, style=style, full_screen=True)
        vf_naviguide.run()

