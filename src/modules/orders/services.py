from config import db
from decimal import Decimal
from datetime import date, datetime, timezone, time
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from modules.orders.models import Order, OrderItem, Payment
from modules.users.models import User
from modules.products.models import Product
from modules.preorders.models import PreOrder
from modules.inventories.models import Inventory, InventoryTransaction
from modules.wallets.models import WalletTransaction
from modules.wallets.services import WalletService


class OrderService:

    @staticmethod
    def create_order(user_id, items):
        user = db.session.get(User, user_id)

        if not user or not user.active:
            raise ValueError("Người dùng không tồn tại")

        if not items:
            raise ValueError("Vui lòng chọn sản phẩm cần đặt hàng")

        total_amount = Decimal("0")
        order_items_data = []
        seen_items = set()

        for item in items:

            product_id = item.get("product_id")
            preorder_id = item.get("preorder_id")
            quantity = item.get("quantity")

            item_key = (product_id, preorder_id)

            if item_key in seen_items:
                raise ValueError("Sản phẩm bị trùng trong đơn hàng")

            seen_items.add(item_key)

            if not product_id or not quantity:
                raise ValueError("Thông tin sản phẩm không hợp lệ")

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                raise ValueError("Số lượng sản phẩm không hợp lệ")

            if quantity <= 0:
                raise ValueError("Số lượng sản phẩm phải lớn hơn 0")

            product = db.session.get(Product, product_id)

            if not product or not product.active:
                raise ValueError("Sản phẩm không tồn tại")

            if preorder_id is not None:
                preorder = db.session.get(PreOrder, preorder_id)

                if (
                    not preorder
                    or not preorder.active
                    or preorder.product_id != product_id
                ):
                    raise ValueError("Đợt preorder không hợp lệ")

                today = date.today()

                if today < preorder.start_date or today > preorder.end_date:
                    raise ValueError(
                        f"{product.product_name} " "hiện không có đợt preorder"
                    )

            if item["preorder_id"] is not None:
                pass

            else:
                if product.status == "PREORDER":
                    raise ValueError(
                        f"{product.product_name} " "phải được đặt theo đợt preorder"
                    )

                stmt = select(Inventory).where(
                    Inventory.product_id == product_id, Inventory.active.is_(True)
                )

                inventory = db.session.scalar(stmt)

                if not inventory:
                    raise ValueError("Sản phẩm chưa có tồn kho")

                if inventory.quantity < quantity:
                    raise ValueError("Sản phẩm không đủ số lượng")

            item_total = product.price * quantity

            total_amount += item_total

            order_items_data.append(
                {
                    "product_id": product_id,
                    "preorder_id": preorder_id,
                    "quantity": quantity,
                    "price": product.price,
                }
            )

        order = Order(
            user_id=user_id,
            order_date=date.today(),
            total_amount=total_amount,
            order_status="CHỜ XÁC NHẬN",
            shipping_fee=Decimal("0"),
        )

        try:
            db.session.add(order)
            db.session.flush()

            for item in order_items_data:

                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=item["product_id"],
                    preorder_id=item["preorder_id"],
                    quantity=item["quantity"],
                    price=item["price"],
                )

                db.session.add(order_item)

                if item["preorder_id"] is None:
                    stmt = select(Inventory).where(
                        Inventory.product_id == item["product_id"]
                    )

                    inventory = db.session.scalar(stmt)

                    inventory.quantity -= item["quantity"]

                    inventory_transaction = InventoryTransaction(
                        inventory_id=inventory.inventory_id,
                        transaction_type="XUẤT",
                        quantity=item["quantity"],
                        price=None,
                    )

                    db.session.add(inventory_transaction)

            db.session.commit()

            return order

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all_orders(keyword=None, order_status=None, active=True):
        stmt = select(Order).options(joinedload(Order.user))

        if active is not None:
            stmt = stmt.where(Order.active == active)

        if keyword and keyword.strip():
            kw = keyword.strip()
            if kw.isdigit():
                stmt = stmt.join(User, Order.user_id == User.user_id).where(
                    (Order.order_id == int(kw))
                    | (User.username.ilike(f"%{kw}%"))
                    | (User.email.ilike(f"%{kw}%"))
                )
            else:
                stmt = stmt.join(User, Order.user_id == User.user_id).where(
                    (User.username.ilike(f"%{kw}%")) | (User.email.ilike(f"%{kw}%"))
                )
        else:
            stmt = stmt.join(User, Order.user_id == User.user_id)

        if order_status:
            stmt = stmt.where(Order.order_status == order_status)

        stmt = stmt.order_by(Order.order_id.desc())

        return db.session.scalars(stmt).unique().all()

    @staticmethod
    def get_order_by_id(order_id):
        order = db.session.get(Order, order_id)

        if not order or not order.active:
            raise ValueError("Đơn hàng không tồn tại")

        return order

    @staticmethod
    def get_orders_by_user(user_id):
        stmt = select(Order).where(Order.user_id == user_id, Order.active.is_(True))

        return db.session.scalars(stmt).all()

    @staticmethod
    def update_order_status(order_id, order_status):
        order = OrderService.get_order_by_id(order_id)

        if order.order_status == "ĐÃ HỦY":
            raise ValueError("Đơn hàng đã bị hủy")

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Đơn hàng đã hoàn thành")

        allowed_transitions = {
            "CHỜ XÁC NHẬN": ["ĐÃ XÁC NHẬN", "ĐÃ HỦY"],
            "ĐÃ ĐẶT CỌC": ["ĐANG XỬ LÝ", "ĐÃ XÁC NHẬN", "ĐÃ HỦY"],
            "ĐÃ XÁC NHẬN": ["ĐANG XỬ LÝ", "ĐÃ HỦY"],
            "ĐANG XỬ LÝ": ["HOÀN THÀNH", "ĐÃ HỦY"],
        }

        allowed_statuses = allowed_transitions.get(order.order_status, [])

        if order_status not in allowed_statuses:
            raise ValueError("Không thể chuyển trạng thái đơn hàng này")

        if order_status == "ĐÃ XÁC NHẬN":
            summary = PaymentService.get_order_payment_summary(order_id)
            if summary["remaining_amount"] > 0:
                import time

                auto_payment = Payment(
                    order_id=order_id,
                    amount=summary["remaining_amount"],
                    payment_method="MOMO",
                    payment_type="THANH TOÁN FULL",
                    payment_status="ĐANG THANH TOÁN",
                    transaction_id=f"ADMIN_CONFIRM_{order_id}_{int(time.time())}",
                )
                db.session.add(auto_payment)
                db.session.flush()
                PaymentService.apply_successful_payment(auto_payment)

        order.order_status = order_status
        try:
            db.session.commit()
            return order
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_shipping_info(
        order_id, order_item_ids, shipping_method, shipping_fee, tracking_code
    ):
        order = OrderService.get_order_by_id(order_id)

        if shipping_method not in ["TIÊU CHUẨN", "GIAO NHANH"]:
            raise ValueError("Phương thức vận chuyển không hợp lệ")

        try:
            shipping_fee = Decimal(str(shipping_fee))
        except Exception:
            raise ValueError("Phí vận chuyển không hợp lệ")

        if shipping_fee < 0:
            raise ValueError("Phí vận chuyển không được nhỏ hơn 0")

        tracking_code = tracking_code.strip() if tracking_code else ""

        if not tracking_code:
            raise ValueError("Mã vận đơn không được để trống")

        existing_tracking = db.session.scalar(
            select(OrderItem).where(OrderItem.tracking_code == tracking_code)
        )

        if existing_tracking:
            raise ValueError("Mã vận đơn đã tồn tại")

        if not order_item_ids:
            raise ValueError("Chưa chọn sản phẩm cần vận chuyển")

        stmt = select(OrderItem).where(
            OrderItem.order_item_id.in_(order_item_ids), OrderItem.order_id == order_id
        )

        order_items = db.session.scalars(stmt).all()

        if len(order_items) != len(set(order_item_ids)):
            raise ValueError("Sản phẩm trong đơn hàng không hợp lệ")

        for item in order_items:
            if item.item_status == "ĐÃ HỦY":
                raise ValueError("Không thể vận chuyển sản phẩm đã hủy")

            if item.tracking_code is not None:
                raise ValueError("Sản phẩm đã có thông tin vận chuyển")

        try:
            for item in order_items:
                item.shipping_method = shipping_method

                item.tracking_code = tracking_code

                item.shipping_status = "ĐANG LẤY HÀNG"

            order.shipping_fee += shipping_fee

            db.session.commit()

            return order_items

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_shipping_status(tracking_code, shipping_status):
        valid_statuses = ["ĐANG LẤY HÀNG", "ĐANG GIAO HÀNG", "ĐÃ GIAO"]

        if shipping_status not in valid_statuses:
            raise ValueError("Trạng thái vận chuyển không hợp lệ")

        stmt = select(OrderItem).where(OrderItem.tracking_code == tracking_code)

        order_items = db.session.scalars(stmt).all()

        if not order_items:
            raise ValueError("Mã vận đơn không tồn tại")

        status_order = {"ĐANG LẤY HÀNG": 1, "ĐANG GIAO HÀNG": 2, "ĐÃ GIAO": 3}

        for item in order_items:
            current_status = item.shipping_status

            if current_status is None:
                raise ValueError("Sản phẩm chưa có thông tin vận chuyển")

            if status_order[shipping_status] < status_order[current_status]:
                raise ValueError("Không thể cập nhật lùi trạng thái vận chuyển")

        try:
            for item in order_items:
                item.shipping_status = shipping_status

                if shipping_status == "ĐÃ GIAO":
                    item.item_status = "HOÀN THÀNH"

            db.session.commit()

            return order_items

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def cancel_order_item(order_item_id):
        order_item = db.session.get(
            OrderItem,
            order_item_id,
        )

        if not order_item:
            raise ValueError("Sản phẩm trong đơn hàng không tồn tại")

        order = OrderService.get_order_by_id(order_item.order_id)

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Không thể hủy sản phẩm trong đơn đã hoàn thành")

        if order_item.item_status == "ĐÃ HỦY":
            raise ValueError("Sản phẩm đã được hủy")

        if order_item.shipping_status in [
            "ĐANG GIAO HÀNG",
            "ĐÃ GIAO",
        ]:
            raise ValueError("Sản phẩm đã được vận chuyển, không thể hủy")

        if order_item.preorder_id is not None:
            paid_payment = db.session.scalar(
                select(Payment).where(
                    Payment.order_id == order.order_id,
                    Payment.payment_status == "ĐÃ THANH TOÁN",
                )
            )

            if paid_payment:
                raise ValueError(
                    "Sản phẩm preorder đã thanh toán " "hoặc đặt cọc không được hủy"
                )

        try:
            if order_item.preorder_id is None:
                inventory = db.session.scalar(
                    select(Inventory).where(
                        Inventory.product_id == order_item.product_id,
                        Inventory.active.is_(True),
                    )
                )

                if not inventory:
                    raise ValueError("Không tìm thấy tồn kho sản phẩm")

                inventory.quantity += order_item.quantity

                transaction = InventoryTransaction(
                    inventory_id=inventory.inventory_id,
                    transaction_type="HOÀN KHO",
                    quantity=order_item.quantity,
                    price=None,
                )

                db.session.add(transaction)

            order_item.item_status = "ĐÃ HỦY"

            new_total_amount = Decimal("0")

            for item in order.order_items:

                if item.item_status == "ĐÃ HỦY":
                    continue

                new_total_amount += Decimal(str(item.price)) * Decimal(
                    str(item.quantity)
                )

            order.total_amount = new_total_amount

            all_cancelled = all(
                item.item_status == "ĐÃ HỦY" for item in order.order_items
            )

            if all_cancelled:
                order.order_status = "ĐÃ HỦY"

            db.session.commit()

            return order_item

        except Exception:
            db.session.rollback()
            raise


