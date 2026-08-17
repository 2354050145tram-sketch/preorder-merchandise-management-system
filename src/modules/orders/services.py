from config import db
from decimal import Decimal
from datetime import date, datetime, timezone
from sqlalchemy import select
from modules.orders.models import Order, OrderItem, Payment
from modules.users.models import User
from modules.products.models import Product
from modules.preorders.models import PreOrder
from modules.inventories.models import Inventory, InventoryTransaction


class OrderService:

    @staticmethod
    def create_order(user_id, items):
        user = db.session.get(User, user_id)

        if not user or not user.active:
            raise ValueError("Người dùng không tồn tại")

        # Kiểm tra giỏ hàng
        if not items:
            raise ValueError("Vui lòng chọn sản phẩm cần đặt hàng")

        total_amount = Decimal("0")
        order_items_data = []
        seen_items = set()

        # Kiểm tra sản phẩm
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

            # Khách đang mua theo đợt PREORDER
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

            # Hàng có sẵn
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

            # Tính tiền hàng
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

            # Tạo order item
            for item in order_items_data:

                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=item["product_id"],
                    preorder_id=item["preorder_id"],
                    quantity=item["quantity"],
                    price=item["price"],
                )

                db.session.add(order_item)

                # Tăng số lượng preorder
                if item["preorder_id"]:
                    preorder = db.session.get(PreOrder, item["preorder_id"])

                    preorder.quantity_order += item["quantity"]

                # Giảm số lượng hàng sẵn
                else:
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
        stmt = select(Order).join(User, Order.user_id == User.user_id)

        if active is not None:
            stmt = stmt.where(Order.active == active)

        # Tìm theo username hoặc email
        if keyword and keyword.strip():
            keyword = keyword.strip()

            stmt = stmt.where(
                (User.username.ilike(f"%{keyword}%"))
                | (User.email.ilike(f"%{keyword}%"))
            )

        # Lọc trạng thái đơn hàng
        if order_status:
            valid_statuses = [
                "CHỜ XÁC NHẬN",
                "ĐÃ XÁC NHẬN",
                "ĐANG XỬ LÝ",
                "HOÀN THÀNH",
                "ĐÃ HỦY",
            ]

            if order_status not in valid_statuses:
                raise ValueError("Trạng thái đơn hàng không hợp lệ")

            stmt = stmt.where(Order.order_status == order_status)

        return db.session.scalars(stmt).all()

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
            "ĐÃ XÁC NHẬN": ["ĐANG XỬ LÝ"],
            "ĐANG XỬ LÝ": ["HOÀN THÀNH"],
        }

        allowed_statuses = allowed_transitions.get(order.order_status, [])

        if order_status not in allowed_statuses:
            raise ValueError("Không thể chuyển sang trạng thái đơn hàng này")

        if order_status == "HOÀN THÀNH":
            unfinished_items = [
                item
                for item in order.order_items
                if item.item_status not in ["HOÀN THÀNH", "ĐÃ HỦY"]
            ]

            if unfinished_items:
                raise ValueError("Đơn hàng vẫn còn sản phẩm chưa hoàn thành")

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

            # Cộng phí ship đúng 1 lần
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

        # Chặn cập nhật lùi trạng thái
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
        order_item = db.session.get(OrderItem, order_item_id)

        if not order_item:
            raise ValueError("Sản phẩm trong đơn hàng không tồn tại")

        order = OrderService.get_order_by_id(order_item.order_id)

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Không thể hủy sản phẩm trong đơn đã hoàn thành")

        if order_item.item_status == "ĐÃ HỦY":
            raise ValueError("Sản phẩm đã được hủy")

        if order_item.shipping_status in ["ĐANG GIAO HÀNG", "ĐÃ GIAO"]:
            raise ValueError("Sản phẩm đã được vận chuyển, không thể hủy")

        # PREORDER đã thanh toán thì không được hủy
        if order_item.preorder_id is not None:

            paid_payment = db.session.scalar(
                select(Payment).where(
                    Payment.order_id == order.order_id,
                    Payment.payment_status == "ĐÃ THANH TOÁN",
                )
            )

            if paid_payment:
                raise ValueError("Sản phẩm preorder đã thanh toán không được hủy")

        try:
            # PREORDER chưa thanh toán
            if order_item.preorder_id is not None:

                preorder = db.session.get(PreOrder, order_item.preorder_id)

                if preorder:
                    preorder.quantity_order -= order_item.quantity

                    if preorder.quantity_order < 0:
                        preorder.quantity_order = 0

            # IN_STOCK
            else:
                stmt = select(Inventory).where(
                    Inventory.product_id == order_item.product_id
                )

                inventory = db.session.scalar(stmt)

                if not inventory:
                    raise ValueError("Không tìm thấy tồn kho sản phẩm")

                inventory.quantity += order_item.quantity

                inventory_transaction = InventoryTransaction(
                    inventory_id=inventory.inventory_id,
                    transaction_type="HOÀN KHO",
                    quantity=order_item.quantity,
                    price=None,
                )

                db.session.add(inventory_transaction)

                # Nếu đang ở giai đoạn lấy hàng thì vẫn được hủy
            # và loại item khỏi vận đơn hiện tại
            if order_item.shipping_status == "ĐANG LẤY HÀNG":
                order_item.shipping_method = None
                order_item.tracking_code = None
                order_item.shipping_status = None

            order_item.item_status = "ĐÃ HỦY"

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
    def create_payment(order_id, amount, payment_method, transaction_id=None):
        order = OrderService.get_order_by_id(order_id)

        if order.order_status == "ĐÃ HỦY":
            raise ValueError("Không thể thanh toán đơn hàng đã hủy")

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Đơn hàng đã hoàn thành")

        try:
            amount = Decimal(str(amount))
        except Exception:
            raise ValueError("Số tiền thanh toán không hợp lệ")

        if amount <= 0:
            raise ValueError("Số tiền thanh toán phải lớn hơn 0")

        expected_amount = order.total_amount

        if amount != expected_amount:
            raise ValueError("Số tiền thanh toán không đúng với giá trị đơn hàng")

        transaction_id = (
            str(transaction_id).strip() if transaction_id is not None else ""
        )

        if not transaction_id:
            raise ValueError("Mã giao dịch không được để trống")

        existing_transaction = db.session.scalar(
            select(Payment).where(Payment.transaction_id == transaction_id)
        )

        if existing_transaction:
            raise ValueError("Mã giao dịch đã tồn tại")

        if payment_method not in ["MOMO", "VÍ VERD"]:
            raise ValueError("Phương thức thanh toán không hợp lệ")

        # Không cho tạo thêm payment nếu đã thanh toán
        paid_payment = db.session.scalar(
            select(Payment).where(
                Payment.order_id == order_id, Payment.payment_status == "ĐÃ THANH TOÁN"
            )
        )

        if paid_payment:
            raise ValueError("Đơn hàng đã được thanh toán")

        # Không cho có nhiều giao dịch đang chờ cùng lúc
        pending_payment = db.session.scalar(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.payment_status == "ĐANG THANH TOÁN",
            )
        )

        if pending_payment:
            raise ValueError("Đơn hàng đang có giao dịch thanh toán chưa hoàn tất")

        payment = Payment(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            payment_status="ĐANG THANH TOÁN",
            transaction_id=transaction_id,
        )

        try:
            db.session.add(payment)
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
    def confirm_payment(payment_id):
        payment = db.session.get(Payment, payment_id)

        if not payment:
            raise ValueError("Thanh toán không tồn tại")

        if payment.payment_status == "ĐÃ THANH TOÁN":
            raise ValueError("Thanh toán đã được xác nhận")

        if payment.payment_status in ["ĐÃ HỦY", "ĐÃ HOÀN TIỀN"]:
            raise ValueError("Không thể xác nhận giao dịch này")

        order = OrderService.get_order_by_id(payment.order_id)

        if order.order_status == "ĐÃ HỦY":
            raise ValueError("Không thể xác nhận thanh toán cho đơn hàng đã hủy")

        if order.order_status == "HOÀN THÀNH":
            raise ValueError("Đơn hàng đã hoàn thành")

        if order.order_status != "CHỜ XÁC NHẬN":
            raise ValueError("Đơn hàng không ở trạng thái chờ xác nhận")

        payment.payment_status = "ĐÃ THANH TOÁN"
        payment.paid_at = datetime.now(timezone.utc)

        order.order_status = "ĐÃ XÁC NHẬN"

        try:
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
            raise ValueError("Không thể hủy thanh toán đã thành công")

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
        order_item = db.session.get(OrderItem, order_item_id)

        if not order_item:
            raise ValueError("Sản phẩm trong đơn hàng không tồn tại")

        order = OrderService.get_order_by_id(order_item.order_id)

        # PREORDER không được hoàn sau khi đã thanh toán
        if order_item.preorder_id is not None:
            raise ValueError("Sản phẩm preorder đã thanh toán không được hoàn tiền")

        paid_payment = db.session.scalar(
            select(Payment).where(
                Payment.order_id == order.order_id,
                Payment.payment_status == "ĐÃ THANH TOÁN",
            )
        )

        if not paid_payment:
            raise ValueError("Đơn hàng chưa có thanh toán thành công")

        if order_item.item_status != "ĐÃ HỦY":
            raise ValueError("Chỉ hoàn tiền cho sản phẩm đã hủy")

        refund_amount = order_item.price * order_item.quantity

        return {
            "user_id": order.user_id,
            "order_id": order.order_id,
            "order_item_id": order_item.order_item_id,
            "amount": refund_amount,
        }
