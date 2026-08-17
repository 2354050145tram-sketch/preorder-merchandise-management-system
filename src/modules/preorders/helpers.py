from flask_jwt_extended import get_jwt_identity
from modules.users.services import UserService


def serialize_preorder(preorder):
    return {
        "preorder_id": preorder.preorder_id,
        "product_id": preorder.product_id,
        "product": {
            "product_id": preorder.product.product_id,
            "product_name": preorder.product.product_name,
            "price": float(preorder.product.price),
            "image": preorder.product.image,
            "status": preorder.product.status,
        },
        "start_date": (
            preorder.start_date.isoformat() if preorder.start_date else None
        ),
        "end_date": (preorder.end_date.isoformat() if preorder.end_date else None),
        "quantity_order": preorder.quantity_order,
        "progress_status": preorder.progress_status,
        "progress_note": preorder.progress_note,
        "active": preorder.active,
    }


def check_admin():
    current_user_id = int(get_jwt_identity())

    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:
        raise PermissionError("Không có quyền truy cập")

    return current_user
