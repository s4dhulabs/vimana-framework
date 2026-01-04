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
import curses

class PopupDisplay:
    def __init__(self, text):
        self.text = text

    def show_popup(self, stdscr):
        # Get the size of the terminal
        height, width = stdscr.getmaxyx()

        # Create a new window for the popup
        popup_height = 10
        popup_width = 50
        popup_y = (height - popup_height) // 2
        popup_x = (width - popup_width) // 2
        self.popup_win = curses.newwin(popup_height, popup_width, popup_y, popup_x)

        # Draw a border around the window
        self.popup_win.border()

        # Add the text to the window
        self.popup_win.addstr(1, 1, self.text)

        # Add a close instruction
        self.popup_win.addstr(popup_height - 2, 1, "Press 'x' to close")

        # Refresh the window to show the changes
        self.popup_win.refresh()

        # Wait for the user to press 'x' to close the popup
        while True:
            key = self.popup_win.getch()
            if key == ord('x'):
                break

        # Clear the popup window
        self.popup_win.clear()
        self.popup_win.refresh()

    def display_detailed_view(self):
        curses.wrapper(self.show_popup)
