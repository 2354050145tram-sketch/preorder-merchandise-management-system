import unittest
from datetime import date
from decimal import Decimal
from config import db
from modules.inventories.models import InventoryTransaction
from modules.orders.models import Order, OrderItem, Payment
from modules.orders.services import OrderService, PaymentService
from modules.wallets.models import WalletTransaction
from modules.wallets.services import WalletService
from tests.support import DatabaseTestCase


class OrderMixin:
    def create_mixed_order(self):
        return OrderService.create_order(
            self.seed["customer"].user_id,
            [
                {"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 2},
                {"product_id": self.seed["preorder_product"].product_id, "preorder_id": self.seed["preorder"].preorder_id, "quantity": 1},
            ],
        )


class OrderServiceTests(OrderMixin, DatabaseTestCase, unittest.TestCase):
    def test_create_and_query_order(self):
        inventory = self.seed["stock_product"].inventories[0]
        order = self.create_mixed_order()
        self.assertEqual(order.total_amount, Decimal("400000"))
        self.assertEqual(len(order.order_items), 2)
        self.assertEqual(inventory.quantity, 18)
        self.assertEqual(InventoryTransaction.query.filter_by(transaction_type="XUẤT").count(), 1)
        self.assertEqual(OrderService.get_order_by_id(order.order_id), order)
        self.assertEqual(OrderService.get_orders_by_user(order.user_id)[0], order)
        self.assertIn(order, OrderService.get_all_orders(keyword=str(order.order_id)))
        self.assertIn(order, OrderService.get_all_orders(keyword="customer", order_status="CHỜ XÁC NHẬN"))

    def test_create_order_validation(self):
        uid = self.seed["customer"].user_id
        stock = self.seed["stock_product"].product_id
        pre_product = self.seed["preorder_product"].product_id
        pre = self.seed["preorder"].preorder_id
        cases = [
            (999, [], "Người dùng không tồn tại"),
            (uid, [], "Vui lòng chọn"),
            (uid, [{"product_id": stock, "preorder_id": None, "quantity": 1}] * 2, "bị trùng"),
            (uid, [{"product_id": None, "preorder_id": None, "quantity": 1}], "Thông tin sản phẩm"),
            (uid, [{"product_id": stock, "preorder_id": None, "quantity": "x"}], "Số lượng sản phẩm không hợp lệ"),
            (uid, [{"product_id": stock, "preorder_id": None, "quantity": -1}], "phải lớn hơn 0"),
            (uid, [{"product_id": 999, "preorder_id": None, "quantity": 1}], "Sản phẩm không tồn tại"),
            (uid, [{"product_id": stock, "preorder_id": pre, "quantity": 1}], "Đợt preorder không hợp lệ"),
            (uid, [{"product_id": pre_product, "preorder_id": None, "quantity": 1}], "phải được đặt theo"),
            (uid, [{"product_id": stock, "preorder_id": None, "quantity": 999}], "không đủ số lượng"),
        ]
        for user_id, items, msg in cases:
            with self.subTest(msg=msg), self.assertRaisesRegex(ValueError, msg):
                OrderService.create_order(user_id, items)

    def test_shipping_status_and_order_status(self):
        order = self.create_mixed_order()
        item_ids = [i.order_item_id for i in order.order_items]
        shipped = OrderService.update_shipping_info(order.order_id, item_ids, "TIÊU CHUẨN", 30000, "TRACK-1")
        self.assertEqual(len(shipped), 2)
        self.assertEqual(order.shipping_fee, Decimal("30000"))
        shipped = OrderService.update_shipping_status("TRACK-1", "ĐANG GIAO HÀNG")
        self.assertTrue(all(i.shipping_status == "ĐANG GIAO HÀNG" for i in shipped))
        shipped = OrderService.update_shipping_status("TRACK-1", "ĐÃ GIAO")
        self.assertTrue(all(i.item_status == "HOÀN THÀNH" for i in shipped))

        order2 = OrderService.create_order(self.seed["customer"].user_id, [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}])
        self.assertEqual(OrderService.update_order_status(order2.order_id, "ĐÃ HỦY").order_status, "ĐÃ HỦY")
        with self.assertRaisesRegex(ValueError, "đã bị hủy"):
            OrderService.update_order_status(order2.order_id, "ĐÃ XÁC NHẬN")

    def test_shipping_validation(self):
        order = self.create_mixed_order()
        ids = [order.order_items[0].order_item_id]
        cases = [
            ((order.order_id, ids, "BAD", 0, "T"), "Phương thức"),
            ((order.order_id, ids, "TIÊU CHUẨN", "bad", "T"), "Phí vận chuyển"),
            ((order.order_id, ids, "TIÊU CHUẨN", -1, "T"), "không được nhỏ hơn"),
            ((order.order_id, ids, "TIÊU CHUẨN", 0, ""), "không được để trống"),
            ((order.order_id, [], "TIÊU CHUẨN", 0, "T"), "Chưa chọn"),
            ((order.order_id, [999], "TIÊU CHUẨN", 0, "T"), "không hợp lệ"),
        ]
        for args, msg in cases:
            with self.subTest(msg=msg), self.assertRaisesRegex(ValueError, msg):
                OrderService.update_shipping_info(*args)
        with self.assertRaises(ValueError):
            OrderService.update_shipping_status("none", "ĐÃ GIAO")
        with self.assertRaises(ValueError):
            OrderService.update_shipping_status("none", "BAD")

    def test_cancel_stock_item_restores_inventory(self):
        order = self.create_mixed_order()
        stock_item = next(i for i in order.order_items if i.preorder_id is None)
        inventory = self.seed["stock_product"].inventories[0]
        before = inventory.quantity
        cancelled = OrderService.cancel_order_item(stock_item.order_item_id)
        self.assertEqual(cancelled.item_status, "ĐÃ HỦY")
        self.assertEqual(inventory.quantity, before + stock_item.quantity)
        with self.assertRaisesRegex(ValueError, "đã được hủy"):
            OrderService.cancel_order_item(stock_item.order_item_id)
        with self.assertRaises(ValueError):
            OrderService.cancel_order_item(999)

    def test_remaining_order_edge_cases(self):
        uid = self.seed["customer"].user_id
        self.seed["preorder"].start_date = date.today().replace(year=date.today().year + 1)
        self.seed["preorder"].end_date = date.today().replace(year=date.today().year + 1)
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "không có đợt preorder"):
            OrderService.create_order(
                uid,
                [{"product_id": self.seed["preorder_product"].product_id, "preorder_id": self.seed["preorder"].preorder_id, "quantity": 1}],
            )
        self.seed["preorder"].start_date = date.today()
        self.seed["preorder"].end_date = date.today()
        with self.assertRaisesRegex(ValueError, "chưa có tồn kho"):
            OrderService.create_order(
                uid,
                [{"product_id": self.seed["spare_product"].product_id, "preorder_id": None, "quantity": 1}],
            )

        order = self.create_mixed_order()
        item_ids = [item.order_item_id for item in order.order_items]
        OrderService.update_shipping_info(order.order_id, item_ids, "TIÊU CHUẨN", 0, "EDGE-TRACK")
        with self.assertRaisesRegex(ValueError, "đã tồn tại"):
            OrderService.update_shipping_info(order.order_id, item_ids, "TIÊU CHUẨN", 0, "EDGE-TRACK")
        OrderService.update_shipping_status("EDGE-TRACK", "ĐANG GIAO HÀNG")
        with self.assertRaisesRegex(ValueError, "cập nhật lùi"):
            OrderService.update_shipping_status("EDGE-TRACK", "ĐANG LẤY HÀNG")
        with self.assertRaisesRegex(ValueError, "được vận chuyển"):
            OrderService.cancel_order_item(item_ids[0])

        unshipped = OrderService.create_order(
            uid,
            [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}],
        )
        with self.assertRaisesRegex(ValueError, "chưa có thông tin"):
            item = unshipped.order_items[0]
            item.tracking_code = "NO-STATUS"
            db.session.commit()
            OrderService.update_shipping_status("NO-STATUS", "ĐANG GIAO HÀNG")

        unshipped.order_status = "HOÀN THÀNH"
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "đã hoàn thành"):
            OrderService.update_order_status(unshipped.order_id, "ĐÃ HỦY")
        with self.assertRaisesRegex(ValueError, "đơn đã hoàn thành"):
            OrderService.cancel_order_item(unshipped.order_items[0].order_item_id)


