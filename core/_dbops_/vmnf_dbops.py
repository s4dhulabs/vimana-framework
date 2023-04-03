from .models.sessions import VFSessions as VFS 
from .models.siddhis import Siddhis as VFSD
from .models.scans import VFScans

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
            '_SIDDHIS_' : VFSD,
            '_SESSIONS_': VFS,
            '_SCANS_'   : VFScans
        }
        self.create_db()
    
    def list_resource(self, _TABLE_, filters):
        if not self.table_exists(_TABLE_):
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
        vf_model = self.tbl_model[_MODEL_]

        try:
            num_rows_deleted = db.session.query(vf_model).delete()
            db.session.commit()
        except:
            db.session.rollback()
   
    def getall(self, _MODEL_):
        vf_model = self.tbl_model[_MODEL_]
        try:
            return vf_model.query.all()
        except exc.OperationalError as OE:
            handle_OpErr(str(OE.orig))

    def get_by_id(self, _MODEL_, obj_id_col, obj_id):
        if not self.table_exists(_MODEL_):
            handle_OpErr('no such table:')

        vf_model = self.tbl_model[_MODEL_]
        model_attr = getattr(vf_model, obj_id_col)
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

