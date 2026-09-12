import unittest
from datetime import date, timedelta
from unittest.mock import patch
from config import db
from modules.users.models import Profile, User
from modules.users.services import UserService
from modules.products.models import Product, ProductTag, Tag
from modules.products.services import ProductService
from modules.preorders.models import PreOrder
from modules.preorders.services import PreOrderService
from tests.support import DatabaseTestCase


class UserServiceTests(DatabaseTestCase, unittest.TestCase):
    def test_check_duplicate_and_register(self):
        for kwargs, message in [
            ({"email": "customer@example.com"}, "Email đã tồn tại"),
            ({"username": "customer"}, "Tên đăng nhập đã tồn tại"),
            ({"phone_num": "0900000002"}, "Số điện thoại đã tồn tại"),
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, message):
                UserService.check_duplicate(**kwargs)

        user = UserService.register(
            " NEW@example.com ", " newuser ", "password1", "password1",
            " New User ", "0912345678", " Hà Nội ",
        )
        self.assertEqual(user.email, "NEW@example.com")
        self.assertIsNotNone(user.wallet)
        self.assertEqual(user.profile.full_name, "New User")

    def test_register_validations(self):
        base = ["a@b.com", "newname", "password1", "password1", "Name", "0912345678", "HCM"]
        cases = [
            (["", *base[1:]], "Thông tin không được để trống"),
            (["bad", *base[1:]], "Email không hợp lệ"),
            ([*base[:5], "123", base[6]], "Số điện thoại không hợp lệ"),
            ([base[0], base[1], "short", "short", *base[4:]], "Mật khẩu phải có ít nhất 8 ký tự"),
            ([base[0], base[1], base[2], "different1", *base[4:]], "Mật khẩu xác nhận không khớp"),
        ]
        for args, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                UserService.register(*args)

    def test_login_password_and_profile(self):
        user = UserService.login("customer", "customer123")
        self.assertEqual(user.user_id, self.seed["customer"].user_id)
        for login, password in [("", "x"), ("customer", "wrong"), ("missing", "customer123")]:
            with self.subTest(login=login), self.assertRaises(ValueError):
                UserService.login(login, password)

        UserService.change_password(user.user_id, "customer123", "newpass123")
        self.assertEqual(UserService.login("customer", "newpass123").user_id, user.user_id)

        profile = UserService.update_profile(
            user.user_id,
            {"full_name": " Updated ", "phone_num": "0987654321", "address": " Hà Nội ", "avatar": " avatar.png "},
        )
        self.assertEqual(profile.full_name, "Updated")
        self.assertEqual(profile.avatar, "avatar.png")

    def test_user_error_paths_and_admin_queries(self):
        with self.assertRaisesRegex(ValueError, "User không tồn tại"):
            UserService.get_user_by_id(999)
        self.seed["other"].active = False
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "User không tồn tại"):
            UserService.get_user_by_id(self.seed["other"].user_id, active=True)
        self.assertGreaterEqual(len(UserService.get_all_users()), 3)
        self.assertGreaterEqual(len(UserService.get_all_users_admin()), 3)
        self.assertEqual(UserService.get_user_detail_admin(self.seed["customer"].user_id).username, "customer")
        with self.assertRaises(ValueError):
            UserService.get_user_detail_admin(999)
        with self.assertRaisesRegex(ValueError, "Quản trị viên"):
            UserService.toggle_user_status(self.seed["admin"].user_id, False)
        result = UserService.toggle_user_status(self.seed["customer"].user_id, False)
        self.assertFalse(result.active)

    def test_social_login_existing_and_new(self):
        new = UserService.social_login("GOOGLE", "google-1", email="g@example.com", full_name="Google User")
        self.assertEqual(new.provider, "GOOGLE")
        self.assertEqual(UserService.social_login("GOOGLE", "google-1"), new)
        with self.assertRaisesRegex(ValueError, "Nhà cung cấp"):
            UserService.social_login("GITHUB", "1")
        with self.assertRaisesRegex(ValueError, "Không lấy được thông tin"):
            UserService.social_login("GOOGLE", None)
        with self.assertRaisesRegex(ValueError, "Email này đã được sử dụng"):
            UserService.social_login("GOOGLE", "google-2", email="customer@example.com")

    def test_remaining_user_service_branches(self):
        customer = self.seed["customer"]
        UserService.check_duplicate(
            email=customer.email,
            username=customer.username,
            phone_num=customer.profile.phone_num,
            exclude_user_id=customer.user_id,
        )
        self.assertEqual(len(UserService.get_all_users(active=True)), 3)

        generated = UserService.social_login(
            "FACEBOOK", "fb-no-email", username="customer", full_name=None
        )
        self.assertTrue(generated.email.endswith("@social.verdia.local"))
        self.assertNotEqual(generated.username, "customer")
        with self.assertRaisesRegex(ValueError, "bên thứ ba"):
            UserService.change_password(generated.user_id, "old", "newpass1")
        generated.active = False
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "bị khóa"):
            UserService.social_login("FACEBOOK", "fb-no-email")

        with self.assertRaisesRegex(ValueError, "User không tồn tại"):
            UserService.change_password(999, "old", "newpass1")
        for old, new in [(None, "newpass1"), ("customer123", "short"), ("customer123", "customer123")]:
            with self.subTest(old=old, new=new), self.assertRaises(ValueError):
                UserService.change_password(customer.user_id, old, new)

        with self.assertRaisesRegex(ValueError, "Profile không tồn tại"):
            UserService.update_profile(999, {})
        with self.assertRaisesRegex(ValueError, "Số điện thoại không hợp lệ"):
            UserService.update_profile(customer.user_id, {"phone_num": "123"})
        self.assertIsNone(UserService.update_profile(customer.user_id, {"avatar": None}).avatar)

        other_id = self.seed["other"].user_id
        self.assertFalse(UserService.delete_user(other_id).active)
        with self.assertRaises(ValueError):
            UserService.delete_user(other_id)
        self.assertFalse(UserService.lock_user(customer.user_id).active)
        with self.assertRaises(ValueError):
            UserService.lock_user(customer.user_id)
        with self.assertRaisesRegex(ValueError, "Người dùng không tồn tại"):
            UserService.toggle_user_status(999, True)


