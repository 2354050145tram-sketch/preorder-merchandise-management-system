from flask import (
    Blueprint,
    request,
)

from flask_jwt_extended import (
    jwt_required,
)

from modules.products.services import (
    ProductService,
)

from modules.products.helpers import (
    serialize_product,
    check_admin,
)

from utils.helpers import (
    response_success,
    response_error,
)

product_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/products",
)


@product_bp.route(
    "",
    methods=["GET"],
)
def get_all_products():
    try:
        keyword = request.args.get("keyword")

        status = request.args.get("status")

        min_price = request.args.get("min_price")

        max_price = request.args.get("max_price")

        category_id = request.args.get(
            "category_id",
            type=int,
        )

        sub_category_id = request.args.get(
            "sub_category_id",
            type=int,
        )

        tag_ids = request.args.getlist(
            "tag_ids",
            type=int,
        )

        products = ProductService.get_all_products(
            keyword=keyword,
            status=status,
            tag_ids=(tag_ids or None),
            category_id=category_id,
            sub_category_id=sub_category_id,
            min_price=min_price,
            max_price=max_price,
            active=True,
        )

        return response_success(
            {"products": [serialize_product(product) for product in products]},
            "Lấy danh sách sản phẩm thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy danh sách sản phẩm",
            500,
        )


@product_bp.route(
    "/<int:product_id>",
    methods=["GET"],
)
def get_product_by_id(product_id):
    try:
        product = ProductService.get_product_by_id(
            product_id,
            active=True,
        )

        return response_success(
            {"product": serialize_product(product)},
            "Lấy sản phẩm thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            404,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy sản phẩm",
            500,
        )


@product_bp.route(
    "/admin",
    methods=["POST"],
)
@jwt_required()
def create_product():
    try:
        check_admin()

        data = request.get_json() or {}

        product = ProductService.create_product(
            product_name=data.get("product_name"),
            price=data.get("price"),
            description=data.get("description"),
            image=data.get("image"),
            status=data.get("status"),
            tag_ids=data.get("tag_ids"),
        )

        return response_success(
            {"product": serialize_product(product)},
            "Tạo sản phẩm thành công",
            201,
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
            "Có lỗi xảy ra khi tạo sản phẩm",
            500,
        )


@product_bp.route(
    "/admin/<int:product_id>",
    methods=["PUT"],
)
@jwt_required()
def update_product(product_id):
    try:
        check_admin()

        data = request.get_json() or {}

        tag_ids = data.get("tag_ids") if "tag_ids" in data else None

        product = ProductService.update_product(
            product_id=product_id,
            data=data,
            tag_ids=tag_ids,
        )

        return response_success(
            {"product": serialize_product(product)},
            "Cập nhật sản phẩm thành công",
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
            "Có lỗi xảy ra khi cập nhật sản phẩm",
            500,
        )


@product_bp.route(
    "/admin/<int:product_id>",
    methods=["DELETE"],
)
@jwt_required()
def delete_product(product_id):
    try:
        check_admin()

        product = ProductService.delete_product(product_id)

        return response_success(
            {"product_id": product.product_id},
            "Sản phẩm đã được ẩn",
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
            "Có lỗi xảy ra khi xóa sản phẩm",
            500,
        )



@product_bp.route(
    "/categories",
    methods=["GET"],
)
def get_categories():
    try:
        categories = ProductService.get_categories()

        return response_success(
            {
                "categories": [
                    {
                        "category_id": category.category_id,
                        "name": category.name,
                    }
                    for category in categories
                ]
            },
            "Lấy danh mục thành công",
            200,
        )

    except Exception as error:
        print("LỖI GET CATEGORIES:", error)

        return response_error(
            str(error),
            500,
        )



@product_bp.route(
    "/categories/" "<int:category_id>/sub-categories",
    methods=["GET"],
)
def get_sub_categories(category_id):
    try:
        sub_categories = ProductService.get_sub_categories(category_id)

        return response_success(
            {
                "sub_categories": [
                    {
                        "sub_category_id": item.sub_category_id,
                        "category_id": item.category_id,
                        "name": item.name,
                    }
                    for item in sub_categories
                ]
            },
            "Lấy danh mục phụ thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            404,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy danh mục phụ",
            500,
        )



@product_bp.route(
    "/tags",
    methods=["GET"],
)
def get_all_tags():
    try:
        tags = ProductService.get_all_tags()

        return response_success(
            {
                "tags": [
                    {
                        "tag_id": tag.tag_id,
                        "name": tag.name,
                        "sub_category_id": tag.sub_category_id,
                    }
                    for tag in tags
                ]
            },
            "Lấy danh sách thẻ thành công",
            200,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy danh sách thẻ",
            500,
        )


@product_bp.route(
    "/sub-categories/" "<int:sub_category_id>/tags",
    methods=["GET"],
)
def get_tags_by_sub_category(sub_category_id):
    try:
        tags = ProductService.get_tags_by_sub_category(sub_category_id)

        return response_success(
            {
                "tags": [
                    {
                        "tag_id": tag.tag_id,
                        "sub_category_id": tag.sub_category_id,
                        "name": tag.name,
                    }
                    for tag in tags
                ]
            },
            "Lấy danh sách thẻ thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            404,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy danh sách thẻ",
            500,
        )


@product_bp.route(
    "/tags",
    methods=["POST"],
)
@jwt_required()
def create_tag():
    try:
        check_admin()

        data = request.get_json() or {}

        tag = ProductService.create_tag(
            name=data.get("name"),
            sub_category_id=data.get("sub_category_id"),
        )

        return response_success(
            {
                "tag": {
                    "tag_id": tag.tag_id,
                    "name": tag.name,
                    "sub_category_id": tag.sub_category_id,
                    "sub_category_name": (
                        tag.sub_category.name if tag.sub_category else None
                    ),
                    "category_id": (
                        tag.sub_category.category_id if tag.sub_category else None
                    ),
                    "category_name": (
                        tag.sub_category.category.name
                        if (tag.sub_category and tag.sub_category.category)
                        else None
                    ),
                }
            },
            "Tạo thẻ thành công",
            201,
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
            "Có lỗi xảy ra khi tạo thẻ",
            500,
        )
