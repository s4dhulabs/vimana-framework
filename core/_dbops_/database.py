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
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(__name__)
    app.config["VFSP"] = f'{basedir}/db'
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.config['VFSP']}/vmnf.db"
    app.config['SECRET_KEY'] = "s0M3Sup3Rs3cR3tK3YbuTn0ts0mUchw3c0ulDn0th4ckW1tHvmnf"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSIONTYPE'] = "VFSManage"
    app.config['DEBUG'] = False
    app.config['VIMANASET'] = app
    db.init_app(app)
    app.app_context().push()
    
    if not os.path.exists(app.config["VFSP"]):
        os.makedirs(app.config["VFSP"])

    db.create_all()
    return app, db

app, db = create_app()

