from ..config import db


class Siddhis(db.Model):
    __tablename__ = '_SIDDHIS_'

    id = db.Column(
        'index', 
        db.Integer, 
        primary_key = True
    )
    _name_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _acronym_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _category_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _framework_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _type_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _module_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _author_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _brief_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )
    _description_ = db.Column(
        db.String(30),
        unique = True,
        nullable = False
    )


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return f"Session {self.session_id} successfully created!"

