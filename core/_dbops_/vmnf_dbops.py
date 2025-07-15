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

from .models.specs import VFSpecs as VFSpecs
from .models.exceptions import VFExceptions as VFX
from .models.sessions import VFSessions as VFS 
from .models.siddhis import Siddhis as VFSD
from .models.tools import Tools as VFTools
from .models.scans import VFScans
from .models.cases import VFCases
from .models.envs import VFEnvs
from .models.channels import VFChannels as VFChannels

from sqlalchemy_utils.functions import database_exists as db_exists
from .db_utils import filter_ops, handle_OpErr,get_filter_clauses
from neotermcolor import cprint,colored as cl
from res.vmnf_banners import case_header
from sqlalchemy import func,exc,inspect
from datetime import datetime as dt
from sqlalchemy import or_, and_
from .database import db, app
import sqlite3
import sys
import os


class VFDBOps:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.session = self.vmnf_handler.get('_session_',False)
        self.tbl_model = {
            '_EXCEPTIONS_': VFX,
            '_SIDDHIS_' : VFSD,
            '_SESSIONS_': VFS,
            '_SCANS_'   : VFScans,
            '_CASES_'   : VFCases,
            '_TOOLS_'   : VFTools,
            '_SPECS_'   : VFSpecs,
            '_ENVS_'    : VFEnvs,
            '_CHANNELS_': VFChannels
        }
        self.create_db()
    
    def get_model_dict(self, model):
        return {c.name: False for c in inspect(self.tbl_model[model.upper()]).columns if c.name != 'index'}

    def list_resource(self, _TABLE_, filters):
        
        if not self.table_exists(_TABLE_):
            if _TABLE_ != '_SIDDHIS_':
                return False

            handle_OpErr('no such table:')

        vf_model = self.tbl_model[_TABLE_]
        query = db.session.query(vf_model)
        filter_clauses = get_filter_clauses(vf_model,filters)
        query = query.filter(*filter_clauses)

        return query.all()

    def create_table(self, vf_model):
        try:
            vf_model.__table__.drop(db.engine)
        except exc.OperationalError as OE:
            pass

        vf_model.__table__.create(db.engine)

    def table_exists(self,_TABLE_):
        if inspect(db.engine).has_table(_TABLE_):
            return True
        return False

    def clean_table(self, _MODEL_):
        try:
            vf_model = self.tbl_model[_MODEL_]
        except KeyError:
            return False

        try:
            num_rows_deleted = db.session.query(vf_model).delete()
            db.session.commit()
        except:
            db.session.rollback()
            return False

        return True
   
    def getall(self, _MODEL_):
        vf_model = self.tbl_model[_MODEL_]

        try:
            return vf_model.query.all()
        except exc.OperationalError as OE:
            handle_OpErr(str(OE.orig))

    def get_by_id(self, _MODEL_, obj_id_col, obj_id, getall:bool=False):
        vf_model = self.tbl_model[_MODEL_]

        if not self.table_exists(_MODEL_):
            # plugins should be loaded with load --plugins
            if _MODEL_ not in ['_SIDDHIS_']:
                self.create_table(vf_model)
                # id doesn't exist 
                return False

            handle_OpErr('no such table:')

        model_attr = getattr(vf_model, obj_id_col)

        if getall:
            return vf_model.query.filter(model_attr==obj_id).all()
        return vf_model.query.filter(model_attr==obj_id).first()

    def flush_resource(self, _TABLE_, obj_id_col, obj_id):
        vf_model = self.tbl_model[_TABLE_]
        model_attr = getattr(vf_model, obj_id_col)
        flush_obj = db.session.query(vf_model).filter(model_attr==obj_id).first()

        if flush_obj:
            db.session.delete(flush_obj)
            db.session.commit()
            return flush_obj

        return False

    def commit(self,entry):
        db.session.add(entry)
        db.session.commit()

    def clean_db(self):
        db.drop_all()

    def create_db(self):
        if not db_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
            db.create_all()

            if self.vmnf_handler.get('debug', False):
                print(f'[{dt.now()}] DB sucessfully created!')

    def register(self,_TABLE_):
        vf_model = self.tbl_model[_TABLE_]

        if not self.table_exists(_TABLE_):
            self.create_table(vf_model)
        
        # session is stored in a dedicate object due to some adaptation
        if _TABLE_ == '_SESSIONS_':
            self.vmnf_handler = self.session

        self.commit(vf_model(**self.vmnf_handler))

    def list_db(self):
        """
        List all tables and their columns/types in the Vimana database.
        """
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        if not tables:
            print(cl("No tables found in the database.", "red"))
            return
        for table in tables:
            print(cl(f"\nTable: {table}", "cyan", attrs=["bold"]))
            columns = inspector.get_columns(table)
            for col in columns:
                col_name = col['name']
                col_type = str(col['type'])
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                print(f"    {col_name}  {col_type}  {nullable}")

    def integrity_check(self):
        """
        Run a database integrity check (currently supports SQLite).
        If debug or verbose is enabled, print detailed process info.
        """
        engine_name = db.engine.name.lower()
        verbose = (self.vmnf_handler.get('debug') or 
                  self.vmnf_handler.get('verbose') or 
                  '--verbose' in self.vmnf_handler.get('args', []))

        if engine_name == 'sqlite':
            conn = db.engine.raw_connection()
            try:
                cursor = conn.cursor()
                if verbose:
                    print(cl(f"[DEBUG] Starting integrity check for backend: {engine_name}", "yellow"))
                    print(cl("[DEBUG] Executing SQL: PRAGMA integrity_check;", "yellow"))
                cursor.execute("PRAGMA integrity_check;")
                results = cursor.fetchall()
                if verbose:
                    print(cl(f"[DEBUG] Raw result(s): {results}", "yellow"))
                if results and results[0][0] == 'ok':
                    print(cl("[OK] Database integrity check passed.", "green", attrs=["bold"]))
                else:
                    print(cl("[FAIL] Database integrity check failed:", "red", attrs=["bold"]))
                    for row in results:
                        print(cl(str(row[0]), "red"))
            finally:
                conn.close()
        else:
            print(cl(f"Integrity check not implemented for backend: {engine_name}", "yellow"))

