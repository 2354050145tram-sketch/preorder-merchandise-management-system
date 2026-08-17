from sqlalchemy import Integer, Column, String, DateTime, Enum, ForeignKey, DECIMAL
from config import db
from datetime import datetime, timezone
from modules.base_model import BaseModel


class Wallet(BaseModel):
    __tablename__ = "wallets"

    wallet_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    balance = Column(DECIMAL(15, 2), nullable=False, default=0)

    user = db.relationship("User", back_populates="wallet", uselist=False)
    transactions = db.relationship(
        "WalletTransaction", back_populates="wallet", cascade="all, delete-orphan"
    )


class WalletTransaction(db.Model):
    __tablename__ = "wallet_transactions"

    wallet_transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_id = Column(Integer, ForeignKey("wallets.wallet_id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)
    transaction_type = Column(
        Enum("NẠP TIỀN", "THANH TOÁN", "RÚT TIỀN", "HOÀN TIỀN"), nullable=False
    )
    amount = Column(DECIMAL(15, 2), nullable=False)
    balance_before = Column(DECIMAL(15, 2), nullable=False)
    balance_after = Column(DECIMAL(15, 2), nullable=False)
    transaction_status = Column(
        Enum("CHỜ XỬ LÝ", "THÀNH CÔNG", "THẤT BẠI", "ĐÃ HỦY"), nullable=False
    )
    transaction_code = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    wallet = db.relationship("Wallet", back_populates="transactions")
    order = db.relationship("Order", back_populates="wallet_transactions")
