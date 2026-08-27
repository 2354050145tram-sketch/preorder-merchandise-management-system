from flask_jwt_extended import get_jwt_identity
from modules.users.services import UserService


def check_admin():
    current_user_id = int(get_jwt_identity())

    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:
        raise PermissionError("Không có quyền truy cập")

    return current_user


def serialize_order_item(item):
    return {
        "order_item_id": item.order_item_id,
        "product_id": item.product_id,
        "preorder_id": item.preorder_id,
        "product_name": (item.product.product_name if item.product else None),
        "quantity": item.quantity,
        "price": float(item.price),
        "item_status": item.item_status,
        "shipping_method": item.shipping_method,
        "tracking_code": item.tracking_code,
        "shipping_status": item.shipping_status,
    }


def serialize_payment(payment):
    return {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "payment_status": payment.payment_status,
        "transaction_id": payment.transaction_id,
        "paid_at": (payment.paid_at.isoformat() if payment.paid_at else None),
        "created_at": (payment.created_at.isoformat() if payment.created_at else None),
    }


def serialize_order(order):
    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "order_date": (order.order_date.isoformat() if order.order_date else None),
        "total_amount": float(order.total_amount),
        "shipping_fee": float(order.shipping_fee),
        "amount_to_pay_online": float(order.total_amount),
        "order_status": order.order_status,
        "active": order.active,
        "created_at": (order.created_at.isoformat() if order.created_at else None),
        "order_items": [serialize_order_item(item) for item in order.order_items],
        "payments": [serialize_payment(payment) for payment in order.payments],
    }
