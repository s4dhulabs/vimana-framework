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

from ..database import db
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType
from sqlalchemy.types import JSON



class Tools(db.Model):
    __tablename__ = '_TOOLS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    name = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    full_name = db.Column(
        db.String(100),
        unique = True,
        nullable = True
    )
    brief = db.Column(
        db.String(100),
        unique = True,
        nullable = False
    )
    description = db.Column(
        db.String(1000),
        unique = True,
        nullable = False
    )
    type = db.Column(
        db.String(10),
        unique = False,
        nullable = False
    )
    scope = db.Column(
        JSON,
        unique = False,
        nullable = False
    )
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        #return f"successfully created!"
        return f"<VFTools: tool={self.name}>"


