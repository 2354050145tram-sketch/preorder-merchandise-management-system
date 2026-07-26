from sqlalchemy import Integer, Column, String, Enum, ForeignKey, DECIMAL
from config import db
from modules.base_model import BaseModel

class Product(BaseModel):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(255), nullable=False, unique=True)
    price = Column(DECIMAL(8,2), nullable=False)
    description = Column(String(255), nullable=False)
    image = Column(String(255), nullable=False)
    status = Column(Enum("PREORDER", "IN_STOCK"), nullable=False)

class Tag(BaseModel):
    __tablename__ = "tags"

    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)

class ProductTag(db.Model):
    __tablename__ = "product_tags"

    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.tag_id", ondelete="CASCADE"), primary_key=True)
