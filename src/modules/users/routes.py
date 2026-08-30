import os
from flask import Blueprint, request, redirect, url_for, session
from modules.users.services import UserService
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from modules.users.oauth import google, facebook
from utils.helpers import response_success, response_error

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}

        user = UserService.register(
            email=data.get("email"),
            username=data.get("username"),
            password=data.get("password"),
            confirm_password=data.get("confirm_password"),
            full_name=data.get("full_name"),
            phone_num=data.get("phone_num"),
            address=data.get("address"),
        )

        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))

        return response_success(
            {
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            "Đăng ký thành công",
            201,
        )
    except ValueError as error:
        return response_error(str(error), 400)
    except Exception:
        return response_error("Có lỗi xảy ra khi đăng ký", 500)


@user_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        user = UserService.login(login=data.get("login"), password=data.get("password"))

        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))

        return response_success(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "role_id": user.role_id,
                },
            },
            "Đăng nhập thành công",
            200,
        )
    except ValueError as error:
        return response_error(str(error), 401)
    except Exception:
        return response_error("Có lỗi xảy ra khi đăng nhập", 500)


@user_bp.route("/auth/google", methods=["GET"])
def google_login():
    redirect_uri = url_for("users.google_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@user_bp.route("/auth/google/callback", methods=["GET"])
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get("userinfo")

        if not user_info:
            raise ValueError("Không lấy được thông tin Google")

        if not user_info.get("email_verified", False):
            raise ValueError("Email Google chưa được xác minh")

        user = UserService.social_login(
            provider="GOOGLE",
            provider_user_id=user_info.get("sub"),
            email=user_info.get("email"),
            username=None,
            full_name=user_info.get("name"),
            avatar=user_info.get("picture"),
        )

        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))

        session["oauth_access_token"] = access_token
        session["oauth_refresh_token"] = refresh_token

        return redirect("/products")
    except ValueError as error:
        return response_error(str(error), 400)
    except Exception:
        return response_error(
            "Có lỗi xảy ra khi đăng nhập Google",
            500,
        )


@user_bp.route("/oauth/session", methods=["GET"])
def get_oauth_session():
    access_token = session.pop("oauth_access_token", None)
    refresh_token = session.pop("oauth_refresh_token", None)

    if not access_token or not refresh_token:
        return response_error("Không có phiên đăng nhập OAuth", 401)

    return response_success(
        {"access_token": access_token, "refresh_token": refresh_token},
        "Đăng nhập OAuth thành công",
        200,
    )


@user_bp.route("/auth/facebook", methods=["GET"])
def facebook_login():
    redirect_uri = f"{os.getenv('PUBLIC_BASE_URL')}/api/users/auth/facebook/callback"
    return facebook.authorize_redirect(redirect_uri)


@user_bp.route("/auth/facebook/callback", methods=["GET"])
def facebook_callback():
    try:
        token = facebook.authorize_access_token()
        response = facebook.get("me?fields=id,name,email,picture")
        user_info = response.json()

        if not user_info.get("id"):
            raise ValueError("Không lấy được thông tin Facebook")

        email = user_info.get("email")
        if not email:
            raise ValueError("Không lấy được email Facebook")

        picture = user_info.get("picture", {}).get("data", {}).get("url")

        user = UserService.social_login(
            provider="FACEBOOK",
            provider_user_id=user_info.get("id"),
            email=email,
            username=None,
            full_name=user_info.get("name"),
            avatar=picture,
        )

        access_token = create_access_token(identity=str(user.user_id))
        refresh_token = create_refresh_token(identity=str(user.user_id))

        session["oauth_access_token"] = access_token
        session["oauth_refresh_token"] = refresh_token

        return redirect("/products")
    
    except ValueError as error:
        return response_error(str(error), 400)
    except Exception:
        return response_error(
            "Có lỗi xảy ra khi đăng nhập Facebook",
            500,
        )


@user_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        user_id = int(get_jwt_identity())
        UserService.get_user_by_id(user_id, active=True)
        new_access_token = create_access_token(identity=str(user_id))
        return response_success(
            {"access_token": new_access_token}, "Làm mới token thành công", 200
        )
    except ValueError as error:
        return response_error(str(error), 403)
    except Exception:
        return response_error("Có lỗi xảy ra khi làm mới token", 500)


@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        user_id = int(get_jwt_identity())
        user = UserService.get_user_by_id(user_id, active=True)
        return response_success(
            {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "profile": {
                    "full_name": user.profile.full_name if user.profile else None,
                    "phone_num": user.profile.phone_num if user.profile else None,
                    "address": user.profile.address if user.profile else None,
                    "avatar": user.profile.avatar if user.profile else None,
                },
            }
        )
    except ValueError as error:
        return response_error(str(error), 404)


