from sqlalchemy import Integer, Column, ForeignKey, DECIMAL, Enum, DateTime
from config import db
from datetime import datetime, timezone
from modules.base_model import BaseModel


class Inventory(BaseModel):
    __tablename__ = "inventories"

    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(
        Integer, ForeignKey("products.product_id"), nullable=False, unique=True
    )
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(8, 2), nullable=False)

    product = db.relationship("Product", back_populates="inventories")
    transactions = db.relationship(
        "InventoryTransaction", back_populates="inventory", cascade="all, delete-orphan"
    )

    @property
    def status(self):
        if self.quantity <= 0:
            return "HẾT HÀNG"

        if self.quantity <= 5:
            return "SẮP HẾT HÀNG"

        return "CÒN HÀNG"


class InventoryTransaction(db.Model):
    __tablename__ = "inventory_transactions"

    inventory_transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    inventory_id = Column(
        Integer, ForeignKey("inventories.inventory_id"), nullable=False
    )
    transaction_type = Column(
        Enum("NHẬP", "XUẤT", "ĐIỀU CHỈNH", "HOÀN KHO"), nullable=False
    )
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(8, 2), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    inventory = db.relationship("Inventory", back_populates="transactions")
