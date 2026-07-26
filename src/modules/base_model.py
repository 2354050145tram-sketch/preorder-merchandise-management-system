from sqlalchemy import Integer, Column, String, Boolean, DateTime, Enum, ForeignKey
from config import db
from datetime import datetime, timezone

class BaseModel(db.Model):
    __abstract__ = True

    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))

