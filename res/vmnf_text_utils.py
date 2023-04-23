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

import textwrap

def text_wrap(t,w):
    return textwrap.fill(t, w)

def format_text(text, m_len=120):
    ref_len = 0
    
    words = text.split(" ")
    formatted_text = ""
    for word in words:
        if ref_len + (len(word) + 1) <= m_len:
            formatted_text = formatted_text + word + " "
            ref_len = ref_len + len(word) + 1
        else:
            formatted_text = formatted_text + "\n" + word + " "
            ref_len = len(word) + 1

    return formatted_text
