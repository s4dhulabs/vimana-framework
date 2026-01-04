#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

# Change to web2py directory
os.chdir('web2py')

# Create a simple welcome application
if not os.path.exists('applications/welcome'):
    os.makedirs('applications/welcome')
    os.makedirs('applications/welcome/controllers')
    os.makedirs('applications/welcome/views/default')

# Create default controller
with open('applications/welcome/controllers/default.py', 'w') as f:
    f.write('''def index():
    return dict(message="Hello from Web2py!")

def about():
    return dict(message="About page")
''')

# Create default view
with open('applications/welcome/views/default/index.html', 'w') as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Web2py Welcome</title>
</head>
<body>
    <h1>{{=message}}</h1>
    <p>This is a minimal Web2py application for testing Framewalk.</p>
</body>
</html>
''')

# Create about view
with open('applications/welcome/views/default/about.html', 'w') as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
    <title>About - Web2py</title>
</head>
<body>
    <h1>{{=message}}</h1>
    <p>Web2py Framework Detection Test</p>
</body>
</html>
''')

# Create routes.py
with open('routes.py', 'w') as f:
    f.write('''# -*- coding: utf-8 -*-
# routes.py
# routes_in: (c,f) -> (controller,function)
# routes_out: (c,f,a) -> (controller,function,arguments)

routes_in = (
    ('/', '/welcome/default/index'),
    ('/about', '/welcome/default/about'),
)

routes_out = (
    ('/welcome/default/index', '/'),
    ('/welcome/default/about', '/about'),
)
''')

# Start web2py server
if __name__ == '__main__':
    # Use the standard web2py server
    os.system('python web2py.py -a "" -p 8080 -i 0.0.0.0') 