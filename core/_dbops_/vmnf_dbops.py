from sqlalchemy_utils.functions import database_exists as db_exists
from .models.sessions import VFSessions as VFS
from .models.siddhis import Siddhis as VFSD
from .config import db, app

from datetime import datetime as dt


class VFSiddhis:
    def __init__(self, **vmnf_handler):
        self.vmnf_handler = vmnf_handler

    def register_siddhi(self,**data):
        if self.get_session(data['session_id']):
            if self.vmnf_handler.get('debug', False):
                print(f"[{dt.now()}] Session {data['session_id']} already exists!")
            return False
    
        self.commit(VFSD(**data)) 

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

    def get_session(self, _sid_):
        return VFS.query.filter_by(session_id=_sid_).first()

    def get_all_sessions(self):
        return VFS.query.all()
    
    def create_db(self):
        if not db_exists(app.config["SQLALCHEMY_DATABASE_URI"]):
            db.create_all()

            if self.vmnf_handler.get('debug', False):
                print(f'[{dt.now()}] DB sucessfully created!')

    def register_session(self):
        if not self.session:
            print(f"[{dt.now()}] Missing session data")
            return False

        if self.get_session(self.session['session_id']):
            print(f"[{dt.now()}] Session {data['session_id']} already exists!")
            return False
    
        self.commit(VFS(**self.session)) 



