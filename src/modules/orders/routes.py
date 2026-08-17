from config import db
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from modules.orders.services import OrderService, PaymentService
from modules.orders.models import OrderItem, Payment
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

        return (
            response_success({"orders": [serialize_order(order) for order in orders]}),
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
            return response_error("Không có quyền xem đơn hàng này", 403)

        return response_success({"order": serialize_order(order)}), 200

    except ValueError as error:
        return response_error(str(error), 404)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy đơn hàng", 500)


@order_bp.route("/admin", methods=["GET"])
@jwt_required()
def get_all_orders():
    try:
        check_admin()

        keyword = request.args.get("keyword")

        order_status = request.args.get("order_status")

        active_param = request.args.get("active")

        if active_param is None:
            active = None

        elif active_param.lower() == "true":
            active = True

        elif active_param.lower() == "false":
            active = False

        else:
            raise ValueError("Trạng thái active không hợp lệ")

        orders = OrderService.get_all_orders(
            keyword=keyword, order_status=order_status, active=active
        )

        return (
            response_success({"orders": [serialize_order(order) for order in orders]}),
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy danh sách đơn hàng", 500)


@order_bp.route("/admin/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order_admin(order_id):
    try:
        check_admin()

        order = OrderService.get_order_by_id(order_id)

        return response_success({"order": serialize_order(order)}), 200

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 404)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy đơn hàng", 500)


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

        payment = PaymentService.create_payment(
            order_id=order_id,
            amount=data.get("amount"),
            payment_method=data.get("payment_method"),
            transaction_id=data.get("transaction_id"),
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


@order_bp.route("/admin/items/<int:order_item_id>/refund", methods=["POST"])
@jwt_required()
def refund_order_item(order_item_id):
    try:
        check_admin()

        refund_data = PaymentService.refund_order_item(order_item_id)

        return response_success(
            refund_data, "Xác nhận yêu cầu hoàn tiền thành công", 200
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi xử lý hoàn tiền", 500)
