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

import os
import hashlib
import pathlib

raw_path = '[vimana_path]/siddhis/jungle/res{}'
respath = os.path.dirname(__file__) 
user_file = '/_users_.txt'
pass_file = '/_passwords_.txt'
users_file_path = respath + user_file
pass_file_path = respath + pass_file
usernames = open(users_file_path, 'r').readlines()
passwords = open(pass_file_path, 'r').readlines()
userlen   = len(usernames)
passlen   = len(passwords)
pass_file_hash=hashlib.sha256(str(usernames).encode('utf-8')).hexdigest()[:25]
user_file_hash=hashlib.sha256(str(passwords).encode('utf-8')).hexdigest()[:25]
round_hash = str(userlen) + ':' + user_file_hash + ':' + str(passlen) + ':' + pass_file_hash 
logout_path = '/admin/logout/'
users_path =  '/admin/auth/user/'
add_users_path = users_path + '/add/'
admin_redir_path = '/admin/login/?next=/admin/'
login_ok = 'Welcome'
login_done_msg = 'Successfully authenticated with credential'
auth_kw='//div[@id="user-tools"]//text()'
logout_kw='Logout performed successfully'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0',
    'Referer': '',
    'Upgrade-Insecure-Requests': '1',
}



