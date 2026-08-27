from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from modules.products.services import ProductService
from modules.products.helpers import (
    serialize_product,
    check_admin
)
from utils.helpers import (
    response_success,
    response_error
)

product_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/products"
)

@product_bp.route(
    "",
    methods=["GET"]
)
def get_all_products(active=None):
    try:
        keyword = request.args.get(
            "keyword"
        )

        status = request.args.get(
            "status"
        )

        min_price = request.args.get(
            "min_price"
        )

        max_price = request.args.get(
            "max_price"
        )

        tag_ids = request.args.getlist(
            "tag_ids",
            type=int
        )

        products = ProductService.get_all_products(
            keyword=keyword,
            status=status,
            tag_ids=tag_ids or None,
            min_price=min_price,
            max_price=max_price,
            active=True
        )

        return response_success({
            "products": [
                serialize_product(product)
                for product in products
            ]
        }), 200

    except ValueError as error:
        return response_error(
            str(error),
            400
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy danh sách sản phẩm",
            500
        )
        
@product_bp.route(
    "/<int:product_id>",
    methods=["GET"]
)
def get_product_by_id(product_id):
    try:
        product = ProductService.get_product_by_id(
            product_id,
            active=True
        )

        return response_success({
            "product": serialize_product(
                product
            )
        }), 200

    except ValueError as error:
        return response_error(
            str(error),
            404
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy sản phẩm",
            500
        )
        
@product_bp.route(
    "/admin",
    methods=["POST"]
)
@jwt_required()
def create_product():
    try:
        check_admin()

        data = request.get_json() or {}

        product = ProductService.create_product(
            product_name=data.get(
                "product_name"
            ),
            price=data.get(
                "price"
            ),
            description=data.get(
                "description"
            ),
            image=data.get(
                "image"
            ),
            status=data.get(
                "status"
            ),
            tag_ids=data.get(
                "tag_ids"
            )
        )

        return response_success({
            "product": serialize_product(
                product
            )
        }, "Tạo sản phẩm thành công", 201)

    except PermissionError as error:
        return response_error(
            str(error),
            403
        )

    except ValueError as error:
        return response_error(
            str(error),
            400
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi tạo sản phẩm",
            500
        )
        
@product_bp.route(
    "/admin/<int:product_id>",
    methods=["PUT"]
)
@jwt_required()
def update_product(product_id):
    try:
        check_admin()

        data = request.get_json() or {}

        tag_ids = (
            data.get("tag_ids")
            if "tag_ids" in data
            else None
        )

        product = ProductService.update_product(
            product_id=product_id,
            data=data,
            tag_ids=tag_ids
        )

        return response_success({
            "product": serialize_product(
                product
            )
        }, "Cập nhật sản phẩm thành công", 200)

    except PermissionError as error:
        return response_error(
            str(error),
            403
        )

    except ValueError as error:
        return response_error(
            str(error),
            400
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi cập nhật sản phẩm",
            500
        )
        
@product_bp.route(
    "/admin/<int:product_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_product(product_id):
    try:
        check_admin()

        product = ProductService.delete_product(
            product_id
        )

        return response_success({
            "product_id": product.product_id
        }, "Sản phẩm đã được ẩn", 200)

    except PermissionError as error:
        return response_error(
            str(error),
            403
        )

    except ValueError as error:
        return response_error(
            str(error),
            400
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi xóa sản phẩm",
            500
        )
        
@product_bp.route(
    "/tags",
    methods=["GET"]
)
def get_all_tags():
    try:
        tags = ProductService.get_all_tags()

        return response_success({
            "tags": [
                {
                    "tag_id": tag.tag_id,
                    "name": tag.name
                }
                for tag in tags
            ]
        }), 200

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy danh sách thẻ",
            500
        )
        
@product_bp.route(
    "/admin/tags",
    methods=["POST"]
)
@jwt_required()
def create_tag():
    try:
        check_admin()

        data = request.get_json() or {}

        tag = ProductService.create_tag(
            name=data.get("name")
        )

        return response_success({
            "tag": {
                "tag_id": tag.tag_id,
                "name": tag.name
            }
        }, "Tạo thẻ thành công", 201)

    except PermissionError as error:
        return response_error(
            str(error),
            403
        )

    except ValueError as error:
        return response_error(
            str(error),
            400
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi tạo thẻ",
            500
        )