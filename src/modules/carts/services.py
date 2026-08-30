from datetime import date

from sqlalchemy import select

from config import db

from modules.carts.models import (
    Cart,
    CartItem,
)

from modules.products.models import Product
from modules.preorders.models import PreOrder
from modules.inventories.models import Inventory
from modules.users.services import UserService


class CartService:

    @staticmethod
    def get_or_create_cart(user_id):
        UserService.get_user_by_id(
            user_id,
            active=True
        )

        stmt = select(Cart).where(
            Cart.user_id == user_id
        )

        cart = db.session.scalar(stmt)

        if cart:
            return cart

        cart = Cart(
            user_id=user_id
        )

        try:
            db.session.add(cart)
            db.session.commit()

            return cart

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_cart(user_id):
        cart = CartService.get_or_create_cart(
            user_id
        )

        return cart

    @staticmethod
    def add_item(
        user_id,
        product_id,
        quantity=1,
    ):
        cart = CartService.get_or_create_cart(
            user_id
        )

        product = db.session.get(
            Product,
            product_id
        )

        if (
            not product
            or not product.active
        ):
            raise ValueError(
                "Sản phẩm không tồn tại"
            )

        try:
            quantity = int(quantity)

        except (TypeError, ValueError):
            raise ValueError(
                "Số lượng không hợp lệ"
            )

        if quantity <= 0:
            raise ValueError(
                "Số lượng phải lớn hơn 0"
            )

        preorder_id = None


        if product.status == "IN_STOCK":
            stmt = select(Inventory).where(
                Inventory.product_id
                == product_id,
                Inventory.active.is_(True)
            )

            inventory = db.session.scalar(
                stmt
            )

            if not inventory:
                raise ValueError(
                    "Sản phẩm chưa có tồn kho"
                )

            if inventory.quantity <= 0:
                raise ValueError(
                    "Sản phẩm đã hết hàng"
                )


        elif product.status == "PREORDER":
            stmt = select(PreOrder).where(
                PreOrder.product_id
                == product_id,
                PreOrder.active.is_(True)
            )

            preorder = db.session.scalar(
                stmt
            )

            if not preorder:
                raise ValueError(
                    "Sản phẩm hiện không có đợt preorder"
                )

            today = date.today()

            if (
                today < preorder.start_date
                or today > preorder.end_date
            ):
                raise ValueError(
                    "Đợt preorder hiện không mở"
                )

            preorder_id = (
                preorder.preorder_id
            )

        else:
            raise ValueError(
                "Trạng thái sản phẩm không hợp lệ"
            )


        stmt = select(CartItem).where(
            CartItem.cart_id
            == cart.cart_id,

            CartItem.product_id
            == product_id,

            CartItem.preorder_id
            == preorder_id,
        )

        existing_item = db.session.scalar(
            stmt
        )

        if existing_item:
            new_quantity = (
                existing_item.quantity
                + quantity
            )

            if product.status == "IN_STOCK":
                inventory = db.session.scalar(
                    select(Inventory).where(
                        Inventory.product_id
                        == product_id,
                        Inventory.active.is_(True)
                    )
                )

                if (
                    inventory.quantity
                    < new_quantity
                ):
                    raise ValueError(
                        "Số lượng vượt quá tồn kho"
                    )

            existing_item.quantity = (
                new_quantity
            )

            try:
                db.session.commit()

                return existing_item

            except Exception:
                db.session.rollback()
                raise

        if product.status == "IN_STOCK":
            inventory = db.session.scalar(
                select(Inventory).where(
                    Inventory.product_id
                    == product_id,
                    Inventory.active.is_(True)
                )
            )

            if inventory.quantity < quantity:
                raise ValueError(
                    "Số lượng vượt quá tồn kho"
                )

        item = CartItem(
            cart_id=cart.cart_id,
            product_id=product_id,
            preorder_id=preorder_id,
            quantity=quantity,
        )

        try:
            db.session.add(item)
            db.session.commit()

            return item

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_quantity(
        user_id,
        cart_item_id,
        quantity,
    ):
        cart = CartService.get_cart(
            user_id
        )

        item = db.session.get(
            CartItem,
            cart_item_id
        )

        if (
            not item
            or item.cart_id
            != cart.cart_id
        ):
            raise ValueError(
                "Sản phẩm trong giỏ hàng không tồn tại"
            )

        try:
            quantity = int(quantity)

        except (TypeError, ValueError):
            raise ValueError(
                "Số lượng không hợp lệ"
            )

        if quantity <= 0:
            raise ValueError(
                "Số lượng phải lớn hơn 0"
            )

        product = item.product

        if product.status == "IN_STOCK":
            inventory = db.session.scalar(
                select(Inventory).where(
                    Inventory.product_id
                    == item.product_id,
                    Inventory.active.is_(True)
                )
            )

            if not inventory:
                raise ValueError(
                    "Sản phẩm chưa có tồn kho"
                )

            if quantity > inventory.quantity:
                raise ValueError(
                    "Số lượng vượt quá tồn kho"
                )

        elif product.status == "PREORDER":
            preorder = item.preorder

            if (
                not preorder
                or not preorder.active
            ):
                raise ValueError(
                    "Đợt preorder đã đóng"
                )

            today = date.today()

            if (
                today < preorder.start_date
                or today > preorder.end_date
            ):
                raise ValueError(
                    "Đợt preorder hiện không mở"
                )

        item.quantity = quantity

        try:
            db.session.commit()

            return item

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def remove_item(
        user_id,
        cart_item_id,
    ):
        cart = CartService.get_cart(
            user_id
        )

        item = db.session.get(
            CartItem,
            cart_item_id
        )

        if (
            not item
            or item.cart_id
            != cart.cart_id
        ):
            raise ValueError(
                "Sản phẩm trong giỏ hàng không tồn tại"
            )

        try:
            db.session.delete(item)
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def clear_cart(user_id):
        cart = CartService.get_cart(
            user_id
        )

        try:
            for item in list(cart.items):
                db.session.delete(item)

            db.session.commit()

        except Exception:
            db.session.rollback()
            raise