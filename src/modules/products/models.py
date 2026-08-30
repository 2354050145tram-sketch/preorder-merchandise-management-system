from sqlalchemy import (
    Integer,
    Column,
    String,
    Enum,
    ForeignKey,
    DECIMAL,
    Boolean,
    UniqueConstraint,
)

from config import db
from modules.base_model import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)

    product_name = Column(String(255), nullable=False, unique=True)

    price = Column(DECIMAL(8, 2), nullable=False)

    description = Column(String(255), nullable=False)

    image = Column(String(255), nullable=False)

    status = Column(Enum("PREORDER", "IN_STOCK"), nullable=False)

    order_items = db.relationship("OrderItem", back_populates="product")

    inventories = db.relationship(
        "Inventory", back_populates="product", cascade="all, delete-orphan"
    )

    preorders = db.relationship("PreOrder", back_populates="product")

    cart_items = db.relationship("CartItem", back_populates="product")

    def __str__(self):
        return self.product_name


class Category(db.Model):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    active = Column(Boolean, nullable=False, default=True)

    sub_categories = db.relationship("SubCategory", back_populates="category")

    def __str__(self):
        return self.name


class SubCategory(db.Model):
    __tablename__ = "sub_categories"

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_sub_category_name"),
    )

    sub_category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    name = Column(String(100), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    category = db.relationship("Category", back_populates="sub_categories")
    tags = db.relationship("Tag", back_populates="sub_category")

    def __str__(self):
        return self.name


class Tag(BaseModel):
    __tablename__ = "tags"

    __table_args__ = (
        UniqueConstraint("sub_category_id", "name", name="uq_tag_sub_category_name"),
    )

    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    sub_category_id = Column(
        Integer, ForeignKey("sub_categories.sub_category_id"), nullable=True
    )
    name = Column(String(255), nullable=False)

    sub_category = db.relationship("SubCategory", back_populates="tags")

    def __str__(self):
        return self.name


class ProductTag(db.Model):
    __tablename__ = "product_tags"

    product_id = Column(
        Integer, ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True
    )
    tag_id = Column(
        Integer, ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True
    )
