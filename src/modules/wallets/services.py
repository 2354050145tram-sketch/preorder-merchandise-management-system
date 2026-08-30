from config import db
from decimal import Decimal, InvalidOperation
from sqlalchemy import select, func
from uuid import uuid4
from modules.wallets.models import Wallet, WalletTransaction
from modules.users.models import User
from modules.orders.models import Order, OrderItem, Payment


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
            valid_types = [
                "NẠP TIỀN",
                "THANH TOÁN",
                "RÚT TIỀN",
                "HOÀN TIỀN",
            ]

            if transaction_type not in valid_types:
                raise ValueError("Loại giao dịch không hợp lệ")

            stmt = stmt.where(WalletTransaction.transaction_type == transaction_type)

        if transaction_status:
            valid_statuses = [
                "CHỜ XỬ LÝ",
                "THÀNH CÔNG",
                "THẤT BẠI",
                "ĐÃ HỦY",
            ]

            if transaction_status not in valid_statuses:
                raise ValueError("Trạng thái giao dịch không hợp lệ")

            stmt = stmt.where(
                WalletTransaction.transaction_status == transaction_status
            )

        stmt = stmt.order_by(
            WalletTransaction.created_at.desc(),
            WalletTransaction.wallet_transaction_id.desc(),
        )

        return db.session.scalars(stmt).all()

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

        if not wallet or not wallet.active:
            raise ValueError("Ví không tồn tại")

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

        if not wallet or not wallet.active:
            raise ValueError("Ví không tồn tại")

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
    def pay_with_wallet(
        user_id,
        order_id,
        payment_type,
    ):
        from modules.orders.services import PaymentService

        wallet = WalletService.get_wallet_by_user(user_id)

        order = db.session.get(
            Order,
            order_id,
        )

        if not order or not order.active:
            raise ValueError("Đơn hàng không tồn tại")

        if order.user_id != user_id:
            raise ValueError("Đơn hàng không thuộc tài khoản này")

        if order.order_status == "ĐÃ HỦY":
            raise ValueError("Không thể thanh toán đơn hàng đã hủy")

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Đơn hàng đã hoàn thành")

        pending_payment = db.session.scalar(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.payment_status == "ĐANG THANH TOÁN",
            )
        )

        if pending_payment:
            raise ValueError("Đơn hàng đang có giao dịch " "thanh toán chưa hoàn tất")

        amount = PaymentService.calculate_payment_amount(
            order_id=order_id,
            payment_type=payment_type,
        )

        amount = Decimal(str(amount))

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Số tiền thanh toán không hợp lệ")

        balance_before = Decimal(str(wallet.balance))

        if balance_before < amount:
            raise ValueError("Số dư Ví Verd không đủ")

        balance_after = balance_before - amount

        transaction_code = str(uuid4())

        wallet_transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            order_id=order_id,
            transaction_type="THANH TOÁN",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            transaction_status="THÀNH CÔNG",
            transaction_code=transaction_code,
            description=(f"{payment_type} đơn hàng " f"#{order_id} bằng Ví Verd"),
        )

        payment = Payment(
            order_id=order_id,
            amount=amount,
            payment_method="VÍ VERD",
            payment_type=payment_type,
            payment_status="ĐANG THANH TOÁN",
            transaction_id=transaction_code,
        )

        try:
            wallet.balance = balance_after

            db.session.add(wallet_transaction)

            db.session.add(payment)

            db.session.flush()

            PaymentService.apply_successful_payment(payment)

            db.session.commit()

            return wallet_transaction

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def refund_to_wallet(order_id, order_item_id, amount, description=None):
        order = db.session.get(Order, order_id)

        if not order or not order.active:
            raise ValueError("Đơn hàng không tồn tại")

        order_item = db.session.get(OrderItem, order_item_id)

        if not order_item or order_item.order_id != order_id:
            raise ValueError("Sản phẩm trong đơn hàng không tồn tại")

        existing_refund = db.session.scalar(
            select(WalletTransaction).where(
                WalletTransaction.order_item_id == order_item_id,
                WalletTransaction.transaction_type == "HOÀN TIỀN",
                WalletTransaction.transaction_status == "THÀNH CÔNG",
            )
        )

        if existing_refund:
            raise ValueError("Sản phẩm đã được hoàn tiền")

        wallet = WalletService.get_wallet_by_user(order.user_id)

        try:
            amount = Decimal(str(amount))

        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Số tiền hoàn không hợp lệ")

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Số tiền hoàn phải lớn hơn 0")

        paid_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.order_id == order_id,
            Payment.payment_status.in_(["ĐÃ THANH TOÁN", "ĐÃ HOÀN TIỀN"]),
        )

        total_paid = db.session.scalar(paid_stmt)

        total_paid = Decimal(str(total_paid))

        if total_paid <= 0:
            raise ValueError("Đơn hàng chưa được thanh toán")

        refunded_stmt = select(
            func.coalesce(func.sum(WalletTransaction.amount), 0)
        ).where(
            WalletTransaction.order_id == order_id,
            WalletTransaction.transaction_type == "HOÀN TIỀN",
            WalletTransaction.transaction_status == "THÀNH CÔNG",
        )

        total_refunded = db.session.scalar(refunded_stmt)

        total_refunded = Decimal(str(total_refunded))

        refundable_amount = total_paid - total_refunded

        if refundable_amount <= 0:
            raise ValueError("Đơn hàng đã được hoàn tiền đầy đủ")

        if amount > refundable_amount:
            raise ValueError("Số tiền hoàn vượt quá số tiền có thể hoàn")

        balance_before = wallet.balance
        balance_after = balance_before + amount

        wallet.balance = balance_after

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            order_id=order_id,
            order_item_id=order_item_id,
            transaction_type="HOÀN TIỀN",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            transaction_status="THÀNH CÔNG",
            transaction_code=str(uuid4()),
            description=(description or f"Hoàn tiền đơn hàng #{order_id}"),
        )

        if amount == refundable_amount:
            payment_stmt = select(Payment).where(
                Payment.order_id == order_id, Payment.payment_status == "ĐÃ THANH TOÁN"
            )

            payments = db.session.scalars(payment_stmt).all()

            for payment in payments:
                payment.payment_status = "ĐÃ HOÀN TIỀN"

        try:
            db.session.add(transaction)

            db.session.commit()

            return transaction

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def create_deposit_request(user_id, amount, description=None):
        wallet = WalletService.get_wallet_by_user(user_id)

        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Số tiền nạp không hợp lệ")

        if not amount.is_finite() or amount <= 0:
            raise ValueError("Số tiền nạp phải lớn hơn 0")

        import time

        trans_code = f"NAP_{user_id}_{int(time.time())}"

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            transaction_type="NẠP TIỀN",
            amount=amount,
            balance_before=wallet.balance,
            balance_after=wallet.balance,
            transaction_status="CHỜ XỬ LÝ",
            transaction_code=trans_code,
            description=description or f"Nạp tiền Ví Verd (Mã: {trans_code})",
        )

        try:
            db.session.add(transaction)
            db.session.commit()
            return transaction
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_deposit_by_id(user_id, wallet_transaction_id):
        wallet = WalletService.get_wallet_by_user(user_id)
        stmt = select(WalletTransaction).where(
            WalletTransaction.wallet_transaction_id == wallet_transaction_id,
            WalletTransaction.wallet_id == wallet.wallet_id,
            WalletTransaction.transaction_type == "NẠP TIỀN",
        )
        transaction = db.session.scalar(stmt)
        if not transaction:
            raise ValueError("Yêu cầu nạp tiền không tồn tại")
        return transaction

    @staticmethod
    def cancel_deposit_request(user_id, wallet_transaction_id):
        wallet = WalletService.get_wallet_by_user(user_id)
        transaction = db.session.get(WalletTransaction, wallet_transaction_id)

        if not transaction or transaction.wallet_id != wallet.wallet_id:
            raise ValueError("Giao dịch không tồn tại")

        if transaction.transaction_type != "NẠP TIỀN":
            raise ValueError("Giao dịch không phải yêu cầu nạp tiền")

        if transaction.transaction_status != "CHỜ XỬ LÝ":
            raise ValueError("Không thể hủy giao dịch đã được xử lý")

        transaction.transaction_status = "ĐÃ HỦY"
        try:
            db.session.commit()
            return transaction
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all_deposits_admin(status=None):
        stmt = (
            select(WalletTransaction, User)
            .join(Wallet, WalletTransaction.wallet_id == Wallet.wallet_id)
            .join(User, Wallet.user_id == User.user_id)
            .where(WalletTransaction.transaction_type == "NẠP TIỀN")
        )
        if status:
            stmt = stmt.where(WalletTransaction.transaction_status == status)

        stmt = stmt.order_by(
            WalletTransaction.created_at.desc(),
            WalletTransaction.wallet_transaction_id.desc(),
        )
        results = db.session.execute(stmt).all()

        deposits = []
        for trans, user in results:
            deposits.append(
                {
                    "wallet_transaction_id": trans.wallet_transaction_id,
                    "wallet_id": trans.wallet_id,
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "amount": float(trans.amount),
                    "balance_before": float(trans.balance_before),
                    "balance_after": float(trans.balance_after),
                    "transaction_status": trans.transaction_status,
                    "transaction_code": trans.transaction_code,
                    "description": trans.description,
                    "created_at": (
                        trans.created_at.isoformat() if trans.created_at else None
                    ),
                }
            )
        return deposits