class PaymentServiceTests(OrderMixin, DatabaseTestCase, unittest.TestCase):
    def test_TPBANK_full_payment_and_summary(self):
        order = self.create_mixed_order()
        summary = PaymentService.get_order_payment_summary(order.order_id)
        self.assertEqual(summary["remaining_amount"], Decimal("400000"))
        self.assertEqual(PaymentService.calculate_payment_amount(order.order_id, "THANH TOÁN FULL"), Decimal("400000"))
        payment = PaymentService.create_payment(order.order_id, "TPBANK", "THANH TOÁN FULL", "TX-TPBANK")
        self.assertEqual(payment.payment_status, "ĐÃ THANH TOÁN")
        self.assertEqual(order.order_status, "ĐÃ XÁC NHẬN")
        self.assertEqual(self.seed["preorder"].quantity_order, 1)
        self.assertEqual(PaymentService.get_payments_by_order(order.order_id)[0], payment)
        with self.assertRaisesRegex(ValueError, "đầy đủ"):
            PaymentService.calculate_payment_amount(order.order_id, "THANH TOÁN FULL")

    def test_payment_validation_and_cancel(self):
        order = self.create_mixed_order()
        with self.assertRaisesRegex(ValueError, "Loại thanh toán"):
            PaymentService.calculate_payment_amount(order.order_id, "BAD")
        with self.assertRaisesRegex(ValueError, "chưa đủ điều kiện"):
            PaymentService.calculate_payment_amount(order.order_id, "ĐẶT CỌC")
        with self.assertRaisesRegex(ValueError, "chưa có khoản cọc"):
            PaymentService.calculate_payment_amount(order.order_id, "THANH TOÁN CÒN LẠI")
        with self.assertRaisesRegex(ValueError, "Phương thức"):
            PaymentService.create_payment(order.order_id, "CASH", "THANH TOÁN FULL")
        pending = Payment(order_id=order.order_id, amount=1000, payment_method="TPBANK", payment_type="THANH TOÁN FULL", payment_status="ĐANG THANH TOÁN", transaction_id="PENDING")
        db.session.add(pending)
        db.session.commit()
        self.assertEqual(PaymentService.cancel_payment(pending.payment_id).payment_status, "ĐÃ HỦY")
        with self.assertRaises(ValueError):
            PaymentService.cancel_payment(pending.payment_id)
        with self.assertRaises(ValueError):
            PaymentService.cancel_payment(999)

    def test_deposit_and_remaining_payment(self):
        prior = Order(user_id=self.seed["customer"].user_id, order_date=date.today(), total_amount=1, order_status="HOÀN THÀNH", shipping_fee=0, active=True)
        db.session.add(prior)
        db.session.commit()
        order = self.create_mixed_order()
        deposit = PaymentService.calculate_payment_amount(order.order_id, "ĐẶT CỌC")
        self.assertEqual(deposit, Decimal("340000.00"))
        payment = Payment(order_id=order.order_id, amount=deposit, payment_method="TPBANK", payment_type="ĐẶT CỌC", payment_status="ĐANG THANH TOÁN", transaction_id="DEP")
        db.session.add(payment)
        db.session.flush()
        PaymentService.apply_successful_payment(payment)
        db.session.commit()
        self.assertEqual(order.order_status, "ĐÃ ĐẶT CỌC")
        self.assertEqual(PaymentService.calculate_payment_amount(order.order_id, "THANH TOÁN CÒN LẠI"), Decimal("60000.00"))

    def test_refund_information(self):
        order = self.create_mixed_order()
        payment = PaymentService.create_payment(order.order_id, "TPBANK", "THANH TOÁN FULL", "PAID")
        stock_item = next(i for i in order.order_items if i.preorder_id is None)
        stock_item.item_status = "ĐÃ HỦY"
        db.session.commit()
        info = PaymentService.refund_order_item(stock_item.order_item_id)
        self.assertEqual(info["amount"], Decimal("200000"))
        preorder_item = next(i for i in order.order_items if i.preorder_id is not None)
        with self.assertRaises(ValueError):
            PaymentService.refund_order_item(preorder_item.order_item_id)
        self.assertTrue(PaymentService.get_preorder_customers_by_product(self.seed["preorder_product"].product_id))

    def test_remaining_payment_edge_cases(self):
        order = OrderService.create_order(
            self.seed["customer"].user_id,
            [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}],
        )
        wallet_payment = PaymentService.create_payment(
            order.order_id, "VÍ VERD", "THANH TOÁN FULL"
        )
        self.assertEqual(wallet_payment.payment_method, "VÍ VERD")

        for payment in [None]:
            with self.assertRaisesRegex(ValueError, "không tồn tại"):
                PaymentService.apply_successful_payment(payment)
        with self.assertRaisesRegex(ValueError, "đã được xác nhận"):
            PaymentService.apply_successful_payment(wallet_payment)

        second = OrderService.create_order(
            self.seed["customer"].user_id,
            [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}],
        )
        cancelled = Payment(
            order_id=second.order_id,
            amount=1,
            payment_method="TPBANK",
            payment_type="THANH TOÁN FULL",
            payment_status="ĐÃ HỦY",
            transaction_id="EDGE-CANCELLED",
        )
        db.session.add(cancelled)
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "Không thể xác nhận"):
            PaymentService.apply_successful_payment(cancelled)
        with self.assertRaisesRegex(ValueError, "đã thành công"):
            PaymentService.cancel_payment(wallet_payment.payment_id)
        cancelled.payment_status = "ĐÃ HOÀN TIỀN"
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "đã được hoàn tiền"):
            PaymentService.cancel_payment(cancelled.payment_id)
        with self.assertRaisesRegex(ValueError, "không tồn tại"):
            PaymentService.refund_order_item(999)
        with self.assertRaisesRegex(ValueError, "thanh toán thành công"):
            PaymentService.refund_order_item(second.order_items[0].order_item_id)


