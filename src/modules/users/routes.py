from flask import Blueprint, request
from modules.users.services import UserService
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
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
                },
            },
            "Đăng nhập thành công",
            200,
        )

    except ValueError as error:
        return response_error(str(error), 401)

    except Exception:
        return response_error("Có lỗi xảy ra khi đăng nhập", 500)


@user_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        user_id = int(get_jwt_identity())

        UserService.get_user_by_id(user_id, active=True)

        new_access_token = create_access_token(identity=str(user_id))

        return response_success({"access_token": new_access_token}), 200

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
                    "full_name": user.profile.full_name,
                    "phone_num": user.profile.phone_num,
                    "address": user.profile.address,
                    "avatar": user.profile.avatar,
                    "background_music": user.profile.background_music,
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
                "background_music": profile.background_music,
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

        old_pw = data.get("old_password")

        new_pw = data.get("new_password")

        UserService.change_password(user_id, old_pw, new_pw)

        return response_success({}, "Đổi mật khẩu thành công", 200)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi đổi mật khẩu", 500)


@user_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def get_all_users():
    try:
        current_user_id = int(get_jwt_identity())

        current_user = UserService.get_user_by_id(current_user_id, active=True)

        # role_id = 0 là ADMIN
        if current_user.role_id != 0:
            return response_error("Không có quyền truy cập", 403)

        users = UserService.get_all_users()

        return (
            response_success(
                {
                    "users": [
                        {
                            "user_id": user.user_id,
                            "email": user.email,
                            "username": user.username,
                            "role_id": user.role_id,
                            "active": user.active,
                        }
                        for user in users
                    ]
                }
            ),
            200,
        )

    except ValueError as error:
        return response_error(str(error), 404)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy danh sách người dùng", 500)


@user_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())

        if current_user_id != user_id:
            return response_error("Không có quyền xóa user khác", 403)

        UserService.delete_user(user_id)

        return response_success({}, "User đã được xóa", 200)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi xóa user", 500)


@user_bp.route("/admin/users/<int:user_id>/lock", methods=["PUT"])
@jwt_required()
def lock_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())

        current_user = UserService.get_user_by_id(current_user_id, active=True)

        if current_user.role_id != 0:
            return response_error("Không có quyền truy cập", 403)

        UserService.lock_user(user_id)

        return response_success({}, "Khóa tài khoản thành công", 200)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi khóa tài khoản", 500)
