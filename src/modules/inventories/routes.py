from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from modules.inventories.services import InventoryService
from modules.inventories.helpers import (
    check_admin,
    serialize_inventory,
    serialize_inventory_transaction,
)
from utils.helpers import response_success, response_error

inventory_bp = Blueprint("inventories", __name__, url_prefix="/api/inventories")


@inventory_bp.route("/admin", methods=["GET"])
@jwt_required()
def get_all_inventory():
    try:
        check_admin()

        keyword = request.args.get("keyword")
        status = request.args.get("status")
        active_param = request.args.get("active")

        if active_param is None:
            active = None

        elif active_param.lower() == "true":
            active = True

        elif active_param.lower() == "false":
            active = False

        else:
            raise ValueError("Trạng thái không hợp lệ")

        inventories = InventoryService.get_all_inventory(
            keyword=keyword, status=status, active=active
        )

        return (
            response_success(
                {
                    "inventories": [
                        serialize_inventory(inventory) for inventory in inventories
                    ]
                }
            ),
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy tồn kho", 500)


@inventory_bp.route("/admin", methods=["POST"])
@jwt_required()
def create_inventory():
    try:
        check_admin()

        data = request.get_json() or {}

        inventory = InventoryService.create_inventory(
            product_id=data.get("product_id"),
            quantity=data.get("quantity"),
            price=data.get("price"),
        )

        return response_success(
            {"inventory": serialize_inventory(inventory)}, "Tạo tồn kho thành công", 201
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi tạo tồn kho", 500)


@inventory_bp.route("/admin/<int:product_id>/import", methods=["POST"])
@jwt_required()
def import_stock(product_id):
    try:
        check_admin()

        data = request.get_json() or {}

        inventory = InventoryService.import_stock(
            product_id=product_id,
            quantity=data.get("quantity"),
            price=data.get("price"),
        )

        return response_success(
            {"inventory": serialize_inventory(inventory)}, "Nhập hàng thành công", 200
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi nhập hàng", 500)


@inventory_bp.route("/admin/<int:product_id>/export", methods=["POST"])
@jwt_required()
def export_stock(product_id):
    try:
        check_admin()

        data = request.get_json() or {}

        inventory = InventoryService.export_stock(
            product_id=product_id, quantity=data.get("quantity")
        )

        return response_success(
            {"inventory": serialize_inventory(inventory)}, "Xuất kho thành công", 200
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi xuất kho", 500)


@inventory_bp.route("/admin/<int:product_id>/quantity", methods=["PUT"])
@jwt_required()
def update_stock(product_id):
    try:
        check_admin()

        data = request.get_json() or {}

        inventory = InventoryService.update_stock(
            product_id=product_id, quantity=data.get("quantity")
        )

        return response_success(
            {"inventory": serialize_inventory(inventory)},
            "Điều chỉnh tồn kho thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi điều chỉnh tồn kho", 500)


@inventory_bp.route("/admin/<int:product_id>/status", methods=["GET"])
@jwt_required()
def get_inventory_status(product_id):
    try:
        check_admin()

        status = InventoryService.get_inventory_status(product_id)

        return response_success({"product_id": product_id, "status": status}), 200

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 404)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy trạng thái tồn kho", 500)


@inventory_bp.route("/admin/transactions", methods=["GET"])
@jwt_required()
def get_inventory_transactions():
    try:
        check_admin()

        product_id = request.args.get("product_id", type=int)

        transaction_type = request.args.get("transaction_type")

        transactions = InventoryService.get_inventory_transactions(
            product_id=product_id, transaction_type=transaction_type
        )

        return (
            response_success(
                {
                    "transactions": [
                        serialize_inventory_transaction(transaction)
                        for transaction in transactions
                    ]
                }
            ),
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy lịch sử tồn kho", 500)