class WalletServiceTests(OrderMixin, DatabaseTestCase, unittest.TestCase):
    def test_deposit_withdraw_and_filters(self):
        uid = self.seed["customer"].user_id
        wallet = WalletService.get_wallet_by_user(uid)
        deposit = WalletService.create_deposit_request(uid, 60000, "Nạp test")
        self.assertEqual(WalletService.get_deposit_by_id(uid, deposit.wallet_transaction_id), deposit)
        approved = WalletService.approve_deposit(deposit.wallet_transaction_id)
        self.assertEqual(approved.transaction_status, "THÀNH CÔNG")
        self.assertEqual(wallet.balance, Decimal("550000"))
        withdraw = WalletService.create_withdraw_request(uid, 50000)
        approved_w = WalletService.approve_withdraw(withdraw.wallet_transaction_id)
        self.assertEqual(approved_w.transaction_status, "THÀNH CÔNG")
        self.assertEqual(wallet.balance, Decimal("490000"))
        self.assertTrue(WalletService.get_transactions(uid, "NẠP TIỀN", "THÀNH CÔNG"))
        self.assertTrue(WalletService.get_all_deposits_admin("THÀNH CÔNG"))

    def test_cancel_deposit_and_wallet_validations(self):
        uid = self.seed["customer"].user_id
        deposit = WalletService.create_deposit_request(uid, 20000)
        self.assertEqual(WalletService.cancel_deposit_request(uid, deposit.wallet_transaction_id).transaction_status, "ĐÃ HỦY")
        for fn, args in [
            (WalletService.create_deposit_request, (uid, "bad")),
            (WalletService.create_deposit_request, (uid, 0)),
            (WalletService.create_withdraw_request, (uid, "bad")),
            (WalletService.create_withdraw_request, (uid, 0)),
            (WalletService.create_withdraw_request, (uid, 9999999)),
            (WalletService.get_transactions, (uid, "BAD", None)),
            (WalletService.get_transactions, (uid, None, "BAD")),
        ]:
            with self.subTest(fn=fn.__name__), self.assertRaises(ValueError):
                fn(*args)
        with self.assertRaises(ValueError):
            WalletService.get_deposit_by_id(uid, 999)
        with self.assertRaises(ValueError):
            WalletService.cancel_deposit_request(uid, deposit.wallet_transaction_id)

    def test_wallet_payment_and_refund(self):
        uid = self.seed["customer"].user_id
        order = OrderService.create_order(uid, [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}])
        transaction = WalletService.pay_with_wallet(uid, order.order_id, "THANH TOÁN FULL")
        self.assertEqual(transaction.transaction_status, "THÀNH CÔNG")
        self.assertEqual(order.order_status, "ĐÃ XÁC NHẬN")
        item = order.order_items[0]
        item.item_status = "ĐÃ HỦY"
        db.session.commit()
        refund_info = PaymentService.refund_order_item(item.order_item_id)
        refund = WalletService.refund_to_wallet(order.order_id, item.order_item_id, refund_info["amount"])
        self.assertEqual(refund.transaction_type, "HOÀN TIỀN")
        with self.assertRaisesRegex(ValueError, "đã được hoàn tiền"):
            WalletService.refund_to_wallet(order.order_id, item.order_item_id, refund_info["amount"])

    def test_create_wallet_and_errors(self):
        with self.assertRaisesRegex(ValueError, "đã có ví"):
            WalletService.create_wallet(self.seed["customer"].user_id)
        with self.assertRaisesRegex(ValueError, "User không tồn tại"):
            WalletService.create_wallet(999)
        self.seed["other"].wallet.active = False
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "Ví không tồn tại"):
            WalletService.get_wallet_by_user(self.seed["other"].user_id)

    def test_wallet_approval_and_payment_error_branches(self):
        uid = self.seed["customer"].user_id
        deposit = WalletService.create_deposit_request(uid, 20000)
        WalletService.approve_deposit(deposit.wallet_transaction_id)
        with self.assertRaisesRegex(ValueError, "đã được xử lý"):
            WalletService.approve_deposit(deposit.wallet_transaction_id)

        withdrawal = WalletService.create_withdraw_request(uid, 60000)
        WalletService.approve_withdraw(withdrawal.wallet_transaction_id)
        with self.assertRaisesRegex(ValueError, "đã được xử lý"):
            WalletService.approve_withdraw(withdrawal.wallet_transaction_id)
        with self.assertRaisesRegex(ValueError, "không tồn tại"):
            WalletService.approve_deposit(999)
        with self.assertRaisesRegex(ValueError, "không tồn tại"):
            WalletService.approve_withdraw(999)
        with self.assertRaisesRegex(ValueError, "không phải yêu cầu nạp"):
            WalletService.approve_deposit(withdrawal.wallet_transaction_id)
        with self.assertRaisesRegex(ValueError, "không phải yêu cầu rút"):
            WalletService.approve_withdraw(deposit.wallet_transaction_id)

        other_order = OrderService.create_order(
            self.seed["other"].user_id,
            [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}],
        )
        with self.assertRaisesRegex(ValueError, "không thuộc"):
            WalletService.pay_with_wallet(uid, other_order.order_id, "THANH TOÁN FULL")
        with self.assertRaisesRegex(ValueError, "Đơn hàng không tồn tại"):
            WalletService.pay_with_wallet(uid, 999, "THANH TOÁN FULL")

        own = OrderService.create_order(
            uid,
            [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}],
        )
        pending = Payment(
            order_id=own.order_id,
            amount=1,
            payment_method="TPBANK",
            payment_type="THANH TOÁN FULL",
            payment_status="ĐANG THANH TOÁN",
            transaction_id="WALLET-PENDING",
        )
        db.session.add(pending)
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "chưa hoàn tất"):
            WalletService.pay_with_wallet(uid, own.order_id, "THANH TOÁN FULL")


if __name__ == "__main__":
    unittest.main()
