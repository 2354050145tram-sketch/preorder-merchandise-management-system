from flask_jwt_extended import get_jwt_identity
from modules.users.services import UserService


def check_admin():
    current_user_id = int(get_jwt_identity())

    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:
        raise PermissionError("Không có quyền truy cập")

    return current_user


def serialize_inventory(inventory):
    return {
        "inventory_id": inventory.inventory_id,
        "product_id": inventory.product_id,
        "product_name": (inventory.product.product_name if inventory.product else None),
        "quantity": inventory.quantity,
        "price": float(inventory.price),
        "status": inventory.status,
        "active": inventory.active,
        "created_at": (
            inventory.created_at.isoformat() if inventory.created_at else None
        ),
        "updated_at": (
            inventory.updated_at.isoformat() if inventory.updated_at else None
        ),
    }


def serialize_inventory_transaction(transaction):
    return {
        "inventory_transaction_id": transaction.inventory_transaction_id,
        "inventory_transaction_id": transaction.inventory_transaction_id,
        "inventory_id": transaction.inventory_id,
        "transaction_type": transaction.transaction_type,
        "quantity": transaction.quantity,
        "price": (float(transaction.price) if transaction.price is not None else None),
        "created_at": (
            transaction.created_at.isoformat() if transaction.created_at else None
        ),
    }
