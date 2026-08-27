from flask_jwt_extended import get_jwt_identity
from modules.users.services import UserService


def check_admin():
    current_user_id = int(get_jwt_identity())

    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:
        raise PermissionError("Không có quyền truy cập")

    return current_user


def serialize_wallet(wallet):
    return {
        "wallet_id": wallet.wallet_id,
        "user_id": wallet.user_id,
        "balance": float(wallet.balance),
        "active": wallet.active,
        "created_at": (wallet.created_at.isoformat() if wallet.created_at else None),
        "updated_at": (wallet.updated_at.isoformat() if wallet.updated_at else None),
    }


def serialize_wallet_transaction(transaction):
    return {
        "wallet_transaction_id": transaction.wallet_transaction_id,
        "wallet_id": transaction.wallet_id,
        "order_id": transaction.order_id,
        "transaction_type": transaction.transaction_type,
        "amount": float(transaction.amount),
        "balance_before": float(transaction.balance_before),
        "balance_after": float(transaction.balance_after),
        "transaction_status": transaction.transaction_status,
        "transaction_code": transaction.transaction_code,
        "description": transaction.description,
        "created_at": (
            transaction.created_at.isoformat() if transaction.created_at else None
        ),
    }
