from flask_jwt_extended import get_jwt_identity
from modules.users.services import UserService


def check_admin():
    current_user_id = int(get_jwt_identity())

    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:
        raise PermissionError("Không có quyền truy cập")

    return current_user


def serialize_notification(notification):
    return {
        "notification_id": notification.notification_id,
        "preorder_id": notification.preorder_id,
        "title": notification.title,
        "message": notification.message,
        "created_at": (
            notification.created_at.isoformat() if notification.created_at else None
        ),
    }
