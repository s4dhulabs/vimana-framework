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

class VFSpecs(db.Model):
    __tablename__ = '_SPECS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    spec_id = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    spec_title = db.Column(
        db.String(200),
        unique = False,
        nullable = True
    )
    fastapi_version = db.Column(
        db.String(15),
        unique = False,
        nullable = True
    )
    openapi_version = db.Column(
        db.String(15),
        unique = False,
        nullable = True
    )
    spec_host = db.Column(
        db.String(100),
        unique = False,
        nullable = False
    )
    spec_paths = db.Column(
        db.String(200),
        unique = False,
        nullable = False
    )
    spec_methods = db.Column(
        db.String(50),
        nullable = False
    ) 
    spec_file_path = db.Column(
        db.String(200),
        nullable = False
    ) 
    spec_date = db.Column(
        db.DateTime,
        nullable = False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<VFSpecs: spec={self.spec_id}>"

