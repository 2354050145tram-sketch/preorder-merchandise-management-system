from sqlalchemy import Integer, Column, String, Boolean, DateTime, Enum, ForeignKey
from config import db
from datetime import datetime, timezone
from modules.base_model import BaseModel

class Role(BaseModel):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)

    users = db.relationship("User", back_populates="role")

    def __str__(self):
        return self.name


class User(BaseModel):
    __tablename__="users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    provider = Column(Enum("LOCAL", "FACEBOOK", "GOOGLE", "INSTAGRAM", "X"), nullable=False, default="LOCAL")
    provider_user_id = Column(String(255), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)

    role = db.relationship("Role", back_populates="users")
    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user")
    wallet = db.relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    user_notifications = db.relationship("UserNotification", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return self.username

class Profile(db.Model):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    full_name = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    phone_num = Column(String(10), nullable=False)
    address = Column(String(255), nullable=False)
    background_music = Column(String(255), nullable=True)

    user = db.relationship("User", back_populates="profile")