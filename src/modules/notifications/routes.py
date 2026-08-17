from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from modules.notifications.services import NotificationService
from modules.notifications.helpers import check_admin, serialize_notification
from utils.helpers import response_success, response_error

notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


# Admin gửi thông báo cho toàn bộ khách thuộc đợt preorder
@notification_bp.route("/admin/preorders/<int:preorder_id>", methods=["POST"])
@jwt_required()
def send_preorder_notification(preorder_id):
    try:
        check_admin()

        data = request.get_json() or {}

        notification = NotificationService.send_preorder_notification(
            preorder_id=preorder_id,
            title=data.get("title"),
            message=data.get("message"),
        )

        if notification is None:
            return response_success({}, "Không có khách hàng để gửi thông báo", 200)

        return response_success(
            {"notification": serialize_notification(notification)},
            "Gửi thông báo preorder thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi gửi thông báo preorder", 500)


# Khách hàng xem thông báo của chính mình
@notification_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_notifications():
    try:
        user_id = int(get_jwt_identity())

        notifications = NotificationService.get_user_notifications(user_id)

        return (
            response_success(
                {
                    "notifications": [
                        serialize_notification(notification)
                        for notification in notifications
                    ]
                }
            ),
            200,
        )

    except ValueError as error:
        return response_error(str(error), 404)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy thông báo", 500)