class ProductServiceTests(DatabaseTestCase, unittest.TestCase):
    def test_create_update_delete_product_and_tags(self):
        product = ProductService.create_product(" New Product ", "123000", " Desc ", " x.jpg ", "IN_STOCK", [self.seed["tag"].tag_id])
        self.assertEqual(product.product_name, "New Product")
        self.assertEqual(ProductTag.query.filter_by(product_id=product.product_id).count(), 1)
        updated = ProductService.update_product(product.product_id, {"product_name": "Renamed", "price": "130000", "description": "New", "image": "n.jpg", "status": "PREORDER"}, [])
        self.assertEqual(updated.status, "PREORDER")
        self.assertEqual(ProductTag.query.filter_by(product_id=product.product_id).count(), 0)
        self.assertFalse(ProductService.delete_product(product.product_id).active)

        tag = ProductService.create_tag(" New Tag ", self.seed["sub_category"].sub_category_id)
        self.assertEqual(tag.name, "New Tag")
        self.assertTrue(ProductService.get_all_tags())
        self.assertTrue(ProductService.get_categories())
        self.assertTrue(ProductService.get_sub_categories(self.seed["category"].category_id))
        self.assertTrue(ProductService.get_tags_by_sub_category(self.seed["sub_category"].sub_category_id))

    def test_product_filters_and_errors(self):
        results = ProductService.get_all_products(keyword="Áo", status="IN_STOCK", min_price=0, max_price=150000, tag_ids=[self.seed["tag"].tag_id], category_id=self.seed["category"].category_id, sub_category_id=self.seed["sub_category"].sub_category_id)
        self.assertEqual([p.product_id for p in results], [self.seed["stock_product"].product_id])
        cases = [
            (("", 1, "d", "i", "IN_STOCK"), "không được để trống"),
            (("X", "bad", "d", "i", "IN_STOCK"), "Giá sản phẩm không hợp lệ"),
            (("X", -1, "d", "i", "IN_STOCK"), "phải lớn hơn 0"),
            (("X", 1, "d", "i", "BAD"), "Trạng thái sản phẩm"),
        ]
        for args, msg in cases:
            with self.subTest(msg=msg), self.assertRaisesRegex(ValueError, msg):
                ProductService.create_product(*args)
        for kwargs in [{"status": "BAD"}, {"min_price": "bad"}, {"max_price": -1}, {"min_price": 10, "max_price": 1}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ProductService.get_all_products(**kwargs)
        with self.assertRaises(ValueError):
            ProductService.get_product_by_id(999)
        with self.assertRaises(ValueError):
            ProductService.create_tag("", self.seed["sub_category"].sub_category_id)
        with self.assertRaises(ValueError):
            ProductService.create_tag("X", 999)

    def test_remaining_product_service_validations(self):
        tag_id = self.seed["tag"].tag_id
        other_tag_id = self.seed["other_tag"].tag_id
        with self.assertRaisesRegex(ValueError, "Tên sản phẩm đã tồn tại"):
            ProductService.create_product("Áo có sẵn", 1, "d", "i", "IN_STOCK")
        with self.assertRaisesRegex(ValueError, "Thẻ không tồn tại"):
            ProductService.create_product("Bad tag", 1, "d", "i", "IN_STOCK", [999])
        with self.assertRaisesRegex(ValueError, "cùng một danh mục phụ"):
            ProductService.create_product("Mixed tags", 1, "d", "i", "IN_STOCK", [tag_id, other_tag_id])

        for kwargs in [
            {"category_id": 999},
            {"sub_category_id": 999},
            {"tag_ids": [999]},
            {"category_id": self.seed["category"].category_id, "sub_category_id": self.seed["other_sub"].sub_category_id, "tag_ids": [tag_id]},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ProductService.get_all_products(**kwargs)

        product = self.seed["spare_product"]
        for data, tags in [
            ({"product_name": "Áo có sẵn"}, None),
            ({"price": "bad"}, None),
            ({"price": 0}, None),
            ({"status": "BAD"}, None),
            ({}, [999]),
            ({}, [tag_id, other_tag_id]),
        ]:
            with self.subTest(data=data, tags=tags), self.assertRaises(ValueError):
                ProductService.update_product(product.product_id, data, tags)
        with self.assertRaises(ValueError):
            ProductService.update_product(999, {}, None)
        with self.assertRaisesRegex(ValueError, "đã tồn tại"):
            ProductService.create_tag("Oversize", self.seed["sub_category"].sub_category_id)


class PreOrderServiceTests(DatabaseTestCase, unittest.TestCase):
    def test_create_query_update_progress_delete(self):
        product = self.seed["spare_product"]
        preorder = PreOrderService.create_preorder(product.product_id, date.today(), date.today() + timedelta(days=5), " Open ")
        self.assertEqual(preorder.progress_status, "MỞ PREORDER")
        self.assertIn(preorder, PreOrderService.get_all_preorders(keyword="phụ", min_price=0, max_price=100000))
        updated = PreOrderService.update_preorder(preorder.preorder_id, {"end_date": date.today() + timedelta(days=10), "progress_note": " Updated ", "active": False})
        self.assertFalse(updated.active)
        updated = PreOrderService.update_preorder(preorder.preorder_id, {"active": True})
        self.assertTrue(updated.active)
        progressed = PreOrderService.update_progress(preorder.preorder_id, "HOÀN THÀNH", " Done ")
        self.assertFalse(progressed.active)
        progressed.active = True
        db.session.commit()
        self.assertFalse(PreOrderService.delete_preorder(preorder.preorder_id).active)

    def test_preorder_validations(self):
        product_id = self.seed["spare_product"].product_id
        cases = [
            ((None, date.today(), date.today(), "x"), "không được để trống"),
            ((product_id, date.today(), date.today(), " "), "Ghi chú"),
            ((999, date.today(), date.today(), "x"), "Sản phẩm không tồn tại"),
            ((product_id, date.today() + timedelta(days=1), date.today(), "x"), "Ngày bắt đầu"),
        ]
        for args, msg in cases:
            with self.subTest(msg=msg), self.assertRaisesRegex(ValueError, msg):
                PreOrderService.create_preorder(*args)
        with self.assertRaisesRegex(ValueError, "đang có đợt preorder"):
            PreOrderService.create_preorder(self.seed["preorder_product"].product_id, date.today(), date.today(), "x")
        for kwargs in [{"min_price": "bad"}, {"max_price": -1}, {"min_price": 2, "max_price": 1}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                PreOrderService.get_all_preorders(**kwargs)
        with self.assertRaises(ValueError):
            PreOrderService.get_preorder_by_id(999)
        with self.assertRaises(ValueError):
            PreOrderService.update_progress(self.seed["preorder"].preorder_id, "BAD", "x")
        with self.assertRaises(ValueError):
            PreOrderService.update_progress(self.seed["preorder"].preorder_id, "ĐANG SẢN XUẤT", " ")

    def test_remaining_preorder_service_branches(self):
        self.assertTrue(
            PreOrderService.get_all_preorders(tag_ids=[self.seed["tag"].tag_id])
        )
        with self.assertRaises(ValueError):
            PreOrderService.get_all_preorders(max_price="bad")
        self.seed["preorder"].active = False
        db.session.commit()
        with self.assertRaises(ValueError):
            PreOrderService.get_preorder_by_id(self.seed["preorder"].preorder_id, active=True)

        spare = PreOrderService.create_preorder(
            self.seed["spare_product"].product_id,
            date.today(),
            date.today() + timedelta(days=2),
            "spare",
        )
        with self.assertRaisesRegex(ValueError, "Ngày bắt đầu"):
            PreOrderService.update_preorder(
                spare.preorder_id,
                {"start_date": date.today() + timedelta(days=5)},
            )
        db.session.rollback()
        with self.assertRaisesRegex(ValueError, "Ghi chú"):
            PreOrderService.update_preorder(spare.preorder_id, {"progress_note": " "})
        with self.assertRaisesRegex(ValueError, "active"):
            PreOrderService.update_preorder(spare.preorder_id, {"active": "yes"})
        PreOrderService.update_progress(spare.preorder_id, "HOÀN THÀNH", "done")
        reopened = PreOrderService.update_preorder(spare.preorder_id, {"active": True})
        self.assertEqual(reopened.progress_status, "MỞ PREORDER")


if __name__ == "__main__":
    unittest.main()
