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

class VFScans(db.Model):
    __tablename__ = '_SCANS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    scan_id = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    scan_type = db.Column(
        db.String(30),
        unique = False,
        nullable = True
    )
    scan_date = db.Column(
        db.DateTime,
        unique = True,
        nullable = False
    )
    scan_hash = db.Column(
        db.String(200),
        unique = True,
        nullable = False
    )
    scan_target_project = db.Column(
        db.String(100),
        nullable = False
    ) 
    scan_target_full_path = db.Column(
        db.String(300),
        nullable = False
    ) 
    scan_cache_dir = db.Column(
        db.String(300),
        nullable = False
    ) 
    scan_output_file = db.Column(
        db.String(200),
        unique = True,
        nullable = False
    )
    project_framework = db.Column(
        db.String(30),
        unique = False,
        nullable = True
    )
    project_framework_version = db.Column(
        db.String(10),
        unique = False,
        nullable = True
    )
    project_framework_total_cves = db.Column(
        db.String(10),
        unique = False,
        nullable = True
    )
    project_total_requirements = db.Column(
        db.Integer,
        nullable = False
    ) 
    project_total_view_modules = db.Column(
        db.Integer,
        nullable = False
    )
    scan_scope = db.Column(
        JSON,
        unique = False,
        nullable = False
    )
    scan_plugin = db.Column(
        db.String(20),
        unique = False,
        nullable = True
    )
    vmnf_handler = db.Column(
        JSON,
        unique = False,
        nullable = False
    )
    plugin_instance = db.Column(
        JSON,
        unique = False,
        nullable = False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<VFScans: scan_id={self.scan_id}>"

