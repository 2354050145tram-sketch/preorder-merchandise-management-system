from sqlalchemy import Integer, Column, ForeignKey, DateTime, UniqueConstraint
from datetime import datetime, timezone
from config import db


class Cart(db.Model):
    __tablename__ = "carts"

    cart_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = db.relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )
    user = db.relationship("User", back_populates="cart")


class CartItem(db.Model):
    __tablename__ = "cart_items"

    __table_args__ = (UniqueConstraint("cart_id", "product_id", "preorder_id", name="uq_cart_product_preorder"),)

    cart_item_id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("carts.cart_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    preorder_id = Column(Integer, ForeignKey("preorders.preorder_id"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product", back_populates="cart_items")
    preorder = db.relationship("PreOrder", back_populates="cart_items")