class PaymentService:

    @staticmethod
    def has_previous_paid_order(
        user_id,
        exclude_order_id=None,
    ):
        stmt = select(Order.order_id).where(
            Order.user_id == user_id,
            Order.active.is_(True),
            Order.order_status.in_(
                [
                    "ĐÃ XÁC NHẬN",
                    "ĐANG XỬ LÝ",
                    "HOÀN THÀNH",
                ]
            ),
        )

        if exclude_order_id is not None:
            stmt = stmt.where(Order.order_id != exclude_order_id)

        return db.session.scalar(stmt) is not None

    @staticmethod
    def get_order_payment_summary(order_id):
        order = OrderService.get_order_by_id(order_id)

        preorder_amount = Decimal("0")
        in_stock_amount = Decimal("0")

        for item in order.order_items:
            if item.item_status == "ĐÃ HỦY":
                continue

            item_amount = Decimal(str(item.price)) * Decimal(str(item.quantity))

            if item.preorder_id is not None:
                preorder_amount += item_amount
            else:
                in_stock_amount += item_amount

        shipping_fee = Decimal(str(order.shipping_fee or 0))

        total_amount = preorder_amount + in_stock_amount + shipping_fee

        paid_stmt = select(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        ).where(
            Payment.order_id == order_id,
            Payment.payment_status.in_(
                [
                    "ĐÃ THANH TOÁN",
                    "ĐÃ HOÀN TIỀN",
                ]
            ),
        )

        total_paid = Decimal(str(db.session.scalar(paid_stmt)))

        remaining_amount = total_amount - total_paid

        if remaining_amount < 0:
            remaining_amount = Decimal("0")

        eligible_for_deposit = (
            preorder_amount > 0
            and PaymentService.has_previous_paid_order(
                user_id=order.user_id,
                exclude_order_id=order.order_id,
            )
        )

        user = db.session.get(User, order.user_id)

        wallet_balance = 0.0
        if user and user.wallet and user.wallet.balance is not None:
            wallet_balance = float(user.wallet.balance)

        return {
            "order": order,
            "wallet_balance": wallet_balance,
            "preorder_amount": preorder_amount,
            "in_stock_amount": in_stock_amount,
            "shipping_fee": shipping_fee,
            "total_amount": total_amount,
            "total_paid": total_paid,
            "remaining_amount": remaining_amount,
            "eligible_for_deposit": eligible_for_deposit,
        }

    @staticmethod
    def calculate_payment_amount(
        order_id,
        payment_type,
    ):
        valid_types = [
            "THANH TOÁN FULL",
            "ĐẶT CỌC",
            "THANH TOÁN CÒN LẠI",
        ]

        if payment_type not in valid_types:
            raise ValueError("Loại thanh toán không hợp lệ")

        summary = PaymentService.get_order_payment_summary(order_id)

        if summary["remaining_amount"] <= 0:
            raise ValueError("Đơn hàng đã được thanh toán đầy đủ")

        if payment_type == "THANH TOÁN FULL":
            return summary["remaining_amount"]

        if payment_type == "ĐẶT CỌC":
            if not summary["eligible_for_deposit"]:
                raise ValueError("Khách hàng chưa đủ điều kiện " "cọc 70%")

            if summary["total_paid"] > 0:
                raise ValueError("Đơn hàng đã phát sinh thanh toán")

            return (
                summary["in_stock_amount"]
                + summary["shipping_fee"]
                + (summary["preorder_amount"] * Decimal("0.70"))
            )

        if summary["total_paid"] <= 0:
            raise ValueError("Đơn hàng chưa có khoản cọc")

        return summary["remaining_amount"]

    @staticmethod
    def create_payment(
        order_id,
        payment_method,
        payment_type,
        transaction_id=None,
    ):
        order = OrderService.get_order_by_id(order_id)

        if order.order_status == "ĐÃ HỦY":
            raise ValueError("Không thể thanh toán đơn hàng đã hủy")

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Đơn hàng đã hoàn thành")

        if payment_method not in ["MOMO", "VÍ VERD"]:
            raise ValueError("Phương thức thanh toán không hợp lệ")

        if payment_method in ["VÍ VERD"]:
            trans = WalletService.pay_with_wallet(
                user_id=order.user_id, order_id=order_id, payment_type=payment_type
            )

            payment = db.session.scalar(
                select(Payment).where(Payment.transaction_id == trans.transaction_code)
            )
            return payment

        amount = PaymentService.calculate_payment_amount(
            order_id=order_id,
            payment_type=payment_type,
        )

        transaction_id = (
            str(transaction_id).strip()
            if transaction_id
            else f"MOMO_{order_id}_{int(time.time())}"
        )

        existing_transaction = db.session.scalar(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )
        if existing_transaction:
            transaction_id = f"{transaction_id}_{int(time.time())}"

        payment = Payment(
            order_id=order_id,
            amount=amount,
            payment_method="MOMO",
            payment_type=payment_type,
            payment_status="ĐANG THANH TOÁN",
            transaction_id=transaction_id,
        )

        try:
            db.session.add(payment)
            db.session.flush()

            PaymentService.apply_successful_payment(payment)

            db.session.commit()
            return payment

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_payments_by_order(order_id):
        OrderService.get_order_by_id(order_id)

        stmt = select(Payment).where(Payment.order_id == order_id)

        return db.session.scalars(stmt).all()

    @staticmethod
    def apply_successful_payment(payment):
        if not payment:
            raise ValueError("Thanh toán không tồn tại")

        if payment.payment_status == "ĐÃ THANH TOÁN":
            raise ValueError("Thanh toán đã được xác nhận")

        if payment.payment_status in [
            "ĐÃ HỦY",
            "ĐÃ HOÀN TIỀN",
        ]:
            raise ValueError("Không thể xác nhận giao dịch này")

        order = OrderService.get_order_by_id(payment.order_id)

        if order.order_status == "ĐÃ HỦY":
            raise ValueError("Không thể xác nhận thanh toán " "cho đơn hàng đã hủy")

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Đơn hàng đã hoàn thành")

        previous_paid_stmt = select(Payment.payment_id).where(
            Payment.order_id == order.order_id,
            Payment.payment_status.in_(
                [
                    "ĐÃ THANH TOÁN",
                    "ĐÃ HOÀN TIỀN",
                ]
            ),
            Payment.payment_id != payment.payment_id,
        )

        had_previous_payment = db.session.scalar(previous_paid_stmt) is not None

        payment.payment_status = "ĐÃ THANH TOÁN"

        payment.paid_at = datetime.now(timezone.utc)

        if not had_previous_payment:
            for item in order.order_items:
                if item.preorder_id is not None and item.item_status != "ĐÃ HỦY":
                    preorder = db.session.get(
                        PreOrder,
                        item.preorder_id,
                    )

                    if preorder:
                        preorder.quantity_order += item.quantity

        db.session.flush()

        paid_stmt = select(
            func.coalesce(
                func.sum(Payment.amount),
                0,
            )
        ).where(
            Payment.order_id == order.order_id,
            Payment.payment_status.in_(
                [
                    "ĐÃ THANH TOÁN",
                    "ĐÃ HOÀN TIỀN",
                ]
            ),
        )

        total_paid = Decimal(str(db.session.scalar(paid_stmt)))

        required_amount = Decimal(str(order.total_amount)) + Decimal(
            str(order.shipping_fee or 0)
        )

        if total_paid >= required_amount:
            order.order_status = "ĐÃ XÁC NHẬN"

        elif total_paid > 0:
            order.order_status = "ĐÃ ĐẶT CỌC"

        return payment

    @staticmethod
    def confirm_payment(payment_id):
        payment = db.session.get(Payment, payment_id)

        try:
            PaymentService.apply_successful_payment(payment)

            db.session.commit()

            return payment

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def cancel_payment(payment_id):
        payment = db.session.get(Payment, payment_id)

        if not payment:
            raise ValueError("Thanh toán không tồn tại")

        if payment.payment_status == "ĐÃ THANH TOÁN":
            raise ValueError("Không thể hủy thanh toán " "đã thành công")

        if payment.payment_status == "ĐÃ HỦY":
            raise ValueError("Thanh toán đã được hủy")

        if payment.payment_status == "ĐÃ HOÀN TIỀN":
            raise ValueError("Thanh toán đã được hoàn tiền")

        payment.payment_status = "ĐÃ HỦY"

        try:
            db.session.commit()

            return payment

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def refund_order_item(order_item_id):
        order_item = db.session.get(
            OrderItem,
            order_item_id,
        )

        if not order_item:
            raise ValueError("Sản phẩm trong đơn hàng " "không tồn tại")

        order = OrderService.get_order_by_id(order_item.order_id)

        if order_item.preorder_id is not None:
            raise ValueError("Sản phẩm preorder đã thanh toán " "không được hoàn tiền")

        paid_payment = db.session.scalar(
            select(Payment).where(
                Payment.order_id == order.order_id,
                Payment.payment_status == "ĐÃ THANH TOÁN",
            )
        )

        if not paid_payment:
            raise ValueError("Đơn hàng chưa có thanh toán " "thành công")

        if order_item.item_status != "ĐÃ HỦY":
            raise ValueError("Chỉ hoàn tiền cho sản phẩm " "đã hủy")

        refund_amount = Decimal(str(order_item.price)) * Decimal(
            str(order_item.quantity)
        )

        return {
            "user_id": order.user_id,
            "order_id": order.order_id,
            "order_item_id": order_item.order_item_id,
            "amount": refund_amount,
        }

    @staticmethod
    def get_preorder_customers_by_product(product_id):
        stmt = (
            select(
                Order.order_id,
                User.username,
                OrderItem.quantity,
                (OrderItem.price * OrderItem.quantity).label("total_amount"),
                Order.order_status,
                Order.order_date.label("created_at"),
            )
            .join(User, Order.user_id == User.user_id)
            .join(OrderItem, Order.order_id == OrderItem.order_id)
            .where(
                OrderItem.product_id == product_id,
                OrderItem.preorder_id.is_not(None),
                OrderItem.item_status != "ĐÃ HỦY",
                Order.active.is_(True),
            )
            .order_by(Order.order_id.desc())
        )

        results = db.session.execute(stmt).all()

        customers = []
        for r in results:
            customers.append(
                {
                    "order_id": r.order_id,
                    "username": r.username,
                    "quantity": r.quantity,
                    "total_amount": float(r.total_amount),
                    "order_status": r.order_status,
                    "created_at": str(r.created_at) if r.created_at else None,
                }
            )
        return customers
