from sqlalchemy import Integer, Column, String, Enum, ForeignKey, DECIMAL, Date, Boolean, DateTime
from config import db
from datetime import datetime, timezone

class Order(db.Model):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    order_date = Column(Date, nullable=False)
    total_amount = Column(DECIMAL(8,2), nullable=False)
    order_status = Column(Enum("CHỜ XÁC NHẬN","ĐÃ XÁC NHẬN","ĐANG XỬ LÝ","HOÀN THÀNH","ĐÃ HỦY"), nullable=False, default="CHỜ XÁC NHẬN")
    shipping_fee = Column(DECIMAL(8,2), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="orders")
    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    wallet_transactions = db.relationship("WalletTransaction", back_populates="order")

class OrderItem(db.Model):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    preorder_id = Column(Integer, ForeignKey("preorders.preorder_id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(8,2), nullable=False)
    item_status = Column(Enum("ĐANG XỬ LÝ", "HOÀN THÀNH", "ĐÃ HỦY"), nullable=False, default="ĐANG XỬ LÝ")
    shipping_method = Column(Enum("TIÊU CHUẨN","GIAO NHANH"), nullable=True)
    tracking_code = Column(String(255), nullable=True)
    shipping_status = Column(Enum("ĐANG LẤY HÀNG","ĐANG GIAO HÀNG","ĐÃ GIAO"), nullable=True)

    order = db.relationship("Order", back_populates="order_items")
    product = db.relationship("Product", back_populates="order_items")
    preorder = db.relationship("PreOrder", back_populates="order_items")

class Payment(db.Model):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    amount = Column(DECIMAL(8,2), nullable=False)
    payment_method = Column(Enum("MOMO", "VÍ VERD"), nullable=False)
    payment_status = Column(Enum("ĐANG THANH TOÁN","ĐÃ THANH TOÁN","ĐÃ HỦY","ĐÃ HOÀN TIỀN"), nullable=False)
    transaction_id = Column(String(255), nullable=False, unique=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    order = db.relationship("Order", back_populates="payments")