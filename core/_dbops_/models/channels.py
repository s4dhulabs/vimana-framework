from sqlalchemy import Column, String, DateTime, Text, JSON
from core._dbops_.database import db
from datetime import datetime, timezone

class VFChannels(db.Model):
    __tablename__ = '_CHANNELS_'
    channel_id = Column(String(16), primary_key=True, unique=True, nullable=False)
    type = Column(String(32), nullable=False)
    plugin = Column(String(32), nullable=False)
    target_url = Column(String(256), nullable=False)
    endpoint = Column(String(256), nullable=False)
    method = Column(String(16), nullable=False)
    payload_template = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_verified = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(32), default='active')
    channel_metadata = Column(JSON, nullable=True)