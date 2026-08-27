from sqlalchemy import select
from flask_jwt_extended import get_jwt_identity
from config import db
from modules.products.models import Tag, ProductTag
from modules.users.services import UserService


def serialize_product(product):
    stmt = (
        select(Tag)
        .join(
            ProductTag,
            Tag.tag_id == ProductTag.tag_id
        )
        .where(
            ProductTag.product_id == product.product_id,
            Tag.active.is_(True)
        )
    )

    tags = db.session.scalars(
        stmt
    ).all()

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "price": float(product.price),
        "description": product.description,
        "image": product.image,
        "status": product.status,
        "active": product.active,
        "tags": [
            {
                "tag_id": tag.tag_id,
                "name": tag.name
            }
            for tag in tags
        ]
    }


def check_admin():
    current_user_id = int(
        get_jwt_identity()
    )

    current_user = UserService.get_user_by_id(
        current_user_id,
        active=True
    )

    if current_user.role_id != 0:
        raise PermissionError(
            "Không có quyền truy cập"
        )

    return current_user