from config import db
from flask import Blueprint, request
from sqlalchemy import select
from flask_jwt_extended import jwt_required, get_jwt_identity
from modules.orders.services import OrderService, PaymentService
from modules.orders.models import Order, OrderItem, Payment
from modules.users.models import User
from modules.orders.models import OrderItem, Payment
from modules.wallets.services import WalletService
from modules.wallets.helpers import serialize_wallet_transaction
from modules.orders.helpers import (
    check_admin,
    serialize_order,
    serialize_order_item,
    serialize_payment,
)
from utils.helpers import response_success, response_error

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@order_bp.route("", methods=["POST"])
@jwt_required()
def create_order():
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}

        order = OrderService.create_order(user_id=user_id, items=data.get("items"))

        return response_success(
            {"order": serialize_order(order)}, "Tạo đơn hàng thành công", 201
        )

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi tạo đơn hàng", 500)


@order_bp.route("/my-orders", methods=["GET"])
@jwt_required()
def get_my_orders():
    try:
        user_id = int(get_jwt_identity())

        orders = OrderService.get_orders_by_user(user_id)

        return response_success(
            {"orders": [serialize_order(order) for order in orders]},
            "Lấy danh sách đơn hàng thành công",
            200,
        )

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy đơn hàng", 500)


@order_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order_by_id(order_id):
    try:
        user_id = int(get_jwt_identity())

        order = OrderService.get_order_by_id(order_id)

        if order.user_id != user_id:
            return response_error(
                "Không có quyền xem đơn hàng này",
                403,
            )

        return response_success(
            {"order": serialize_order(order)},
            "Lấy chi tiết đơn hàng thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            404,
        )

    except Exception as error:

        print(
            "GET ORDER DETAIL ERROR:",
            error,
        )

        return response_error(
            "Có lỗi xảy ra khi lấy đơn hàng",
            500,
        )


from modules.orders.helpers import check_admin, serialize_order, serialize_order_summary


@order_bp.route("/admin", methods=["GET"])
@jwt_required()
def get_all_orders():
    try:
        check_admin()
        keyword = request.args.get("keyword")
        order_status = request.args.get("order_status")
        active_param = request.args.get("active")

        active = None
        if active_param is not None:
            if active_param.lower() == "true":
                active = True
            elif active_param.lower() == "false":
                active = False

        orders = OrderService.get_all_orders(
            keyword=keyword, order_status=order_status, active=active
        )

        return response_success(
            {"orders": [serialize_order_summary(order) for order in orders]},
            "Lấy danh sách đơn hàng thành công",
            200,
        )
    except PermissionError as error:
        return response_error(str(error), 403)
    except Exception as error:
        return response_error(f"Lỗi: {str(error)}", 500)


