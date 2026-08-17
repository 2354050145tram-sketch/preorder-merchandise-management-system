from sqlalchemy import Column, Boolean, DateTime
from config import db
from datetime import datetime, timezone

class BaseModel(db.Model):
    __abstract__ = True

    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