@user_bp.route("/<int:user_id>/profile", methods=["PUT"])
@jwt_required()
def update_user_profile(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        if current_user_id != user_id:
            return response_error("Không có quyền sửa profile người khác", 403)

        UserService.get_user_by_id(user_id, active=True)
        data = request.get_json() or {}
        profile = UserService.update_profile(user_id, data)

        return response_success(
            {
                "full_name": profile.full_name,
                "phone_num": profile.phone_num,
                "address": profile.address,
                "avatar": profile.avatar,
            },
            "Cập nhật profile thành công",
            200,
        )
    except ValueError as error:
        return response_error(str(error), 400)
    except Exception:
        return response_error("Có lỗi xảy ra khi cập nhật profile", 500)


@user_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        UserService.change_password(
            user_id, data.get("old_password"), data.get("new_password")
        )
        return response_success({}, "Đổi mật khẩu thành công", 200)
    except ValueError as error:
        return response_error(str(error), 400)
    except Exception:
        return response_error("Có lỗi xảy ra khi đổi mật khẩu", 500)


@user_bp.route("/admin", methods=["GET"])
@jwt_required()
def get_admin_users():
    try:
        admin_id = int(get_jwt_identity())
        current_admin = UserService.get_user_by_id(admin_id, active=True)
        if current_admin.role_id != 0:
            return response_error("Không có quyền truy cập", 403)

        users = UserService.get_all_users_admin()
        user_list = []

        for u in users:
            wallet_bal = 0.0
            if u.wallet and u.wallet.balance is not None:
                wallet_bal = float(u.wallet.balance)

            orders_list = []
            if u.orders:
                orders_list = [{"order_id": o.order_id} for o in u.orders if o.active]

            user_list.append(
                {
                    "user_id": u.user_id,
                    "email": u.email,
                    "username": u.username,
                    "role_id": u.role_id,
                    "active": u.active,
                    "wallet_balance": wallet_bal,
                    "orders": orders_list,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
            )

        return response_success(
            {"users": user_list}, "Lấy danh sách người dùng thành công", 200
        )
    except PermissionError as error:
        return response_error(str(error), 403)
    except Exception as error:
        return response_error(f"Lỗi: {str(error)}", 500)


@user_bp.route("/admin/<int:user_id>", methods=["GET"])
@jwt_required()
def get_admin_user_detail(user_id):
    try:
        admin_id = int(get_jwt_identity())
        current_admin = UserService.get_user_by_id(admin_id, active=True)
        if current_admin.role_id != 0:
            return response_error("Không có quyền truy cập", 403)

        u = UserService.get_user_detail_admin(user_id)

        orders_data = []
        for o in getattr(u, "orders", []) or []:
            if getattr(o, "active", True):
                o_date = (
                    o.order_date.isoformat()
                    if getattr(o, "order_date", None)
                    else (
                        o.created_at.isoformat()
                        if getattr(o, "created_at", None)
                        else None
                    )
                )
                orders_data.append(
                    {
                        "order_id": o.order_id,
                        "order_date": str(o_date).split("T")[0] if o_date else None,
                        "total_amount": float(o.total_amount or 0.0),
                        "order_status": o.order_status,
                        "created_at": o_date,
                    }
                )

        wallet_trans_data = []
        if getattr(u, "wallet", None) and getattr(u.wallet, "transactions", None):
            for t in u.wallet.transactions:
                t_date = (
                    t.created_at.isoformat() if getattr(t, "created_at", None) else None
                )
                trans_id = (
                    getattr(t, "wallet_transaction_id", None)
                    or getattr(t, "transaction_id", None)
                    or getattr(t, "id", None)
                )
                wallet_trans_data.append(
                    {
                        "transaction_id": trans_id,
                        "transaction_type": t.transaction_type,
                        "amount": float(t.amount or 0.0),
                        "description": getattr(t, "description", None)
                        or getattr(t, "note", None)
                        or "—",
                        "created_at": t_date,
                    }
                )

        wallet_bal = (
            float(u.wallet.balance)
            if getattr(u, "wallet", None) and u.wallet.balance is not None
            else 0.0
        )

        user_detail = {
            "user_id": u.user_id,
            "email": u.email,
            "username": u.username,
            "role_id": u.role_id,
            "active": u.active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "wallet_balance": wallet_bal,
            "orders": orders_data,
            "wallet_transactions": wallet_trans_data,
        }

        return response_success(
            {"user": user_detail}, "Lấy chi tiết người dùng thành công", 200
        )
    except PermissionError as error:
        return response_error(str(error), 403)
    except ValueError as error:
        return response_error(str(error), 404)
    except Exception as error:
        return response_error(f"Lỗi: {str(error)}", 500)


@user_bp.route("/admin/<int:user_id>/status", methods=["PUT"])
@jwt_required()
def update_user_status(user_id):
    try:
        admin_id = int(get_jwt_identity())
        current_admin = UserService.get_user_by_id(admin_id, active=True)
        if current_admin.role_id != 0:
            return response_error("Không có quyền truy cập", 403)

        data = request.get_json() or {}
        active = data.get("active")
        if active is None:
            raise ValueError("Trạng thái không hợp lệ")

        user = UserService.toggle_user_status(user_id, active)
        action_text = "Mở khóa" if user.active else "Khóa"
        return response_success(
            {"user_id": user.user_id, "active": user.active},
            f"{action_text} tài khoản thành công",
            200,
        )
    except PermissionError as error:
        return response_error(str(error), 403)
    except ValueError as error:
        return response_error(str(error), 400)
    except Exception as error:
        return response_error(f"Lỗi: {str(error)}", 500)
