import unittest
from unittest.mock import patch
from config import db
from modules.orders.services import OrderService
from tests.support import DatabaseTestCase


class InventoryRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_inventory_admin_lifecycle_routes(self):
        headers = self.access_headers("admin")
        stock_id = self.seed["stock_product"].product_id
        spare_id = self.seed["spare_product"].product_id
        self.assertEqual(self.client.get("/api/inventories/admin?active=true", headers=headers).status_code, 200)
        self.assertEqual(
            self.client.post(
                "/api/inventories/admin",
                json={"product_id": spare_id, "quantity": 2, "price": 40000},
                headers=headers,
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                f"/api/inventories/admin/{stock_id}/import",
                json={"quantity": 3, "price": 70000},
                headers=headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                f"/api/inventories/admin/{stock_id}/export",
                json={"quantity": 2},
                headers=headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                f"/api/inventories/admin/{stock_id}/quantity",
                json={"quantity": 8},
                headers=headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"/api/inventories/admin/{stock_id}/status", headers=headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                f"/api/inventories/admin/transactions?product_id={stock_id}&transaction_type=NHẬP",
                headers=headers,
            ).status_code,
            200,
        )

    def test_inventory_route_permissions_validations_and_errors(self):
        customer = self.access_headers()
        admin = self.access_headers("admin")
        stock_id = self.seed["stock_product"].product_id
        self.assertEqual(self.client.get("/api/inventories/admin", headers=customer).status_code, 403)
        self.assertEqual(self.client.get("/api/inventories/admin?active=bad", headers=admin).status_code, 400)
        self.assertEqual(self.client.post("/api/inventories/admin", json={}, headers=admin).status_code, 400)
        self.assertEqual(
            self.client.post(
                f"/api/inventories/admin/{stock_id}/export", json={"quantity": 999}, headers=admin
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get("/api/inventories/admin/99999/status", headers=admin).status_code, 404)
        self.assertEqual(
            self.client.get(
                "/api/inventories/admin/transactions?transaction_type=BAD", headers=admin
            ).status_code,
            400,
        )
        with patch("modules.inventories.routes.InventoryService.get_all_inventory", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/inventories/admin", headers=admin).status_code, 500)

    def test_all_inventory_route_unexpected_error_handlers(self):
        headers = self.access_headers("admin")
        pid = self.seed["stock_product"].product_id
        cases = [
            ("create_inventory", "post", "/api/inventories/admin", {}),
            ("import_stock", "post", f"/api/inventories/admin/{pid}/import", {}),
            ("export_stock", "post", f"/api/inventories/admin/{pid}/export", {}),
            ("update_stock", "put", f"/api/inventories/admin/{pid}/quantity", {}),
            ("get_inventory_status", "get", f"/api/inventories/admin/{pid}/status", None),
            ("get_inventory_transactions", "get", "/api/inventories/admin/transactions", None),
        ]
        for service, method, url, payload in cases:
            with self.subTest(url=url), patch(
                f"modules.inventories.routes.InventoryService.{service}", side_effect=RuntimeError("db")
            ):
                kwargs = {"headers": headers}
                if payload is not None:
                    kwargs["json"] = payload
                self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 500)


class CartRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_cart_route_lifecycle(self):
        headers = self.access_headers()
        self.assertEqual(self.client.get("/api/cart", headers=headers).status_code, 200)
        added = self.client.post(
            "/api/cart/items",
            json={"product_id": self.seed["stock_product"].product_id, "quantity": 2},
            headers=headers,
        )
        self.assertEqual(added.status_code, 201)
        item_id = added.get_json()["data"]["item"]["cart_item_id"]
        self.assertEqual(
            self.client.put(
                f"/api/cart/items/{item_id}", json={"quantity": 3}, headers=headers
            ).status_code,
            200,
        )
        self.assertEqual(self.client.delete(f"/api/cart/items/{item_id}", headers=headers).status_code, 200)
        self.client.post(
            "/api/cart/items",
            json={"product_id": self.seed["preorder_product"].product_id, "quantity": 1},
            headers=headers,
        )
        self.assertEqual(self.client.delete("/api/cart", headers=headers).status_code, 200)

    def test_cart_route_validation_and_errors(self):
        headers = self.access_headers()
        self.assertEqual(self.client.post("/api/cart/items", json={}, headers=headers).status_code, 400)
        self.assertEqual(self.client.put("/api/cart/items/99999", json={"quantity": 1}, headers=headers).status_code, 400)
        self.assertEqual(self.client.delete("/api/cart/items/99999", headers=headers).status_code, 400)
        with patch("modules.carts.routes.CartService.get_cart", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/cart", headers=headers).status_code, 500)
        with patch("modules.carts.routes.CartService.clear_cart", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.delete("/api/cart", headers=headers).status_code, 500)

    def test_all_cart_route_unexpected_error_handlers(self):
        headers = self.access_headers()
        cases = [
            ("add_item", "post", "/api/cart/items", {}),
            ("update_quantity", "put", "/api/cart/items/1", {}),
            ("remove_item", "delete", "/api/cart/items/1", None),
        ]
        for service, method, url, payload in cases:
            with self.subTest(url=url), patch(
                f"modules.carts.routes.CartService.{service}", side_effect=RuntimeError("db")
            ):
                kwargs = {"headers": headers}
                if payload is not None:
                    kwargs["json"] = payload
                self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 500)


class WalletRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_wallet_deposit_withdraw_and_admin_routes(self):
        customer = self.access_headers()
        admin = self.access_headers("admin")
        self.assertEqual(self.client.get("/api/wallets/me", headers=customer).status_code, 200)
        self.assertEqual(self.client.get("/api/wallets/me/transactions", headers=customer).status_code, 200)

        cancel_deposit = self.client.post(
            "/api/wallets/deposit",
            json={"amount": 20000, "description": "route cancel"},
            headers=customer,
        )
        self.assertEqual(cancel_deposit.status_code, 201)
        cancel_id = cancel_deposit.get_json()["data"]["transaction"]["wallet_transaction_id"]
        self.assertEqual(self.client.get(f"/api/wallets/deposit/{cancel_id}", headers=customer).status_code, 200)
        self.assertEqual(
            self.client.put(f"/api/wallets/deposit/{cancel_id}/cancel", headers=customer).status_code,
            200,
        )

        approve_deposit = self.client.post(
            "/api/wallets/deposit", json={"amount": 30000}, headers=customer
        )
        approve_id = approve_deposit.get_json()["data"]["transaction"]["wallet_transaction_id"]
        self.assertEqual(
            self.client.put(
                f"/api/wallets/admin/deposits/{approve_id}/approve", headers=admin
            ).status_code,
            200,
        )
        withdrawal = self.client.post(
            "/api/wallets/withdraw", json={"amount": 10000}, headers=customer
        )
        self.assertEqual(withdrawal.status_code, 201)
        withdrawal_id = withdrawal.get_json()["data"]["transaction"]["wallet_transaction_id"]
        self.assertEqual(
            self.client.put(
                f"/api/wallets/admin/withdrawals/{withdrawal_id}/approve", headers=admin
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/wallets/admin/deposits", headers=admin).status_code, 200)

    def test_wallet_payment_route(self):
        order = OrderService.create_order(
            self.seed["customer"].user_id,
            [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}],
        )
        self.assertEqual(
            self.client.post(
                f"/api/wallets/pay/{order.order_id}",
                json={"payment_type": "THANH TOÁN FULL"},
                headers=self.access_headers(),
            ).status_code,
            200,
        )

    def test_wallet_route_permissions_validations_and_errors(self):
        customer = self.access_headers()
        admin = self.access_headers("admin")
        self.assertEqual(self.client.post("/api/wallets/deposit", json={}, headers=customer).status_code, 400)
        self.assertEqual(self.client.post("/api/wallets/withdraw", json={"amount": -1}, headers=customer).status_code, 400)
        self.assertEqual(self.client.get("/api/wallets/me/transactions?transaction_type=BAD", headers=customer).status_code, 400)
        self.assertEqual(self.client.get("/api/wallets/deposit/99999", headers=customer).status_code, 404)
        self.assertEqual(self.client.put("/api/wallets/deposit/99999/cancel", headers=customer).status_code, 400)
        self.assertEqual(self.client.get("/api/wallets/admin/deposits", headers=customer).status_code, 403)
        self.assertEqual(self.client.put("/api/wallets/admin/deposits/99999/approve", headers=admin).status_code, 400)
        with patch("modules.wallets.routes.WalletService.get_wallet_by_user", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/wallets/me", headers=customer).status_code, 500)

    def test_all_wallet_route_unexpected_error_handlers(self):
        customer = self.access_headers()
        admin = self.access_headers("admin")
        cases = [
            ("get_transactions", "get", "/api/wallets/me/transactions", None, customer),
            ("create_deposit_request", "post", "/api/wallets/deposit", {}, customer),
            ("create_withdraw_request", "post", "/api/wallets/withdraw", {}, customer),
            ("pay_with_wallet", "post", "/api/wallets/pay/1", {}, customer),
            ("approve_deposit", "put", "/api/wallets/admin/deposits/1/approve", None, admin),
            ("approve_withdraw", "put", "/api/wallets/admin/withdrawals/1/approve", None, admin),
            ("get_deposit_by_id", "get", "/api/wallets/deposit/1", None, customer),
            ("cancel_deposit_request", "put", "/api/wallets/deposit/1/cancel", None, customer),
            ("get_all_deposits_admin", "get", "/api/wallets/admin/deposits", None, admin),
        ]
        for service, method, url, payload, headers in cases:
            with self.subTest(url=url), patch(
                f"modules.wallets.routes.WalletService.{service}", side_effect=RuntimeError("db")
            ):
                kwargs = {"headers": headers}
                if payload is not None:
                    kwargs["json"] = payload
                self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 500)


class AnalyticsRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_all_analytics_routes(self):
        headers = self.access_headers("admin")
        urls = [
            "/api/analytics/dashboard",
            "/api/analytics/revenue?start_date=2020-01-01&end_date=2030-01-01",
            "/api/analytics/orders",
            "/api/analytics/products/best-selling?limit=5",
            "/api/analytics/inventory/low-stock",
            "/api/analytics/customers?limit=5",
            "/api/analytics/admin/stats",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, headers=headers).status_code, 200)

    def test_analytics_permissions_validations_and_errors(self):
        customer = self.access_headers()
        admin = self.access_headers("admin")
        for url in ["/api/analytics/dashboard", "/api/analytics/revenue", "/api/analytics/orders", "/api/analytics/products/best-selling", "/api/analytics/inventory/low-stock", "/api/analytics/customers"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url, headers=customer).status_code, 403)
        self.assertEqual(self.client.get("/api/analytics/revenue?start_date=bad", headers=admin).status_code, 400)
        self.assertEqual(
            self.client.get(
                "/api/analytics/revenue?start_date=2026-02-01&end_date=2026-01-01", headers=admin
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get("/api/analytics/products/best-selling?limit=0", headers=admin).status_code, 400)
        self.assertEqual(self.client.get("/api/analytics/customers?limit=0", headers=admin).status_code, 400)
        with patch("modules.analytics.routes.AnalyticsService.get_dashboard_summary", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/analytics/dashboard", headers=admin).status_code, 500)
        with patch("modules.analytics.routes.AnalyticsService.get_low_stock_products", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/analytics/admin/stats", headers=admin).status_code, 500)

    def test_all_analytics_route_unexpected_error_handlers(self):
        headers = self.access_headers("admin")
        cases = [
            ("get_revenue_report", "/api/analytics/revenue"),
            ("get_order_statistics", "/api/analytics/orders"),
            ("get_best_selling_products", "/api/analytics/products/best-selling"),
            ("get_low_stock_products", "/api/analytics/inventory/low-stock"),
            ("get_customer_statistics", "/api/analytics/customers"),
        ]
        for service, url in cases:
            with self.subTest(url=url), patch(
                f"modules.analytics.routes.AnalyticsService.{service}", side_effect=RuntimeError("db")
            ):
                self.assertEqual(self.client.get(url, headers=headers).status_code, 500)


class NotificationRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_notification_send_and_read_routes(self):
        OrderService.create_order(
            self.seed["customer"].user_id,
            [{"product_id": self.seed["preorder_product"].product_id, "preorder_id": self.seed["preorder"].preorder_id, "quantity": 1}],
        )
        with patch("modules.notifications.services.send_email"):
            sent = self.client.post(
                f"/api/notifications/admin/preorders/{self.seed['preorder'].preorder_id}",
                json={"title": "Route update", "message": "Route message"},
                headers=self.access_headers("admin"),
            )
        self.assertEqual(sent.status_code, 200, sent.get_json())
        self.assertEqual(self.client.get("/api/notifications/me", headers=self.access_headers()).status_code, 200)

    def test_notification_empty_permission_validation_and_errors(self):
        preorder_id = self.seed["preorder"].preorder_id
        self.assertEqual(
            self.client.post(
                f"/api/notifications/admin/preorders/{preorder_id}",
                json={"title": "No customer", "message": "Nothing"},
                headers=self.access_headers("admin"),
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f"/api/notifications/admin/preorders/{preorder_id}",
                json={},
                headers=self.access_headers("admin"),
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                f"/api/notifications/admin/preorders/{preorder_id}",
                json={"title": "x", "message": "y"},
                headers=self.access_headers(),
            ).status_code,
            403,
        )
        with patch("modules.notifications.routes.NotificationService.get_user_notifications", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/notifications/me", headers=self.access_headers()).status_code, 500)
        with patch("modules.notifications.routes.NotificationService.send_preorder_notification", side_effect=RuntimeError("db")):
            self.assertEqual(
                self.client.post(
                    f"/api/notifications/admin/preorders/{preorder_id}",
                    json={},
                    headers=self.access_headers("admin"),
                ).status_code,
                500,
            )


if __name__ == "__main__":
    unittest.main()
