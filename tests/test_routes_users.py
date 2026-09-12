import unittest
from unittest.mock import Mock, patch
from flask import redirect
from modules.products.models import Product
from modules.orders.services import OrderService
from modules.wallets.services import WalletService
from tests.support import DatabaseTestCase


class UserRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_register_login_refresh_me_profile_and_password_routes(self):
        registered = self.client.post(
            "/api/users/register",
            json={
                "email": "new@example.com",
                "username": "new-user",
                "password": "secret123",
                "confirm_password": "secret123",
                "full_name": "New User",
                "phone_num": "0912345678",
                "address": "Hồ Chí Minh",
            },
        )
        self.assertEqual(registered.status_code, 201, registered.get_json())
        self.assertEqual(
            self.client.post(
                "/api/users/login",
                json={"login": "customer", "password": "customer123"},
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/users/refresh", headers=self.refresh_headers()
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/api/users/me", headers=self.access_headers()).status_code,
            200,
        )
        customer_id = self.seed["customer"].user_id
        self.assertEqual(
            self.client.put(
                f"/api/users/{customer_id}/profile",
                json={"full_name": "Customer Updated", "address": "Đà Nẵng"},
                headers=self.access_headers(),
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                "/api/users/change-password",
                json={"old_password": "customer123", "new_password": "changed123"},
                headers=self.access_headers(),
            ).status_code,
            200,
        )

    def test_user_route_validation_and_authorization(self):
        self.assertEqual(self.client.post("/api/users/register", json={}).status_code, 400)
        self.assertEqual(self.client.post("/api/users/login", json={}).status_code, 401)
        self.assertEqual(self.client.get("/api/users/oauth/session").status_code, 401)
        self.assertEqual(
            self.client.put(
                f"/api/users/{self.seed['other'].user_id}/profile",
                json={},
                headers=self.access_headers(),
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.put(
                "/api/users/change-password",
                json={"old_password": "wrong", "new_password": "x"},
                headers=self.access_headers(),
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get("/api/users/admin", headers=self.access_headers()).status_code,
            403,
        )

    def test_admin_user_routes(self):
        headers = self.access_headers("admin")
        customer_id = self.seed["customer"].user_id
        self.assertEqual(self.client.get("/api/users/admin", headers=headers).status_code, 200)
        self.assertEqual(
            self.client.get(f"/api/users/admin/{customer_id}", headers=headers).status_code,
            200,
        )
        locked = self.client.put(
            f"/api/users/admin/{customer_id}/status",
            json={"active": False},
            headers=headers,
        )
        self.assertEqual(locked.status_code, 200)
        self.assertEqual(
            self.client.put(
                f"/api/users/admin/{self.seed['other'].user_id}/status",
                json={},
                headers=headers,
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get("/api/users/admin/99999", headers=headers).status_code,
            404,
        )

    def test_admin_user_detail_serializes_orders_and_wallet_transactions(self):
        customer_id = self.seed["customer"].user_id
        OrderService.create_order(
            customer_id,
            [{"product_id": self.seed["stock_product"].product_id, "preorder_id": None, "quantity": 1}],
        )
        WalletService.create_deposit_request(customer_id, 20000, "detail route")
        response = self.client.get(
            f"/api/users/admin/{customer_id}", headers=self.access_headers("admin")
        )
        self.assertEqual(response.status_code, 200)
        detail = response.get_json()["data"]["user"]
        self.assertEqual(len(detail["orders"]), 1)
        self.assertEqual(len(detail["wallet_transactions"]), 1)

    def test_google_and_facebook_oauth_routes(self):
        with patch("modules.users.routes.google.authorize_redirect", return_value=("google", 302)):
            self.assertEqual(self.client.get("/api/users/auth/google").status_code, 302)
        with patch("modules.users.routes.facebook.authorize_redirect", return_value=("facebook", 302)):
            self.assertEqual(self.client.get("/api/users/auth/facebook").status_code, 302)

        google_info = {
            "userinfo": {
                "sub": "google-route-1",
                "email": "google-route@example.com",
                "email_verified": True,
                "name": "Google Route",
                "picture": "avatar.png",
            }
        }
        with patch("modules.users.routes.google.authorize_access_token", return_value=google_info):
            self.assertEqual(self.client.get("/api/users/auth/google/callback").status_code, 302)
        self.assertEqual(self.client.get("/api/users/oauth/session").status_code, 200)

        fb_response = Mock()
        fb_response.json.return_value = {
            "id": "facebook-route-1",
            "email": "facebook-route@example.com",
            "name": "Facebook Route",
            "picture": {"data": {"url": "fb.png"}},
        }
        with patch("modules.users.routes.facebook.authorize_access_token", return_value={"access_token": "x"}), patch(
            "modules.users.routes.facebook.get", return_value=fb_response
        ):
            self.assertEqual(self.client.get("/api/users/auth/facebook/callback").status_code, 302)
        self.assertEqual(self.client.get("/api/users/oauth/session").status_code, 200)

    def test_oauth_and_user_unexpected_errors_are_json(self):
        with patch("modules.users.routes.google.authorize_access_token", return_value={}):
            self.assertEqual(self.client.get("/api/users/auth/google/callback").status_code, 400)
        bad_fb = Mock()
        bad_fb.json.return_value = {"id": "fb-without-email"}
        with patch("modules.users.routes.facebook.authorize_access_token", return_value={}), patch(
            "modules.users.routes.facebook.get", return_value=bad_fb
        ):
            self.assertEqual(self.client.get("/api/users/auth/facebook/callback").status_code, 400)
        with patch("modules.users.routes.UserService.register", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.post("/api/users/register", json={}).status_code, 500)
        with patch("modules.users.routes.UserService.login", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.post("/api/users/login", json={}).status_code, 500)

    def test_remaining_user_route_unexpected_error_handlers(self):
        customer = self.access_headers()
        admin = self.access_headers("admin")
        customer_id = self.seed["customer"].user_id
        cases = [
            ("get_user_by_id", "post", "/api/users/refresh", None, self.refresh_headers()),
            ("get_user_by_id", "put", f"/api/users/{customer_id}/profile", {}, customer),
            ("change_password", "put", "/api/users/change-password", {}, customer),
            ("get_all_users_admin", "get", "/api/users/admin", None, admin),
            ("get_user_detail_admin", "get", f"/api/users/admin/{customer_id}", None, admin),
            ("toggle_user_status", "put", f"/api/users/admin/{customer_id}/status", {"active": False}, admin),
        ]
        for service, method, url, payload, headers in cases:
            with self.subTest(url=url), patch(
                f"modules.users.routes.UserService.{service}", side_effect=RuntimeError("db")
            ):
                kwargs = {"headers": headers}
                if payload is not None:
                    kwargs["json"] = payload
                self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 500)

        with patch("modules.users.routes.google.authorize_access_token", side_effect=RuntimeError("oauth")):
            self.assertEqual(self.client.get("/api/users/auth/google/callback").status_code, 500)
        with patch("modules.users.routes.facebook.authorize_access_token", side_effect=RuntimeError("oauth")):
            self.assertEqual(self.client.get("/api/users/auth/facebook/callback").status_code, 500)


class ProductRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_public_catalog_routes(self):
        product_id = self.seed["stock_product"].product_id
        category_id = self.seed["category"].category_id
        sub_id = self.seed["sub_category"].sub_category_id
        urls = [
            "/api/products",
            f"/api/products/{product_id}",
            "/api/products/categories",
            f"/api/products/categories/{category_id}/sub-categories",
            "/api/products/tags",
            f"/api/products/sub-categories/{sub_id}/tags",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get("/api/products?min_price=bad").status_code, 400)
        self.assertEqual(self.client.get("/api/products/99999").status_code, 404)
        self.assertEqual(
            self.client.get("/api/products/categories/99999/sub-categories").status_code,
            404,
        )
        self.assertEqual(
            self.client.get("/api/products/sub-categories/99999/tags").status_code,
            404,
        )

    def test_admin_product_crud_and_tag_routes(self):
        headers = self.access_headers("admin")
        created = self.client.post(
            "/api/products/admin",
            json={
                "product_name": "Sản phẩm route",
                "price": 123000,
                "description": "test",
                "image": "route.jpg",
                "status": "IN_STOCK",
                "tag_ids": [self.seed["tag"].tag_id],
            },
            headers=headers,
        )
        self.assertEqual(created.status_code, 201, created.get_json())
        product_id = created.get_json()["data"]["product"]["product_id"]
        self.assertEqual(
            self.client.put(
                f"/api/products/admin/{product_id}",
                json={"price": 150000, "tag_ids": [self.seed["other_tag"].tag_id]},
                headers=headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/products/tags",
                json={"name": "Route Tag", "sub_category_id": self.seed["sub_category"].sub_category_id},
                headers=headers,
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.delete(f"/api/products/admin/{product_id}", headers=headers).status_code,
            200,
        )

    def test_product_admin_permission_validation_and_server_errors(self):
        self.assertEqual(
            self.client.post("/api/products/admin", json={}, headers=self.access_headers()).status_code,
            403,
        )
        self.assertEqual(
            self.client.post("/api/products/admin", json={}, headers=self.access_headers("admin")).status_code,
            400,
        )
        self.assertEqual(
            self.client.put("/api/products/admin/99999", json={}, headers=self.access_headers("admin")).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/products/tags", json={}, headers=self.access_headers("admin")).status_code,
            400,
        )
        with patch("modules.products.routes.ProductService.get_categories", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/products/categories").status_code, 500)
        with patch("modules.products.routes.ProductService.get_all_tags", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/products/tags").status_code, 500)

    def test_all_product_route_unexpected_error_handlers(self):
        admin = self.access_headers("admin")
        pid = self.seed["stock_product"].product_id
        sub_id = self.seed["sub_category"].sub_category_id
        cases = [
            ("ProductService.get_all_products", "get", "/api/products", None, None),
            ("ProductService.get_product_by_id", "get", f"/api/products/{pid}", None, None),
            ("ProductService.create_product", "post", "/api/products/admin", {}, admin),
            ("ProductService.update_product", "put", f"/api/products/admin/{pid}", {}, admin),
            ("ProductService.delete_product", "delete", f"/api/products/admin/{pid}", None, admin),
            ("ProductService.get_sub_categories", "get", f"/api/products/categories/{self.seed['category'].category_id}/sub-categories", None, None),
            ("ProductService.get_tags_by_sub_category", "get", f"/api/products/sub-categories/{sub_id}/tags", None, None),
            ("ProductService.create_tag", "post", "/api/products/tags", {}, admin),
        ]
        for service, method, url, payload, headers in cases:
            with self.subTest(url=url), patch(f"modules.products.routes.{service}", side_effect=RuntimeError("db")):
                kwargs = {"headers": headers} if headers else {}
                if payload is not None:
                    kwargs["json"] = payload
                self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 500)


class PreOrderRouteTests(DatabaseTestCase, unittest.TestCase):
    def test_public_and_admin_preorder_lifecycle(self):
        preorder_id = self.seed["preorder"].preorder_id
        self.assertEqual(self.client.get("/api/preorders").status_code, 200)
        self.assertEqual(self.client.get(f"/api/preorders/{preorder_id}").status_code, 200)
        headers = self.access_headers("admin")
        self.assertEqual(self.client.get("/api/preorders/admin?active=true", headers=headers).status_code, 200)

        product = Product(
            product_name="Preorder route mới",
            price=250000,
            description="route",
            image="preorder-route.jpg",
            status="PREORDER",
        )
        from config import db

        db.session.add(product)
        db.session.commit()
        created = self.client.post(
            "/api/preorders/admin",
            json={
                "product_id": product.product_id,
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "progress_note": "Mở preorder từ route",
            },
            headers=headers,
        )
        self.assertEqual(created.status_code, 201)
        new_id = created.get_json()["data"]["preorder"]["preorder_id"]
        self.assertEqual(
            self.client.put(
                f"/api/preorders/admin/{new_id}",
                json={"end_date": "2027-01-31", "progress_note": "updated"},
                headers=headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.put(
                f"/api/preorders/admin/{new_id}/progress",
                json={"progress_status": "ĐÃ VỀ KHO VIỆT NAM", "progress_note": "done"},
                headers=headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(f"/api/preorders/admin/{new_id}", headers=headers).status_code,
            200,
        )

    def test_preorder_permission_validation_and_unexpected_errors(self):
        admin = self.access_headers("admin")
        customer = self.access_headers()
        self.assertEqual(self.client.get("/api/preorders/99999").status_code, 404)
        self.assertEqual(self.client.get("/api/preorders/admin", headers=customer).status_code, 403)
        self.assertEqual(self.client.get("/api/preorders/admin?active=bad", headers=admin).status_code, 400)
        self.assertEqual(self.client.post("/api/preorders/admin", json={}, headers=admin).status_code, 400)
        self.assertEqual(
            self.client.put(
                f"/api/preorders/admin/{self.seed['preorder'].preorder_id}",
                json={"start_date": "not-a-date"},
                headers=admin,
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.put("/api/preorders/admin/99999/progress", json={}, headers=admin).status_code,
            400,
        )
        with patch("modules.preorders.routes.PreOrderService.get_all_preorders", side_effect=RuntimeError("db")):
            self.assertEqual(self.client.get("/api/preorders").status_code, 500)

    def test_all_preorder_route_unexpected_error_handlers(self):
        admin = self.access_headers("admin")
        preorder_id = self.seed["preorder"].preorder_id
        cases = [
            ("get_preorder_by_id", "get", f"/api/preorders/{preorder_id}", None, None),
            ("get_all_preorders", "get", "/api/preorders/admin", None, admin),
            ("create_preorder", "post", "/api/preorders/admin", {"start_date": "2026-01-01", "end_date": "2026-12-31"}, admin),
            ("update_preorder", "put", f"/api/preorders/admin/{preorder_id}", {}, admin),
            ("update_progress", "put", f"/api/preorders/admin/{preorder_id}/progress", {}, admin),
            ("delete_preorder", "delete", f"/api/preorders/admin/{preorder_id}", None, admin),
        ]
        for service, method, url, payload, headers in cases:
            with self.subTest(url=url), patch(
                f"modules.preorders.routes.PreOrderService.{service}", side_effect=RuntimeError("db")
            ):
                kwargs = {"headers": headers} if headers else {}
                if payload is not None:
                    kwargs["json"] = payload
                self.assertEqual(getattr(self.client, method)(url, **kwargs).status_code, 500)


if __name__ == "__main__":
    unittest.main()
