import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from flask_jwt_extended import decode_token
from config import app, db
from modules.analytics.services import AnalyticsService
from modules.analytics import helpers as analytics_helpers
from modules.carts.helpers import serialize_cart, serialize_cart_item
from modules.inventories import helpers as inventory_helpers
from modules.notifications.models import UserNotification
from modules.notifications.services import NotificationService
from modules.notifications import helpers as notification_helpers
from modules.orders.services import OrderService, PaymentService
from modules.orders import helpers as order_helpers
from modules.preorders import helpers as preorder_helpers
from modules.products import helpers as product_helpers
from modules.wallets import helpers as wallet_helpers
from tests.support import DatabaseTestCase
from utils.email import send_email
from utils.helpers import response_error, response_success


class AnalyticsTests(DatabaseTestCase, unittest.TestCase):
    def test_all_analytics_reports(self):
        order = OrderService.create_order(
            self.seed["customer"].user_id,
            [
                {
                    "product_id": self.seed["stock_product"].product_id,
                    "preorder_id": None,
                    "quantity": 2,
                }
            ],
        )
        PaymentService.create_payment(
            order.order_id, "TPBANK", "THANH TOÁN FULL", "ANALYTICS"
        )
        self.seed["stock_product"].inventories[0].quantity = 3
        db.session.commit()
        dashboard = AnalyticsService.get_dashboard_summary()
        self.assertEqual(dashboard["total_orders"], 1)
        self.assertGreater(dashboard["total_revenue"], 0)
        self.assertGreaterEqual(dashboard["total_customers"], 2)
        self.assertGreaterEqual(dashboard["total_products"], 3)
        self.assertEqual(dashboard["low_stock_count"], 1)
        self.assertTrue(AnalyticsService.get_revenue_report())
        self.assertTrue(
            AnalyticsService.get_revenue_report(
                datetime(2020, 1, 1), datetime(2030, 1, 1)
            )
        )
        self.assertTrue(AnalyticsService.get_order_statistics())
        self.assertTrue(AnalyticsService.get_best_selling_products(5))
        self.assertEqual(
            AnalyticsService.get_low_stock_products(5)[0]["status"], "SẮP HẾT HÀNG"
        )
        stats = AnalyticsService.get_customer_statistics(5)
        self.assertGreaterEqual(stats["total_customers"], 2)
        self.assertTrue(stats["top_customers"])

    def test_analytics_validation(self):
        for value in ["bad", 0, -1]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                AnalyticsService.get_customer_statistics(value)
        self.assertEqual(AnalyticsService.get_revenue_report(), [])
        self.assertEqual(AnalyticsService.get_order_statistics(), [])
        self.assertEqual(AnalyticsService.get_best_selling_products(), [])


class NotificationTests(DatabaseTestCase, unittest.TestCase):
    def test_notification_send_and_read(self):
        OrderService.create_order(
            self.seed["customer"].user_id,
            [
                {
                    "product_id": self.seed["preorder_product"].product_id,
                    "preorder_id": self.seed["preorder"].preorder_id,
                    "quantity": 1,
                }
            ],
        )
        with patch("modules.notifications.services.send_email") as mocked_send:
            notification = NotificationService.send_preorder_notification(
                self.seed["preorder"].preorder_id, " Update ", " Production "
            )
            notification = result["notification"]
        self.assertIsNotNone(notification)
        mocked_send.assert_called_once()
        self.assertEqual(UserNotification.query.count(), 1)
        self.assertEqual(
            NotificationService.get_user_notifications(self.seed["customer"].user_id)[
                0
            ],
            notification,
        )

    def test_notification_no_customer_and_validation(self):
        self.assertIsNone(
            NotificationService.send_preorder_notification(
                self.seed["preorder"].preorder_id, "Title", "Body"
            )
        )
        with self.assertRaises(ValueError):
            NotificationService.send_preorder_notification(999, "T", "B")
        with self.assertRaises(ValueError):
            NotificationService.send_preorder_notification(
                self.seed["preorder"].preorder_id, "", "B"
            )
        with self.assertRaises(ValueError):
            NotificationService.get_user_notifications(999)

    def test_email_failure_does_not_rollback_notification(self):
        OrderService.create_order(
            self.seed["customer"].user_id,
            [
                {
                    "product_id": self.seed["preorder_product"].product_id,
                    "preorder_id": self.seed["preorder"].preorder_id,
                    "quantity": 1,
                }
            ],
        )
        with patch(
            "modules.notifications.services.send_email",
            side_effect=RuntimeError("SMTP down"),
        ):
            notification = NotificationService.send_preorder_notification(
                self.seed["preorder"].preorder_id, "Title", "Body"
            )
        self.assertIsNotNone(notification)


