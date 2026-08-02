from flask import Blueprint, request, jsonify
from modules.users.services import UserService
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import check_password_hash
from modules.users.models import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.helpers import response_success, response_error

user_bp = Blueprint("users", __name__)

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    try:
        user = UserService.register(
            email=data.get("email"),
            username=data.get("username"),
            password=data.get("password"),
            full_name=data.get("full_name"),
            phone_num=data.get("phone_num"),
            address=data.get("address")
        )

        access_token = create_access_token(identity=user.user_id)

        return response_success({
            "message": "Đăng ký thành công",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username
            },
            "access_token": access_token
        }), 201

    except ValueError as error:
        return response_error(str(error), 400)
    except Exception:
        return response_error("Có lỗi xảy ra khi đăng ký", 500)
    
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email").strip().lower()
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return response_error({"message": "Sai email hoặc mật khẩu"}), 401

    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)
    return response_success({
        "access_token": access_token,
        "refresh_token": refresh_token
    }, "Đăng nhập thành công", 200)

@user_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return response_success({
        "access_token": new_access_token
    }), 200

@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User không tồn tại"}), 404

    return jsonify({
        "user_id": user.user_id,
        "email": user.email,
        "username": user.username,
        "profile": {
            "full_name": user.profile.full_name,
            "phone_num": user.profile.phone_num,
            "address": user.profile.address
        }
    })

@user_bp.route("/users/<int:user_id>/profile", methods=["PUT"])
@jwt_required()
def update_user_profile(user_id):
    current_user_id = get_jwt_identity()
    if current_user_id != user_id:
        return jsonify({"message": "Không có quyền sửa profile người khác"}), 403

    data = request.get_json()
    profile = UserService.update_profile(user_id, data)

    return jsonify({
        "message": "Profile đã cập nhật",
        "full_name": profile.full_name,
        "phone_num": profile.phone_num,
        "address": profile.address
    })

@user_bp.route("/users/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()
    old_pw = data.get("old_password")
    new_pw = data.get("new_password")

    try:
        UserService.change_password(user_id, old_pw, new_pw)
        return response_success({"message": "Đổi mật khẩu thành công"}), 200
    except ValueError as e:
        return response_error({"message": str(e)}), 400

@user_bp.route("/admin/users", methods=["GET"])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # check role
    if current_user.role_id != 0:  # 0 = admin
        return jsonify({"message": "Không có quyền"}), 403

    users = User.query.all()
    return jsonify([{
        "user_id": u.user_id,
        "email": u.email,
        "username": u.username,
        "role_id": u.role_id
    } for u in users])

@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return jsonify({"message": "Không có quyền xóa user khác"}), 403

    try:
        UserService.delete_user(user_id)
        return response_success({"message": "User đã được xóa"}), 200
    except ValueError as e:
        return response_error({"message": str(e)}), 400
    except Exception:
        return response_error({"message": "Có lỗi xảy ra khi xóa user"}), 500

    
