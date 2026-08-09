from config import db
from sqlalchemy import or_
import re
from werkzeug.security import generate_password_hash, check_password_hash
from modules.users.models import User, Profile

class UserService:

    @staticmethod
    def register(email, username, password, confirm_password, full_name, phone_num, address):
        email = email.strip()
        username = username.strip()

        if not all([email, username, password, confirm_password, full_name, phone_num, address]):
            raise ValueError("Thông tin không được để trống")

        EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Email không hợp lệ")

        PHONE_REGEX = r'^0\d{9}$'

        if not re.match(PHONE_REGEX, phone_num):
            raise ValueError("Số điện thoại không hợp lệ")

        PASSWORD_REGEX = r'^(?=.*[A-Za-z])(?=.*\d).{8,}$'

        if not re.match(PASSWORD_REGEX, password):
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ và số")
        if password != confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp")

        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            raise ValueError("Tên đăng nhập đã tồn tại")

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise ValueError("Email đã tồn tại")

        existing_phone = Profile.query.filter_by(phone_num=phone_num).first()
        if existing_phone:
            raise ValueError("Số điện thoại đã tồn tại")

        user = User(
            email=email,
            username=username,
            password=generate_password_hash(password),
            provider="LOCAL",
            role_id=1
        )

        try:

            db.session.add(user)
            db.session.flush()

            profile = Profile(
                user_id=user.user_id,
                full_name=full_name.strip(),
                phone_num=phone_num.strp(),
                address=address.strip()
            )

            db.session.add(profile)
            db.session.commit()

            return user
        
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def login(login, password):
        login = login.strip()
        
        user = User.query.join(Profile).filter(
            User.provider == "LOCAL",
            User.active == True,
            or_(
                User.email == login,
                User.username == login,
                Profile.phone_num == login
            )
        ).first()

        if not user:
            raise ValueError("Sai tên đăng nhập hoặc mật khẩu")

        if not check_password_hash(user.password, password):
            raise ValueError("Sai tên đăng nhập hoặc mật khẩu")

        return user

    @staticmethod
    def change_password(user_id, old_password, new_password):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User không tồn tại")

        # kiểm tra mật khẩu cũ
        if not check_password_hash(user.password, old_password):
            raise ValueError("Mật khẩu cũ không đúng")

        # hash mật khẩu mới
        user.password = generate_password_hash(new_password)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_profile(user_id, data):
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            raise ValueError("Profile không tồn tại")

        profile.full_name = data.get("full_name", profile.full_name)
        profile.phone_num = data.get("phone_num", profile.phone_num)
        profile.address = data.get("address", profile.address)

        try:
            db.session.commit()
            return profile
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User không tồn tại")

        user.active = False

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def lock_user(user_id):
        user = User.query.get(user_id)

        if not user:
            raise ValueError("User không tồn tại")

        user.active = False

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
