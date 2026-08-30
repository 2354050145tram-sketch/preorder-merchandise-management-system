from sqlalchemy import Integer, Column, String, ForeignKey, DateTime
from config import db
from datetime import datetime, timezone


class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    preorder_id = Column(Integer, ForeignKey("preorders.preorder_id"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(String(255), nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    preorder = db.relationship("PreOrder", back_populates="notifications")
    user_notifications = db.relationship(
        "UserNotification", back_populates="notification", cascade="all, delete-orphan"
    )


class UserNotification(db.Model):
    __tablename__ = "user_notifications"

    user_id = Column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    notification_id = Column(
        Integer,
        ForeignKey("notifications.notification_id", ondelete="CASCADE"),
        primary_key=True,
    )
    send_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", back_populates="user_notifications")
    notification = db.relationship("Notification", back_populates="user_notifications")
