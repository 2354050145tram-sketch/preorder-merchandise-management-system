from flask_jwt_extended import get_jwt_identity
from modules.users.services import UserService


def check_admin():
    current_user_id = int(get_jwt_identity())
    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:
        raise PermissionError("Không có quyền truy cập")

    return current_user


def serialize_order_item(item):
    prod = item.product
    pre = item.preorder

    return {
        "order_item_id": item.order_item_id,
        "product_id": item.product_id,
        "preorder_id": item.preorder_id,
        "product_name": prod.product_name if prod else f"Sản phẩm #{item.product_id}",
        "quantity": item.quantity or 1,
        "price": float(item.price or 0),
        "item_status": item.item_status or "ĐANG XỬ LÝ",
        "shipping_method": item.shipping_method,
        "tracking_code": item.tracking_code,
        "shipping_status": item.shipping_status,
        "product": (
            {
                "product_id": prod.product_id,
                "product_name": prod.product_name,
                "image": prod.image,
                "status": prod.status,
            }
            if prod
            else None
        ),
        "preorder": (
            {
                "preorder_id": pre.preorder_id,
                "start_date": (
                    pre.start_date.isoformat()
                    if getattr(pre, "start_date", None)
                    else None
                ),
                "end_date": (
                    pre.end_date.isoformat() if getattr(pre, "end_date", None) else None
                ),
                "progress_status": pre.progress_status,
                "progress_note": pre.progress_note,
                "active": pre.active,
            }
            if pre
            else None
        ),
    }


def serialize_payment(payment):
    return {
        "payment_id": payment.payment_id,
        "order_id": payment.order_id,
        "amount": float(payment.amount or 0),
        "payment_method": payment.payment_method,
        "payment_type": payment.payment_type,
        "payment_status": payment.payment_status,
        "transaction_id": payment.transaction_id,
        "paid_at": (
            payment.paid_at.isoformat() if getattr(payment, "paid_at", None) else None
        ),
        "created_at": (
            payment.created_at.isoformat()
            if getattr(payment, "created_at", None)
            else None
        ),
    }


def serialize_order(order):
    u = order.user
    o_date = getattr(order, "order_date", None)
    c_date = getattr(order, "created_at", None)

    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "username": u.username if u else f"Khách #{order.user_id}",
        "email": u.email if u else "",
        "order_date": (
            o_date.isoformat()
            if o_date
            else (c_date.strftime("%Y-%m-%d") if c_date else None)
        ),
        "total_amount": float(order.total_amount or 0),
        "shipping_fee": float(order.shipping_fee or 0),
        "amount_to_pay_online": float(order.total_amount or 0),
        "order_status": order.order_status or "CHỜ XÁC NHẬN",
        "active": order.active,
        "created_at": c_date.isoformat() if c_date else None,
        "order_items": [
            serialize_order_item(item) for item in (order.order_items or [])
        ],
        "payments": [serialize_payment(p) for p in (order.payments or [])],
    }

def serialize_order_summary(order):
    u = order.user
    o_date = getattr(order, 'order_date', None)
    c_date = getattr(order, 'created_at', None)

    return {
        "order_id": order.order_id,
        "user_id": order.user_id,
        "username": u.username if u else f"Khách #{order.user_id}",
        "email": u.email if u else "",
        "order_date": o_date.isoformat() if o_date else (c_date.strftime("%Y-%m-%d") if c_date else None),
        "total_amount": float(order.total_amount or 0),
        "shipping_fee": float(order.shipping_fee or 0),
        "order_status": order.order_status or "CHỜ XÁC NHẬN",
        "active": order.active,
    }