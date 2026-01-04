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

class VFEnvs(db.Model):
    __tablename__ = '_ENVS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    env_id = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    env_name = db.Column(
        db.String(50),
        unique = True,
        nullable = True
    )
    env_description = db.Column(
        db.String(200),
        unique = False,
        nullable = True
    )
    env_file_path = db.Column(
        db.String(100),
        unique = False,
        nullable = True
    )
    env_data = db.Column(
        JSON,
        unique = False,
        nullable = False
    )
    env_date = db.Column(
        db.DateTime,
        nullable = False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<VFEnvs: env={self.env_id}>"

