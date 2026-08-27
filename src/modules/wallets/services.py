from config import db
from decimal import Decimal, InvalidOperation
from sqlalchemy import select
from uuid import uuid4
from modules.wallets.models import Wallet, WalletTransaction
from modules.users.models import User
from modules.orders.models import Order


class WalletService:

    @staticmethod
    def create_wallet(user_id):
        user = db.session.get(User, user_id)

        if not user or not user.active:
            raise ValueError("User không tồn tại")

        stmt = select(Wallet).where(Wallet.user_id == user_id)

        existing_wallet = db.session.scalar(stmt)

        if existing_wallet:
            raise ValueError("User đã có ví")

        wallet = Wallet(user_id=user_id, balance=Decimal("0"))

        try:
            db.session.add(wallet)
            db.session.commit()

            return wallet

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_wallet_by_user(user_id):
        stmt = select(Wallet).where(Wallet.user_id == user_id, Wallet.active.is_(True))

        wallet = db.session.scalar(stmt)

        if not wallet:
            raise ValueError("Ví không tồn tại")

        return wallet

    @staticmethod
    def get_transactions(user_id, transaction_type=None, transaction_status=None):
        wallet = WalletService.get_wallet_by_user(user_id)

        stmt = select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.wallet_id
        )

        if transaction_type:
            valid_types = ["NẠP TIỀN", "THANH TOÁN", "RÚT TIỀN", "HOÀN TIỀN"]

            if transaction_type not in valid_types:
                raise ValueError("Loại giao dịch không hợp lệ")

            stmt = stmt.where(WalletTransaction.transaction_type == transaction_type)

        if transaction_status:
            valid_statuses = ["CHỜ XỬ LÝ", "THÀNH CÔNG", "THẤT BẠI", "ĐÃ HỦY"]

            if transaction_status not in valid_statuses:
                raise ValueError("Trạng thái giao dịch không hợp lệ")

            stmt = stmt.where(
                WalletTransaction.transaction_status == transaction_status
            )

        return db.session.scalars(stmt).all()

    @staticmethod
    def create_deposit_request(user_id, amount, description=None):
        wallet = WalletService.get_wallet_by_user(user_id)

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Số tiền nạp không hợp lệ")

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Số tiền nạp phải lớn hơn 0")

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            transaction_type="NẠP TIỀN",
            amount=amount,
            balance_before=wallet.balance,
            balance_after=wallet.balance,
            transaction_status="CHỜ XỬ LÝ",
            transaction_code=str(uuid4()),
            description=description,
        )

        try:
            db.session.add(transaction)
            db.session.commit()

            return transaction

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def approve_deposit(wallet_transaction_id):
        transaction = db.session.get(WalletTransaction, wallet_transaction_id)

        if not transaction:
            raise ValueError("Giao dịch không tồn tại")

        if transaction.transaction_type != "NẠP TIỀN":
            raise ValueError("Giao dịch không phải yêu cầu nạp tiền")

        if transaction.transaction_status != "CHỜ XỬ LÝ":
            raise ValueError("Giao dịch đã được xử lý")

        wallet = db.session.get(Wallet, transaction.wallet_id)

        balance_before = wallet.balance
        balance_after = balance_before + transaction.amount

        wallet.balance = balance_after

        transaction.balance_before = balance_before
        transaction.balance_after = balance_after
        transaction.transaction_status = "THÀNH CÔNG"

        try:
            db.session.commit()

            return transaction

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def create_withdraw_request(user_id, amount, description=None):
        wallet = WalletService.get_wallet_by_user(user_id)

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Số tiền rút không hợp lệ")

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Số tiền rút phải lớn hơn 0")

        if wallet.balance < amount:
            raise ValueError("Số dư ví không đủ")

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            transaction_type="RÚT TIỀN",
            amount=amount,
            balance_before=wallet.balance,
            balance_after=wallet.balance,
            transaction_status="CHỜ XỬ LÝ",
            transaction_code=str(uuid4()),
            description=description,
        )

        try:
            db.session.add(transaction)
            db.session.commit()

            return transaction

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def approve_withdraw(wallet_transaction_id):
        transaction = db.session.get(WalletTransaction, wallet_transaction_id)

        if not transaction:
            raise ValueError("Giao dịch không tồn tại")

        if transaction.transaction_type != "RÚT TIỀN":
            raise ValueError("Giao dịch không phải yêu cầu rút tiền")

        if transaction.transaction_status != "CHỜ XỬ LÝ":
            raise ValueError("Giao dịch đã được xử lý")

        wallet = db.session.get(Wallet, transaction.wallet_id)

        if wallet.balance < transaction.amount:
            transaction.transaction_status = "THẤT BẠI"

            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

            raise ValueError("Số dư ví không đủ")

        balance_before = wallet.balance
        balance_after = balance_before - transaction.amount

        wallet.balance = balance_after

        transaction.balance_before = balance_before
        transaction.balance_after = balance_after
        transaction.transaction_status = "THÀNH CÔNG"

        try:
            db.session.commit()

            return transaction

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def pay_with_wallet(user_id, order_id, amount):
        wallet = WalletService.get_wallet_by_user(user_id)

        order = db.session.get(Order, order_id)

        if not order or not order.active:
            raise ValueError("Đơn hàng không tồn tại")

        if order.user_id != user_id:
            raise ValueError("Đơn hàng không thuộc tài khoản này")

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Số tiền thanh toán không hợp lệ")

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Số tiền thanh toán phải lớn hơn 0")

        if wallet.balance < amount:
            raise ValueError("Số dư ví không đủ")

        balance_before = wallet.balance
        balance_after = balance_before - amount

        wallet.balance = balance_after

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            order_id=order_id,
            transaction_type="THANH TOÁN",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            transaction_status="THÀNH CÔNG",
            transaction_code=str(uuid4()),
            description=f"Thanh toán đơn hàng #{order_id}",
        )

        try:
            db.session.add(transaction)
            db.session.commit()

            return transaction

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def refund_to_wallet(user_id, order_id, amount, description=None):
        wallet = WalletService.get_wallet_by_user(user_id)

        order = db.session.get(Order, order_id)

        if not order:
            raise ValueError("Đơn hàng không tồn tại")

        if order.user_id != user_id:
            raise ValueError("Đơn hàng không thuộc tài khoản này")

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Số tiền hoàn không hợp lệ")

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Số tiền hoàn phải lớn hơn 0")

        balance_before = wallet.balance
        balance_after = balance_before + amount

        wallet.balance = balance_after

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            order_id=order_id,
            transaction_type="HOÀN TIỀN",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            transaction_status="THÀNH CÔNG",
            transaction_code=str(uuid4()),
            description=(description or f"Hoàn tiền đơn hàng #{order_id}"),
        )

        try:
            db.session.add(transaction)
            db.session.commit()

            return transaction

        except Exception:
            db.session.rollback()
            raise
