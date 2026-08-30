from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from modules.carts.services import CartService
from modules.carts.helpers import serialize_cart, serialize_cart_item
from utils.helpers import response_success, response_error

cart_bp = Blueprint("carts", __name__, url_prefix="/api/cart")


@cart_bp.route("", methods=["GET"])
@jwt_required()
def get_cart():
    try:
        user_id = int(get_jwt_identity())
        cart = CartService.get_cart(user_id)

        return response_success(
            {"cart": serialize_cart(cart)},
            "Lấy giỏ hàng thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception as error:
        print("GET CART ERROR:", error)

        return response_error(
            "Có lỗi xảy ra khi lấy giỏ hàng",
            500,
        )


@cart_bp.route("/items", methods=["POST"])
@jwt_required()
def add_cart_item():
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}

        item = CartService.add_item(
            user_id=user_id,
            product_id=data.get("product_id"),
            quantity=data.get(
                "quantity",
                1,
            ),
        )

        return response_success(
            {"item": serialize_cart_item(item)},
            "Thêm sản phẩm vào giỏ hàng thành công",
            201,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception as error:
        print("ADD CART ERROR:", error)

        return response_error(
            "Có lỗi xảy ra khi thêm vào giỏ hàng",
            500,
        )


@cart_bp.route(
    "/items/<int:cart_item_id>",
    methods=["PUT"],
)
@jwt_required()
def update_cart_item(cart_item_id):
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}

        item = CartService.update_quantity(
            user_id=user_id,
            cart_item_id=cart_item_id,
            quantity=data.get("quantity"),
        )

        return response_success(
            {"item": serialize_cart_item(item)},
            "Cập nhật giỏ hàng thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception as error:
        print("UPDATE CART ERROR:", error)

        return response_error(
            "Có lỗi xảy ra khi cập nhật giỏ hàng",
            500,
        )


@cart_bp.route(
    "/items/<int:cart_item_id>",
    methods=["DELETE"],
)
@jwt_required()
def remove_cart_item(cart_item_id):
    try:
        user_id = int(get_jwt_identity())

        CartService.remove_item(
            user_id=user_id,
            cart_item_id=cart_item_id,
        )

        return response_success(
            {},
            "Đã xóa sản phẩm khỏi giỏ hàng",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception as error:
        print("DELETE CART ITEM ERROR:", error)

        return response_error(
            "Có lỗi xảy ra khi xóa sản phẩm",
            500,
        )


@cart_bp.route(
    "",
    methods=["DELETE"],
)
@jwt_required()
def clear_cart():
    try:
        user_id = int(get_jwt_identity())

        CartService.clear_cart(user_id)

        return response_success(
            {},
            "Đã xóa toàn bộ giỏ hàng",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception as error:
        print("CLEAR CART ERROR:", error)

        return response_error(
            "Có lỗi xảy ra khi xóa giỏ hàng",
            500,
        )
