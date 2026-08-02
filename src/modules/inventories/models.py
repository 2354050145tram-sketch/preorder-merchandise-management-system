from sqlalchemy import Integer, Column, ForeignKey, DECIMAL
from config import db
from modules.base_model import BaseModel

class Inventory(BaseModel):
    __tablename__ = "inventories"

    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(8,2), nullable=False)

    product = db.relationship("Product", back_populates="inventories")

    @property
    def status(self):
        if self.quantity <= 0:
            return "HẾT HÀNG"

        if self.quantity <= 5:
            return "SẮP HẾT HÀNG"

        return "CÒN HÀNG"