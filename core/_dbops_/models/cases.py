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
from sqlalchemy.types import JSON

class VFCases(db.Model):
    __tablename__ = '_CASES_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    case_id = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    case_hash = db.Column(
        db.String(200),
        unique = True,
        nullable = False
    )
    case_name = db.Column(
        db.String(20),
        unique = False,
        nullable = False
    )
    case_target = db.Column(
        db.String(100),
        unique = False,
        nullable = False
    )
    case_date = db.Column(
        db.DateTime,
        nullable = False
    )
    case_plugin = db.Column(
        db.String(30),
        nullable = False
    ) 
    case_plugin_info = db.Column(
        db.String(100),
        nullable = False
    ) 
    case_plugin_type = db.Column(
        db.String(20),
        nullable = False
    )
    case_plugin_astt = db.Column(
        db.String(10),
        nullable = False
    )
    case_ns = db.Column(
        JSON,
        unique = False,
        nullable = False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<VFCases: case={self.case_id}>"

