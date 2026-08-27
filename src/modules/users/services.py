from config import db
from sqlalchemy import select, or_
import re
from werkzeug.security import generate_password_hash, check_password_hash
from modules.users.models import User, Profile


class UserService:

    @staticmethod
    def check_duplicate(
        email=None, username=None, phone_num=None, exclude_user_id=None
    ):

        if email:
            stmt = select(User).where(User.email == email)

            if exclude_user_id is not None:
                stmt = stmt.where(User.user_id != exclude_user_id)

            if db.session.scalar(stmt):
                raise ValueError("Email đã tồn tại")

        if username:
            stmt = select(User).where(User.username == username)

            if exclude_user_id is not None:
                stmt = stmt.where(User.user_id != exclude_user_id)

            if db.session.scalar(stmt):
                raise ValueError("Tên đăng nhập đã tồn tại")

        if phone_num:
            stmt = select(Profile).where(Profile.phone_num == phone_num)

            if exclude_user_id is not None:
                stmt = stmt.where(Profile.user_id != exclude_user_id)

            if db.session.scalar(stmt):
                raise ValueError("Số điện thoại đã tồn tại")

    @staticmethod
    def register(
        email, username, password, confirm_password, full_name, phone_num, address
    ):
        email = email.strip() if email else ""
        username = username.strip() if username else ""
        full_name = full_name.strip() if full_name else ""
        phone_num = phone_num.strip() if phone_num else ""
        address = address.strip() if address else ""

        if not all(
            [email, username, password, confirm_password, full_name, phone_num, address]
        ):
            raise ValueError("Thông tin không được để trống")

        EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.match(EMAIL_REGEX, email):
            raise ValueError("Email không hợp lệ")

        PHONE_REGEX = r"^0\d{9}$"

        if not re.match(PHONE_REGEX, phone_num):
            raise ValueError("Số điện thoại không hợp lệ")

        PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d).{8,}$"

        if not re.match(PASSWORD_REGEX, password):
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ và số")

        if password != confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp")

        # Kiểm tra trùng
        UserService.check_duplicate(email=email, username=username, phone_num=phone_num)

        user = User(
            email=email,
            username=username,
            password=generate_password_hash(password),
            provider="LOCAL",
            role_id=1,
        )

        try:

            db.session.add(user)
            db.session.flush()

            profile = Profile(
                user_id=user.user_id,
                full_name=full_name,
                phone_num=phone_num,
                address=address,
            )

            db.session.add(profile)
            db.session.commit()

            return user

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def login(login, password):
        login = login.strip() if login else ""

        if not login or not password:
            raise ValueError("Thông tin đăng nhập không được để trống")

        user = (
            User.query.join(Profile)
            .filter(
                User.provider == "LOCAL",
                User.active.is_(True),
                or_(
                    User.email == login,
                    User.username == login,
                    Profile.phone_num == login,
                ),
            )
            .first()
        )

        if not user:
            raise ValueError("Sai tên đăng nhập hoặc mật khẩu")

        if not check_password_hash(user.password, password):
            raise ValueError("Sai tên đăng nhập hoặc mật khẩu")

        return user

    @staticmethod
    def change_password(user_id, old_password, new_password):
        user = db.session.get(User, user_id)
        if not user or not user.active:
            raise ValueError("User không tồn tại")

        if not old_password or not new_password:
            raise ValueError("Mật khẩu không được để trống")

        # kiểm tra mật khẩu cũ
        if not check_password_hash(user.password, old_password):
            raise ValueError("Mật khẩu cũ không đúng")

        PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d).{8,}$"

        if not re.match(PASSWORD_REGEX, new_password):
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự, " "bao gồm chữ và số")

        if check_password_hash(user.password, new_password):
            raise ValueError("Mật khẩu mới không được trùng mật khẩu cũ")

        # hash mật khẩu mới
        user.password = generate_password_hash(new_password)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_user_by_id(user_id, active=None):
        user = db.session.get(User, user_id)

        if not user:
            raise ValueError("User không tồn tại")

        if active is not None and user.active != active:
            raise ValueError("User không tồn tại")

        return user

    @staticmethod
    def get_all_users(active=None):
        stmt = select(User)

        if active is not None:
            stmt = stmt.where(User.active == active)

        return db.session.scalars(stmt).all()

    @staticmethod
    def update_profile(user_id, data):
        stmt = select(Profile).where(Profile.user_id == user_id)

        profile = db.session.scalar(stmt)

        if not profile:
            raise ValueError("Profile không tồn tại")

        # Cập nhật họ tên
        if "full_name" in data and data["full_name"]:
            profile.full_name = data["full_name"].strip()

        # Cập nhật số điện thoại
        if "phone_num" in data and data["phone_num"]:
            phone_num = data["phone_num"].strip()

            PHONE_REGEX = r"^0\d{9}$"

            if not re.match(PHONE_REGEX, phone_num):
                raise ValueError("Số điện thoại không hợp lệ")

            UserService.check_duplicate(phone_num=phone_num, exclude_user_id=user_id)

            profile.phone_num = phone_num

        # Cập nhật địa chỉ
        if "address" in data and data["address"]:
            profile.address = data["address"].strip()

        # Cập nhật avatar
        if "avatar" in data:
            profile.avatar = data["avatar"].strip() if data["avatar"] else None

        # Cập nhật nhạc nền
        if "background_music" in data:
            profile.background_music = (
                data["background_music"].strip() if data["background_music"] else None
            )

        try:
            db.session.commit()
            return profile

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_user(user_id):
        user = db.session.get(User, user_id)
        if not user or not user.active:
            raise ValueError("User không tồn tại")

        user.active = False

        try:
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def lock_user(user_id):
        user = db.session.get(User, user_id)
        if not user or not user.active:
            raise ValueError("User không tồn tại")

        user.active = False

        try:
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise
