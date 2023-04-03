from ..database import db


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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"<VFAnalysis: session={self.scan_id}>"