class HelperTests(DatabaseTestCase, unittest.TestCase):
    def test_all_serializers(self):
        product = self.seed["preorder_product"]
        product_data = product_helpers.serialize_product(product)
        self.assertTrue(product_data["preorder_available"])
        self.assertTrue(product_data["tags"])
        self.assertEqual(
            preorder_helpers.serialize_preorder(self.seed["preorder"])["product"][
                "product_name"
            ],
            product.product_name,
        )

        order = OrderService.create_order(
            self.seed["customer"].user_id,
            [
                {
                    "product_id": self.seed["stock_product"].product_id,
                    "preorder_id": None,
                    "quantity": 1,
                }
            ],
        )
        payment = PaymentService.create_payment(
            order.order_id, "TPBANK", "THANH TOÁN FULL", "HELPER"
        )
        self.assertEqual(
            order_helpers.serialize_order(order)["order_id"], order.order_id
        )
        self.assertEqual(
            order_helpers.serialize_order_summary(order)["username"], "customer"
        )
        self.assertEqual(
            order_helpers.serialize_order_item(order.order_items[0])["product_name"],
            "Áo có sẵn",
        )
        self.assertEqual(
            order_helpers.serialize_payment(payment)["transaction_id"], "HELPER"
        )

        inventory = self.seed["stock_product"].inventories[0]
        inventory_data = inventory_helpers.serialize_inventory(inventory)
        self.assertEqual(inventory_data["status"], "CÒN HÀNG")
        tx = inventory.transactions[0]
        self.assertEqual(
            inventory_helpers.serialize_inventory_transaction(tx)["transaction_type"],
            "XUẤT",
        )

        cart = self.seed["customer"].cart
        if cart is None:
            from modules.carts.services import CartService

            cart = CartService.get_or_create_cart(self.seed["customer"].user_id)
            CartService.add_item(
                self.seed["customer"].user_id, self.seed["stock_product"].product_id, 1
            )
        self.assertEqual(serialize_cart(cart)["total_items"], 1)
        self.assertEqual(
            serialize_cart_item(cart.items[0])["product_name"], "Áo có sẵn"
        )

        wallet = self.seed["customer"].wallet
        self.assertEqual(
            wallet_helpers.serialize_wallet(wallet)["user_id"],
            self.seed["customer"].user_id,
        )
        wallet_tx = __import__(
            "modules.wallets.services", fromlist=["WalletService"]
        ).WalletService.create_deposit_request(self.seed["customer"].user_id, 20000)
        self.assertEqual(
            wallet_helpers.serialize_wallet_transaction(wallet_tx)["transaction_type"],
            "NẠP TIỀN",
        )

        notification = SimpleNamespace(
            notification_id=1,
            preorder_id=None,
            title="T",
            message="M",
            created_at=datetime.now(timezone.utc),
        )
        self.assertEqual(
            notification_helpers.serialize_notification(notification)["title"], "T"
        )

    def test_analytics_serializers_and_response_helpers(self):
        self.assertEqual(
            analytics_helpers.serialize_dashboard_summary(
                {
                    "total_revenue": 1,
                    "total_orders": 2,
                    "total_customers": 3,
                    "total_products": 4,
                    "low_stock_count": 5,
                }
            )["total_orders"],
            2,
        )
        self.assertEqual(
            analytics_helpers.serialize_revenue_report(
                {"date": date.today(), "paid": 10, "refunded": 2, "revenue": 8}
            )["revenue"],
            8.0,
        )
        self.assertEqual(
            analytics_helpers.serialize_order_statistic(
                {"order_status": "X", "total": 1}
            )["total"],
            1,
        )
        self.assertEqual(
            analytics_helpers.serialize_best_selling_product(
                {"product_id": 1, "product_name": "P", "quantity_sold": 2}
            )["quantity_sold"],
            2,
        )
        self.assertEqual(
            analytics_helpers.serialize_low_stock_product(
                {
                    "product_id": 1,
                    "product_name": "P",
                    "quantity": 0,
                    "status": "HẾT HÀNG",
                }
            )["quantity"],
            0,
        )
        self.assertEqual(
            analytics_helpers.serialize_customer_statistics(
                {
                    "total_customers": 1,
                    "top_customers": [
                        {
                            "user_id": 1,
                            "username": "u",
                            "total_orders": 1,
                            "total_paid": 2,
                            "total_refunded": 1,
                            "total_spent": 1,
                        }
                    ],
                }
            )["top_customers"][0]["total_spent"],
            1.0,
        )
        success, code = response_success({"x": 1}, "ok", 201)
        error, error_code = response_error("bad", 422)
        self.assertEqual((code, success.get_json()["status"]), (201, "success"))
        self.assertEqual((error_code, error.get_json()["status"]), (422, "error"))

    def test_email_validation_and_send(self):
        for args in [("", "S", "B"), ("a@b.com", "", "B"), ("a@b.com", "S", "")]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                send_email(*args)
        with patch("utils.email.mail.send") as mocked:
            send_email(" a@b.com ", " Subject ", " Body ")
            mocked.assert_called_once()

    def test_model_strings_and_inventory_statuses(self):
        self.assertEqual(str(self.seed["admin"].role), "ADMIN")
        self.assertEqual(str(self.seed["customer"]), "customer")
        self.assertEqual(str(self.seed["stock_product"]), "Áo có sẵn")
        self.assertEqual(str(self.seed["category"]), "Thời trang")
        self.assertEqual(str(self.seed["sub_category"]), "Áo")
        self.assertEqual(str(self.seed["tag"]), "Oversize")
        self.assertIn(
            str(self.seed["preorder"].preorder_id), str(self.seed["preorder"])
        )
        inventory = self.seed["stock_product"].inventories[0]
        inventory.quantity = 0
        self.assertEqual(inventory.status, "HẾT HÀNG")
        inventory.quantity = 5
        self.assertEqual(inventory.status, "SẮP HẾT HÀNG")
        inventory.quantity = 6
        self.assertEqual(inventory.status, "CÒN HÀNG")


if __name__ == "__main__":
    unittest.main()
