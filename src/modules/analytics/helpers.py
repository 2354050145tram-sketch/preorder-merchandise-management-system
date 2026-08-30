from flask_jwt_extended import get_jwt_identity
from modules.users.services import UserService


def check_admin():
    current_user_id = int(get_jwt_identity())

    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:
        raise PermissionError("Không có quyền truy cập")

    return current_user


def serialize_dashboard_summary(data):
    return {
        "total_revenue": float(data["total_revenue"] or 0),
        "total_orders": int(data["total_orders"] or 0),
        "total_customers": int(data["total_customers"] or 0),
        "total_products": int(data["total_products"] or 0),
        "low_stock_count": int(data["low_stock_count"] or 0),
    }


def serialize_revenue_report(data):
    return {
        "date": (data["date"].isoformat() if data["date"] is not None else None),
        "paid": float(data["paid"] or 0),
        "refunded": float(data["refunded"] or 0),
        "revenue": float(data["revenue"] or 0),
    }


def serialize_order_statistic(data):
    return {
        "order_status": data["order_status"],
        "total": int(data["total"] or 0),
    }


def serialize_best_selling_product(data):
    return {
        "product_id": data["product_id"],
        "product_name": data["product_name"],
        "quantity_sold": int(data["quantity_sold"] or 0),
    }


def serialize_low_stock_product(data):
    return {
        "product_id": data["product_id"],
        "product_name": data["product_name"],
        "quantity": int(data["quantity"] or 0),
        "status": data["status"],
    }


def serialize_customer_statistics(data):
    return {
        "total_customers": int(data["total_customers"] or 0),
        "top_customers": [
            {
                "user_id": customer["user_id"],
                "username": customer["username"],
                "total_orders": int(customer["total_orders"] or 0),
                "total_paid": float(customer["total_paid"] or 0),
                "total_refunded": float(customer["total_refunded"] or 0),
                "total_spent": float(customer["total_spent"] or 0),
            }
            for customer in data["top_customers"]
        ],
    }
