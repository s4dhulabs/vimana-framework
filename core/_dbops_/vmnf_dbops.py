from sqlalchemy_utils.functions import database_exists as db_exists
from .models.sessions import VFSessions as VFS
from sqlalchemy_filters import apply_filters
from .models.siddhis import Siddhis as VFSD
from res.vmnf_banners import case_header
from datetime import datetime as dt
from sqlalchemy import or_, and_
from sqlalchemy import func,exc,inspect
from neotermcolor import cprint
from .config import db, app
import os


def x():
    print('in x')

class VFSiddhis:
    def __init__(self, **siddhi_specs:dict):
        self.siddhi_specs = siddhi_specs

    def commit(self,entry):
        db.session.add(entry)
        db.session.commit()
    
    def register_siddhi(self):
        if not inspect(db.engine).has_table("_SIDDHIS_"):
            self.create_siddhi_tbl()

        self.commit(VFSD(**self.siddhi_specs)) 

    def handle_OpErr(self, exception):
        if (str(exception.orig)).startswith('no such table:'):
            case_header()
            cprint("[vf:list] It seems like you haven't populated the database yet.\n", 'yellow')
            os._exit(os.EX_OK)

    def list_siddhis_db(self, filters:list):
        try:
            return (apply_filters(db.session.query(VFSD), filters).all())
        except exc.OperationalError as OE:
            self.handle_OpErr(OE)
    
    def get_siddhi(self, siddhi_name):
        try:
            return VFSD.query.filter_by(name=siddhi_name.lower()).first()
        except exc.OperationalError as OE:
            self.handle_OpErr(OE)

    def get_all_siddhis(self):
        return VFSD.query.all()
    
    def create_siddhi_tbl(self):
        try:
            VFSD.__table__.drop(db.engine)
        except exc.OperationalError as OE:
            pass

        VFSD.__table__.create(db.engine)

class VFDBOps:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler
        self.session = self.vmnf_handler.get('_session_',False)
        self.create_db()

    def clean_sessions_table(self):
        try:
            num_rows_deleted = db.session.query(VFS).delete()
            db.session.commit()
        except:
            db.session.rollback()

    def flush_all_sessions_sbsidnw(self):
        [self.flush_session(_s_.session_id) \
            for _s_ in self.get_all_sessions()]

    def flush_session(self, _sid_):
        if not self.get_session(_sid_):
            return False

        flush_vfs = db.session.query(VFS).filter(VFS.session_id==_sid_).first()
        db.session.delete(flush_vfs)
        db.session.commit()

        return flush_vfs

    def commit(self,entry):
        db.session.add(entry)
        db.session.commit()

    def clean_db(self):
        db.drop_all()

    def get_session(self,_sid_):
        return VFS.query.filter_by(session_id=_sid_).first()

    def get_all_sessions(self):
        try:
            return VFS.query.all()
        except exc.OperationalError as OE:
            self.create_db()

            return False
    
    def create_db(self):
        if not db_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
            db.create_all()

            if self.vmnf_handler.get('debug', False):
                print(f'[{dt.now()}] DB sucessfully created!')

    def register_session(self):
        if not self.session:
            print(f"[{dt.now()}] Missing session data")
            return False

        if not inspect(db.engine).has_table("_SESSIONS_"):
            self.create_sessions_tbl()

        if self.get_session(self.session['session_id']):
            print(f"[{dt.now()}] Session {data['session_id']} already exists!")
            return False
    
        self.commit(VFS(**self.session)) 

    def create_sessions_tbl(self):
        try:
            VFS.__table__.drop(db.engine)
        except exc.OperationalError as OE:
            pass

        VFS.__table__.create(db.engine)

