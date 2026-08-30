from datetime import date

from sqlalchemy import select
from flask_jwt_extended import get_jwt_identity

from config import db
from modules.products.models import Tag, ProductTag
from modules.preorders.models import PreOrder
from modules.users.services import UserService


def serialize_product(product):

    stmt = (
        select(Tag)
        .join(ProductTag, Tag.tag_id == ProductTag.tag_id)
        .where(ProductTag.product_id == product.product_id, Tag.active.is_(True))
    )

    tags = db.session.scalars(stmt).all()

    unique_tags = {}

    for tag in tags:
        key = tag.name.strip().lower()

        if key not in unique_tags:
            unique_tags[key] = tag

    tags = list(unique_tags.values())

    active_preorder = None

    if product.status == "PREORDER":

        today = date.today()

        stmt = select(PreOrder).where(
            PreOrder.product_id == product.product_id,
            PreOrder.active.is_(True),
            PreOrder.start_date <= today,
            PreOrder.end_date >= today,
        )

        active_preorder = db.session.scalar(stmt)

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "price": float(product.price),
        "description": product.description,
        "image": product.image,
        "status": product.status,
        "active": product.active,
        "preorder_id": (active_preorder.preorder_id if active_preorder else None),
        "preorder_available": (active_preorder is not None),
        "tags": [{"tag_id": tag.tag_id, "name": tag.name} for tag in tags],
    }


def check_admin():

    current_user_id = int(get_jwt_identity())

    current_user = UserService.get_user_by_id(current_user_id, active=True)

    if current_user.role_id != 0:

        raise PermissionError("Không có quyền truy cập")

    return current_user
