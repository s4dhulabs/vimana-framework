from ..config import db
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType
from sqlalchemy.types import JSON



class Siddhis(db.Model):
    __tablename__ = '_SIDDHIS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    name = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    author = db.Column(
        db.String(100),
        unique = False,
        nullable = False
    )
    brief = db.Column(
        db.String(100),
        unique = True,
        nullable = False
    )
    category = db.Column(
        db.String(30),
        unique = False,
        nullable = False
    )
    framework = db.Column(
        db.String(50),
        unique = False,
        nullable = False
    )
    info = db.Column(
        db.String(100),
        unique = False,
        nullable = False
    )
    module = db.Column(
        db.String(50),
        unique = True,
        nullable = False
    )
    package = db.Column(
        db.String(50),
        unique = False,
        nullable = True
    )
    type = db.Column(
        db.String(30),
        unique = False,
        nullable = False
    )
    tags = db.Column(
        JSON,
        unique = False,
        nullable = False
    )
    description = db.Column(
        db.String(1000),
        unique = True,
        nullable = False
    )
    references = db.Column(
        JSON,
        unique = False,
        nullable = False
    )
    guide = db.Column(
        JSON,
        unique = True,
        nullable = False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"successfully created!"

