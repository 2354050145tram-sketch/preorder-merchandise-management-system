from config import db
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from decimal import Decimal
from uuid import uuid4
import re
from werkzeug.security import generate_password_hash, check_password_hash
from modules.users.models import User, Profile
from modules.wallets.models import Wallet


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

            wallet = Wallet(user_id=user.user_id, balance=Decimal("0"))

            db.session.add(wallet)
            db.session.commit()

            return user

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def social_login(
        provider,
        provider_user_id,
        email=None,
        username=None,
        full_name=None,
        avatar=None,
    ):
        valid_providers = [
            "GOOGLE",
            "FACEBOOK",
            "INSTAGRAM",
            "X",
        ]

        if provider not in valid_providers:
            raise ValueError("Nhà cung cấp đăng nhập không hợp lệ")

        provider_user_id = str(provider_user_id).strip() if provider_user_id else ""

        if not provider_user_id:
            raise ValueError("Không lấy được thông tin tài khoản")

        stmt = select(User).where(
            User.provider == provider,
            User.provider_user_id == provider_user_id,
        )

        user = db.session.scalar(stmt)

        if user:
            if not user.active:
                raise ValueError("Tài khoản đã bị khóa")

            return user

        email = email.strip().lower() if email else None

        full_name = full_name.strip() if full_name else provider

        if email:
            existing_user = db.session.scalar(select(User).where(User.email == email))

            if existing_user:
                raise ValueError("Email này đã được sử dụng bởi " "một tài khoản khác")

        base_username = username.strip() if username else provider.lower()

        generated_username = base_username

        while db.session.scalar(
            select(User).where(User.username == generated_username)
        ):
            generated_username = f"{base_username}_" f"{uuid4().hex[:6]}"

        if not email:
            email = f"{provider.lower()}_" f"{uuid4().hex}" "@social.verdia.local"

        random_password = generate_password_hash(uuid4().hex)

        user = User(
            email=email,
            username=generated_username,
            password=random_password,
            provider=provider,
            provider_user_id=provider_user_id,
            role_id=1,
        )

        try:
            db.session.add(user)

            db.session.flush()

            profile = Profile(
                user_id=user.user_id,
                full_name=full_name,
                avatar=avatar,
                phone_num=None,
                address=None,
            )

            db.session.add(profile)

            wallet = Wallet(
                user_id=user.user_id,
                balance=Decimal("0"),
            )

            db.session.add(wallet)

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

        if user.provider != "LOCAL":
            raise ValueError(
                "Tài khoản đăng nhập bằng "
                "bên thứ ba không sử dụng "
                "mật khẩu Verdia"
            )

        if not old_password or not new_password:
            raise ValueError("Mật khẩu không được để trống")

        if not check_password_hash(user.password, old_password):
            raise ValueError("Mật khẩu cũ không đúng")

        PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d).{8,}$"

        if not re.match(PASSWORD_REGEX, new_password):
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự, " "bao gồm chữ và số")

        if check_password_hash(user.password, new_password):
            raise ValueError("Mật khẩu mới không được trùng mật khẩu cũ")

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

        if "full_name" in data and data["full_name"]:
            profile.full_name = data["full_name"].strip()

        if "phone_num" in data and data["phone_num"]:
            phone_num = data["phone_num"].strip()

            PHONE_REGEX = r"^0\d{9}$"

            if not re.match(PHONE_REGEX, phone_num):
                raise ValueError("Số điện thoại không hợp lệ")

            UserService.check_duplicate(phone_num=phone_num, exclude_user_id=user_id)

            profile.phone_num = phone_num

        if "address" in data and data["address"]:
            profile.address = data["address"].strip()

        if "avatar" in data:
            profile.avatar = data["avatar"].strip() if data["avatar"] else None

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

    @staticmethod
    def get_all_users_admin():
        stmt = (
            select(User)
            .options(
                selectinload(User.wallet),
                selectinload(User.orders),
            )
            .order_by(User.user_id.desc())
        )
        return db.session.scalars(stmt).all()

    @staticmethod
    def get_user_detail_admin(user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("Người dùng không tồn tại")
        return user

    @staticmethod
    def toggle_user_status(user_id, active_status):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("Người dùng không tồn tại")

        if user.role_id == 0:
            raise ValueError("Không thể thay đổi trạng thái tài khoản Quản trị viên")

        user.active = bool(active_status)
        try:
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise
