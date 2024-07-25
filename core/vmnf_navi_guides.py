#!/usr/bin/env python

from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.widgets import Box, Button, Frame, Label, TextArea
from prompt_toolkit.layout import HSplit, Layout, VSplit
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.styles import Style
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

