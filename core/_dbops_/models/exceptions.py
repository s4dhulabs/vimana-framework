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

class VFExceptions(db.Model):
    __tablename__ = '_EXCEPTIONS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    scan_id = db.Column(
        db.String(30),
        unique = False,
        nullable = False
    )
    scan_plugin = db.Column(
        db.String(30),
        unique = False,
        nullable = False
    )
    exception_id = db.Column(
        db.String(30),
        unique = False,
        nullable = False
    )
    exception_type = db.Column(
        db.String(30),
        unique = False,
        nullable = False
    )
    exception_class = db.Column(
        db.String(30),
        unique = False,
        nullable = True
    )
    module = db.Column(
        db.String(200),
        unique = False,
        nullable = True
    )
    module_object = db.Column(
        db.String(100),
        nullable = False
    ) 
    line_number = db.Column(
        db.String(10),
        nullable = True
    ) 
    trigger = db.Column(
        db.String(100),
        nullable = False
    ) 
    method = db.Column(
        db.String(7),
        unique = False,
        nullable = False
    )
    framework = db.Column(
        db.String(20),
        unique = False,
        nullable = True
    )
    framework_version = db.Column(
        db.String(10),
        unique = False,
        nullable = True
    )
    exception_meta = db.Column(
        JSON,
        unique = False,
        nullable = True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<VFX: xid={self.exception_id}@{self.scan_id}>"

