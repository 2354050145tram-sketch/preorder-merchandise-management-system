import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from config import db
from modules.orders.models import Order, Payment
from tests.support import DatabaseTestCase


class OrderRouteTests(DatabaseTestCase, unittest.TestCase):
    def order_payload(self, mixed=True):
        items = [
            {
                "product_id": self.seed["stock_product"].product_id,
                "preorder_id": None,
                "quantity": 1,
            }
        ]
        if mixed:
            items.append(
                {
                    "product_id": self.seed["preorder_product"].product_id,
                    "preorder_id": self.seed["preorder"].preorder_id,
                    "quantity": 1,
                }
            )
        return {"items": items}

    def create_order(self, mixed=True, user_key="customer"):
        response = self.client.post(
            "/api/orders",
            json=self.order_payload(mixed),
            headers=self.access_headers(user_key),
        )
        self.assertEqual(response.status_code, 201, response.get_json())
        order_id = response.get_json()["data"]["order"]["order_id"]
        return db.session.get(Order, order_id)

    def test_create_list_detail_and_admin_order_routes(self):
        order = self.create_order()
        customer = self.access_headers()
        admin = self.access_headers("admin")
        self.assertEqual(self.client.get("/api/orders/my-orders", headers=customer).status_code, 200)
        self.assertEqual(self.client.get(f"/api/orders/{order.order_id}", headers=customer).status_code, 200)
        self.assertEqual(self.client.get("/api/orders/admin?active=true", headers=admin).status_code, 200)
        self.assertEqual(self.client.get(f"/api/orders/admin/{order.order_id}", headers=admin).status_code, 200)
        self.assertEqual(
            self.client.get(
                f"/api/orders/admin/product/{self.seed['preorder_product'].product_id}/preorder-customers",
                headers=admin,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"/api/orders/{order.order_id}/check-payment-status", headers=customer).status_code,
            200,
        )

    def test_order_status_shipping_and_cancel_routes(self):
        order = self.create_order()
        admin = self.access_headers("admin")
        customer = self.access_headers()
        item_ids = [item.order_item_id for item in order.order_items]
        self.assertEqual(
            self.client.put(
                f"/api/orders/admin/{order.order_id}/status",
                json={"order_status": "ĐÃ XÁC NHẬN"},
                headers=admin,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                f"/api/orders/admin/{order.order_id}/shipping",
                json={
                    "order_item_ids": item_ids,
                    "shipping_method": "TIÊU CHUẨN",
                    "shipping_fee": 30000,
                    "tracking_code": "ROUTE-TRACK-1",
                },
                headers=admin,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                f"/api/orders/items/{item_ids[0]}/cancel", headers=customer
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                "/api/orders/admin/shipping/ROUTE-TRACK-1/status",
                json={"shipping_status": "ĐANG GIAO HÀNG"},
                headers=admin,
            ).status_code,
            200,
        )

    def test_payment_routes_and_summary(self):
        order = self.create_order()
        customer = self.access_headers()
        paid = self.client.post(
            f"/api/orders/{order.order_id}/payments",
            json={
                "payment_method": "TPBANK",
                "payment_type": "THANH TOÁN FULL",
                "transaction_id": "ROUTE-TPBANK-1",
            },
            headers=customer,
        )
        self.assertEqual(paid.status_code, 201, paid.get_json())
        self.assertEqual(
            self.client.get(f"/api/orders/{order.order_id}/payments", headers=customer).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(f"/api/orders/{order.order_id}/payment-summary", headers=customer).status_code,
            200,
        )
        self.assertEqual(self.client.get("/api/orders/deposit-eligibility", headers=customer).status_code, 200)

        second = self.create_order(mixed=False)
        pending = Payment(
            order_id=second.order_id,
            amount=second.total_amount,
            payment_method="TPBANK",
            payment_type="THANH TOÁN FULL",
            payment_status="ĐANG THANH TOÁN",
            transaction_id="ROUTE-CONFIRM-1",
        )
        db.session.add(pending)
        db.session.commit()
        self.assertEqual(
            self.client.put(
                f"/api/orders/admin/payments/{pending.payment_id}/confirm",
                headers=self.access_headers("admin"),
            ).status_code,
            200,
        )

        third = self.create_order(mixed=False)
        cancellable = Payment(
            order_id=third.order_id,
            amount=Decimal("100000"),
            payment_method="TPBANK",
            payment_type="THANH TOÁN FULL",
            payment_status="ĐANG THANH TOÁN",
            transaction_id="ROUTE-CANCEL-1",
        )
        db.session.add(cancellable)
        db.session.commit()
        self.assertEqual(
            self.client.put(
                f"/api/orders/payments/{cancellable.payment_id}/cancel", headers=customer
            ).status_code,
            200,
        )

    def test_refund_route(self):
        order = self.create_order(mixed=False)
        customer = self.access_headers()
        self.assertEqual(
            self.client.post(
                f"/api/orders/{order.order_id}/payments",
                json={"payment_method": "TPBANK", "payment_type": "THANH TOÁN FULL", "transaction_id": "REFUND-PAID"},
                headers=customer,
            ).status_code,
            201,
        )
        item_id = order.order_items[0].order_item_id
        self.assertEqual(
            self.client.put(f"/api/orders/items/{item_id}/cancel", headers=customer).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                f"/api/orders/admin/items/{item_id}/refund",
                headers=self.access_headers("admin"),
            ).status_code,
            200,
        )

    def test_order_route_authorization_and_validation(self):
        order = self.create_order()
        customer = self.access_headers()
        other = self.access_headers("other")
        admin = self.access_headers("admin")
        self.assertEqual(self.client.post("/api/orders", json={}, headers=customer).status_code, 400)
        self.assertEqual(self.client.get(f"/api/orders/{order.order_id}", headers=other).status_code, 403)
        self.assertEqual(self.client.get("/api/orders/99999", headers=customer).status_code, 404)
        self.assertEqual(self.client.get("/api/orders/admin", headers=customer).status_code, 403)
        self.assertEqual(self.client.get("/api/orders/admin/99999", headers=admin).status_code, 404)
        self.assertEqual(
            self.client.put(
                f"/api/orders/admin/{order.order_id}/status",
                json={"order_status": "BAD"},
                headers=admin,
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                f"/api/orders/{order.order_id}/payments",
                json={"payment_method": "CASH", "payment_type": "THANH TOÁN FULL"},
                headers=customer,
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(f"/api/orders/{order.order_id}/payments", headers=other).status_code,
            403,
        )
        self.assertEqual(self.client.put("/api/orders/items/99999/cancel", headers=customer).status_code, 400)
        self.assertEqual(self.client.put("/api/orders/payments/99999/cancel", headers=customer).status_code, 400)

    def test_order_route_unexpected_errors(self):
        customer = self.access_headers()
        admin = self.access_headers("admin")
        patches = [
            ("modules.orders.routes.OrderService.get_orders_by_user", "get", "/api/orders/my-orders", customer),
            ("modules.orders.routes.OrderService.get_all_orders", "get", "/api/orders/admin", admin),
            ("modules.orders.routes.PaymentService.has_previous_paid_order", "get", "/api/orders/deposit-eligibility", customer),
            ("modules.orders.routes.OrderService.get_order_by_id", "get", "/api/orders/1/check-payment-status", customer),
        ]
        for target, method, url, headers in patches:
            with self.subTest(url=url), patch(target, side_effect=RuntimeError("db")):
                response = getattr(self.client, method)(url, headers=headers)
                self.assertEqual(response.status_code, 500)

    def test_remaining_order_route_unexpected_error_handlers(self):
        order = self.create_order()
        customer = self.access_headers()
        admin = self.access_headers("admin")
        item_id = order.order_items[0].order_item_id
        pending = Payment(
            order_id=order.order_id,
            amount=1,
            payment_method="TPBANK",
            payment_type="THANH TOÁN FULL",
            payment_status="ĐANG THANH TOÁN",
            transaction_id="GENERIC-ERROR-PAYMENT",
        )
        db.session.add(pending)
        db.session.commit()
        cases = [
            ("OrderService.create_order", "post", "/api/orders", {}, customer),
            ("OrderService.get_order_by_id", "get", f"/api/orders/{order.order_id}", None, customer),
            ("OrderService.get_order_by_id", "get", f"/api/orders/admin/{order.order_id}", None, admin),
            ("OrderService.update_order_status", "put", f"/api/orders/admin/{order.order_id}/status", {}, admin),
            ("OrderService.update_shipping_info", "post", f"/api/orders/admin/{order.order_id}/shipping", {}, admin),
            ("OrderService.update_shipping_status", "put", "/api/orders/admin/shipping/X/status", {}, admin),
            ("PaymentService.create_payment", "post", f"/api/orders/{order.order_id}/payments", {"payment_method": "TPBANK", "payment_type": "THANH TOÁN FULL"}, customer),
            ("PaymentService.get_payments_by_order", "get", f"/api/orders/{order.order_id}/payments", None, customer),
            ("PaymentService.confirm_payment", "put", f"/api/orders/admin/payments/{pending.payment_id}/confirm", None, admin),
            ("PaymentService.cancel_payment", "put", f"/api/orders/payments/{pending.payment_id}/cancel", None, customer),
            ("PaymentService.refund_order_item", "post", f"/api/orders/admin/items/{item_id}/refund", None, admin),
            ("PaymentService.get_order_payment_summary", "get", f"/api/orders/{order.order_id}/payment-summary", None, customer),
        ]
        for target, method, url, payload, headers in cases:
            with self.subTest(url=url), patch(
                f"modules.orders.routes.{target}", side_effect=RuntimeError("db")
            ):
                kwargs = {"headers": headers}
                if payload is not None:
                    kwargs["json"] = payload
                self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 500)

        with patch.object(db.session, "execute", side_effect=RuntimeError("db")):
            self.assertEqual(
                self.client.get(
                    f"/api/orders/admin/product/{self.seed['preorder_product'].product_id}/preorder-customers",
                    headers=admin,
                ).status_code,
                500,
            )


if __name__ == "__main__":
    unittest.main()