@order_bp.route("/admin/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order_admin(order_id):
    try:
        check_admin()
        order = OrderService.get_order_by_id(order_id)
        if not order:
            return response_error("Đơn hàng không tồn tại", 404)

        # Trả về dữ liệu chi tiết an toàn
        return response_success(
            {"order": serialize_order(order)}, "Lấy chi tiết đơn hàng thành công", 200
        )

    except PermissionError as error:
        return response_error(str(error), 403)
    except ValueError as error:
        return response_error(str(error), 404)
    except Exception as error:
        print(">>> LỖI GET ORDER ADMIN DETAIL:", str(error))
        return response_error(f"Lỗi: {str(error)}", 500)


@order_bp.route("/admin/<int:order_id>/status", methods=["PUT"])
@jwt_required()
def update_order_status(order_id):
    try:
        check_admin()

        data = request.get_json() or {}

        order = OrderService.update_order_status(
            order_id=order_id, order_status=data.get("order_status")
        )

        return response_success(
            {"order": serialize_order(order)},
            "Cập nhật trạng thái đơn hàng thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi cập nhật trạng thái đơn hàng", 500)


@order_bp.route("/admin/<int:order_id>/shipping", methods=["POST"])
@jwt_required()
def update_shipping_info(order_id):
    try:
        check_admin()

        data = request.get_json() or {}

        order_items = OrderService.update_shipping_info(
            order_id=order_id,
            order_item_ids=data.get("order_item_ids"),
            shipping_method=data.get("shipping_method"),
            shipping_fee=data.get("shipping_fee"),
            tracking_code=data.get("tracking_code"),
        )

        return response_success(
            {"order_items": [serialize_order_item(item) for item in order_items]},
            "Tạo thông tin vận chuyển thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi cập nhật vận chuyển", 500)


@order_bp.route("/admin/shipping/<string:tracking_code>/status", methods=["PUT"])
@jwt_required()
def update_shipping_status(tracking_code):
    try:
        check_admin()

        data = request.get_json() or {}

        order_items = OrderService.update_shipping_status(
            tracking_code=tracking_code, shipping_status=data.get("shipping_status")
        )

        return response_success(
            {"order_items": [serialize_order_item(item) for item in order_items]},
            "Cập nhật trạng thái vận chuyển thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi cập nhật trạng thái vận chuyển", 500)


@order_bp.route("/items/<int:order_item_id>/cancel", methods=["PUT"])
@jwt_required()
def cancel_order_item(order_item_id):
    try:
        user_id = int(get_jwt_identity())

        order_item = db.session.get(OrderItem, order_item_id)

        if not order_item:
            raise ValueError("Sản phẩm trong đơn hàng không tồn tại")

        order = OrderService.get_order_by_id(order_item.order_id)

        if order.user_id != user_id:
            return response_error("Không có quyền hủy sản phẩm này", 403)

        order_item = OrderService.cancel_order_item(order_item_id)

        return response_success(
            {"order_item": serialize_order_item(order_item)},
            "Hủy sản phẩm thành công",
            200,
        )

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi hủy sản phẩm", 500)


@order_bp.route("/<int:order_id>/payments", methods=["POST"])
@jwt_required()
def create_payment(order_id):
    try:
        user_id = int(get_jwt_identity())

        order = OrderService.get_order_by_id(order_id)

        if order.user_id != user_id:
            return response_error("Không có quyền thanh toán đơn hàng này", 403)

        data = request.get_json() or {}

        payment_method = data.get("payment_method")

        payment_type = data.get("payment_type")

        transaction_id = data.get("transaction_id")

        if payment_method != "MOMO":
            raise ValueError("Phương thức thanh toán không hợp lệ")

        payment = PaymentService.create_payment(
            order_id=order_id,
            payment_method=payment_method,
            payment_type=payment_type,
            transaction_id=transaction_id,
        )

        return response_success(
            {"payment": serialize_payment(payment)}, "Tạo thanh toán thành công", 201
        )

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi tạo thanh toán", 500)


@order_bp.route("/<int:order_id>/payments", methods=["GET"])
@jwt_required()
def get_payments_by_order(order_id):
    try:
        user_id = int(get_jwt_identity())

        order = OrderService.get_order_by_id(order_id)

        if order.user_id != user_id:
            return response_error("Không có quyền xem thanh toán của đơn hàng này", 403)

        payments = PaymentService.get_payments_by_order(order_id)

        return (
            response_success(
                {"payments": [serialize_payment(payment) for payment in payments]}
            ),
            200,
        )

    except ValueError as error:
        return response_error(str(error), 404)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy thanh toán", 500)


@order_bp.route("/admin/payments/<int:payment_id>/confirm", methods=["PUT"])
@jwt_required()
def confirm_payment(payment_id):
    try:
        check_admin()

        payment = PaymentService.confirm_payment(payment_id)

        return response_success(
            {"payment": serialize_payment(payment)},
            "Xác nhận thanh toán thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi xác nhận thanh toán", 500)


@order_bp.route("/payments/<int:payment_id>/cancel", methods=["PUT"])
@jwt_required()
def cancel_payment(payment_id):
    try:
        user_id = int(get_jwt_identity())

        payment = db.session.get(Payment, payment_id)

        if not payment:
            raise ValueError("Thanh toán không tồn tại")

        order = OrderService.get_order_by_id(payment.order_id)

        if order.user_id != user_id:
            return response_error("Không có quyền hủy thanh toán này", 403)

        payment = PaymentService.cancel_payment(payment_id)

        return response_success(
            {"payment": serialize_payment(payment)}, "Hủy thanh toán thành công", 200
        )

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi hủy thanh toán", 500)


@order_bp.route(
    "/admin/items/" "<int:order_item_id>/refund",
    methods=["POST"],
)
@jwt_required()
def refund_order_item(order_item_id):
    try:
        check_admin()

        refund_data = PaymentService.refund_order_item(order_item_id)

        transaction = WalletService.refund_to_wallet(
            order_id=refund_data["order_id"],
            order_item_id=refund_data["order_item_id"],
            amount=refund_data["amount"],
            description=("Hoàn tiền sản phẩm " f"#{order_item_id}"),
        )

        return response_success(
            {"transaction": serialize_wallet_transaction(transaction)},
            "Hoàn tiền vào Ví Verd thành công",
            200,
        )

    except PermissionError as error:
        return response_error(
            str(error),
            403,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi hoàn tiền",
            500,
        )


@order_bp.route(
    "/deposit-eligibility",
    methods=["GET"],
)
@jwt_required()
def get_deposit_eligibility():

    try:
        user_id = int(get_jwt_identity())

        eligible = PaymentService.has_previous_paid_order(user_id=user_id)

        return response_success(
            {
                "eligible_for_deposit": eligible,
                "deposit_rate": 70 if eligible else None,
            },
            "Kiểm tra quyền đặt cọc thành công",
            200,
        )

    except Exception as error:

        print("DEPOSIT ELIGIBILITY ERROR:", error)

        return response_error(
            "Có lỗi xảy ra khi kiểm tra quyền đặt cọc",
            500,
        )


@order_bp.route(
    "/<int:order_id>/payment-summary",
    methods=["GET"],
)
@jwt_required()
def get_payment_summary(order_id):
    try:
        user_id = int(get_jwt_identity())

        summary = PaymentService.get_order_payment_summary(order_id)

        order = summary["order"]

        if order.user_id != user_id:
            return response_error(
                "Không có quyền truy cập đơn hàng",
                403,
            )

        return response_success(
            {
                "order_id": order.order_id,
                "preorder_amount": float(summary["preorder_amount"]),
                "in_stock_amount": float(summary["in_stock_amount"]),
                "shipping_fee": float(summary["shipping_fee"]),
                "total_amount": float(summary["total_amount"]),
                "total_paid": float(summary["total_paid"]),
                "remaining_amount": float(summary["remaining_amount"]),
                "eligible_for_deposit": summary["eligible_for_deposit"],
                "deposit_rate": 70 if summary["eligible_for_deposit"] else None,
            },
            "Lấy thông tin thanh toán thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy " "thông tin thanh toán",
            500,
        )


@order_bp.route("/admin/product/<int:product_id>/preorder-customers", methods=["GET"])
@jwt_required()
def get_preorder_customers_by_product(product_id):
    try:
        check_admin()

        stmt = (
            select(
                Order.order_id,
                User.username,
                User.email,
                OrderItem.quantity,
                OrderItem.price,
                Order.order_status,
                Order.created_at,
            )
            .join(User, Order.user_id == User.user_id)
            .join(OrderItem, Order.order_id == OrderItem.order_id)
            .where(
                OrderItem.product_id == product_id,
                OrderItem.item_status != "ĐÃ HỦY",
                Order.active.is_(True),
            )
            .order_by(Order.created_at.desc())
        )

        results = db.session.execute(stmt).all()

        customers = []
        for r in results:
            item_price = float(r.price)
            item_quantity = r.quantity
            item_subtotal = (
                item_price * item_quantity
            )  # Tính riêng tiền của sản phẩm này

            customers.append(
                {
                    "order_id": r.order_id,
                    "username": r.username,
                    "email": r.email,
                    "quantity": item_quantity,
                    "price": item_price,
                    "subtotal": item_subtotal,
                    "order_status": r.order_status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
            )

        return response_success(
            {"customers": customers},
            "Lấy danh sách khách hàng preorder thành công",
            200,
        )
    except PermissionError as error:
        return response_error(str(error), 403)
    except Exception as e:
        return response_error(f"Lỗi: {str(e)}", 500)


@order_bp.route("/<int:order_id>/check-payment-status", methods=["GET"])
@jwt_required()
def check_payment_status(order_id):
    try:
        order = OrderService.get_order_by_id(order_id)
        is_paid = order.order_status in ["ĐÃ ĐẶT CỌC", "ĐÃ XÁC NHẬN", "HOÀN THÀNH"]
        return response_success(
            {"is_paid": is_paid, "status": order.order_status},
            "Lấy trạng thái thành công",
            200,
        )
    except Exception as error:
        return response_error(f"Lỗi: {str(error)}", 500)
