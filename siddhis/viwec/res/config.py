import os
import hashlib

respath = os.path.dirname(__file__) 
usernames = open(respath + '/_users_.txt', 'r').readlines()
passwords = open(respath + '/_passwords_.txt', 'r').readlines()
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



