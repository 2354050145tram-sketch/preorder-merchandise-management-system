from sqlalchemy import Integer, Column, String, Enum, ForeignKey, Date
from config import db
from modules.base_model import BaseModel

class PreOrder(BaseModel):
    __tablename__ = "preorders"

    preorder_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    quantity_order = Column(Integer, nullable=False)
    progress_status = Column(Enum("MỞ PREORDER", "ĐÃ ĐẶT HÀNG", "ĐANG SẢN XUẤT", "ĐÃ VỀ KHO TRUNG QUỐC", "ĐÃ VỀ KHO VIỆT NAM", "ĐANG GÓI HÀNG", "ĐÃ VẬN CHUYỂN", "HOÀN THÀNH"), nullable=False)
    progress_note = Column(String(255), nullable=False)

    order_items = db.relationship("OrderItem", back_populates="preorder")
    notifications = db.relationship("Notification", back_populates="preorder")

    def __str__(self):
        return self.name
