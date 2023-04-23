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


class VFSessions(db.Model):
    __tablename__ = '_SESSIONS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    session_id = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    session_hash = db.Column(
        db.String(200),
        unique = True,
        nullable = False
    )
    session_file = db.Column(
        db.String(20),
        unique = True,
        nullable = False
    )
    session_path = db.Column(
        db.String(40),
        unique = True,
        nullable = False
    )
    session_date = db.Column(
        db.DateTime,
        nullable = False
    )
    session_plugin = db.Column(
        db.String(30),
        nullable = False
    ) 
    session_target = db.Column(
        db.String(30),
        nullable = False
    ) 
    target_port = db.Column(
        db.String(20),
        nullable = False
    ) 
    target_url = db.Column(
        db.String(40),
        nullable = False
    )
    framework = db.Column(
        db.String(20),
        nullable = True
    )
    framework_version = db.Column(
        db.String(10),
        nullable = True
    )
    total_exceptions = db.Column(
        db.String(10),
        nullable = True
    )
    total_cves = db.Column(
        db.String(10),
        nullable = True
    )
    total_tickets = db.Column(
        db.String(10),
        nullable = True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<VFSession: session={self.session_id}>"

