import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["VFSP"] = f'{basedir}/db'
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{app.config['VFSP']}/vmnf.db"
app.config['SECRET_KEY'] = "s0M3Sup3Rs3cR3tK3YbuTn0ts0mUchw3c0ulDn0th4ckW1tHvmnf"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSIONTYPE'] = "VFSManage"
app.config['DEBUG'] = False
app.config['VIMANASET'] = app
db = SQLAlchemy(app)
db.init_app(app)

