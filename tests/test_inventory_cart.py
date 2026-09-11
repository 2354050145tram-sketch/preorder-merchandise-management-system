import unittest
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from config import db
from modules.carts.models import CartItem
from modules.carts.services import CartService
from modules.inventories.models import Inventory, InventoryTransaction
from modules.inventories.services import InventoryService
from modules.products.models import Product
from tests.support import DatabaseTestCase


class InventoryServiceTests(DatabaseTestCase, unittest.TestCase):
    def test_full_inventory_lifecycle(self):
        spare_id = self.seed["spare_product"].product_id
        inventory = InventoryService.create_inventory(spare_id, 5, "40000")
        self.assertEqual(inventory.status, "SẮP HẾT HÀNG")
        self.assertEqual(InventoryTransaction.query.count(), 1)
        inventory = InventoryService.import_stock(spare_id, 5, "60000")
        self.assertEqual(inventory.quantity, 10)
        self.assertEqual(inventory.price, Decimal("50000"))
        inventory = InventoryService.export_stock(spare_id, 3)
        self.assertEqual(inventory.quantity, 7)
        inventory = InventoryService.update_stock(spare_id, 2)
        self.assertEqual(inventory.status, "SẮP HẾT HÀNG")
        inventory = InventoryService.restore_stock(spare_id, 4)
        self.assertEqual(inventory.quantity, 6)
        self.assertEqual(InventoryService.get_inventory_status(spare_id), "CÒN HÀNG")
        self.assertEqual(len(InventoryService.get_inventory_transactions(product_id=spare_id)), 5)
        self.assertEqual(len(InventoryService.get_inventory_transactions(transaction_type="NHẬP")), 2)

    def test_inventory_queries_and_status_filter(self):
        all_items = InventoryService.get_all_inventory(keyword="Áo", active=True)
        self.assertEqual(len(all_items), 1)
        stock = self.seed["stock_product"].inventories[0]
        stock.quantity = 0
        db.session.commit()
        self.assertEqual(InventoryService.get_all_inventory(status="HẾT HÀNG")[0].status, "HẾT HÀNG")
        stock.quantity = 4
        db.session.commit()
        self.assertEqual(InventoryService.get_all_inventory(status="SẮP HẾT HÀNG")[0].status, "SẮP HẾT HÀNG")
        with self.assertRaisesRegex(ValueError, "Trạng thái tồn kho"):
            InventoryService.get_all_inventory(status="BAD")

    def test_create_inventory_validations(self):
        spare_id = self.seed["spare_product"].product_id
        cases = [
            ((999, 1, 1), "Sản phẩm không tồn tại"),
            ((self.seed["stock_product"].product_id, 1, 1), "đã có tồn kho"),
            ((spare_id, "x", 1), "Số lượng không hợp lệ"),
            ((spare_id, -1, 1), "không được nhỏ hơn 0"),
            ((spare_id, 1, "x"), "Giá nhập không hợp lệ"),
            ((spare_id, 1, 0), "Giá nhập phải lớn hơn 0"),
        ]
        for args, msg in cases:
            with self.subTest(msg=msg), self.assertRaisesRegex(ValueError, msg):
                InventoryService.create_inventory(*args)
        with self.assertRaisesRegex(ValueError, "chưa có tồn kho"):
            InventoryService.get_inventory_by_product(spare_id)

    def test_import_export_update_restore_validations(self):
        pid = self.seed["stock_product"].product_id
        calls = [
            (InventoryService.import_stock, (pid, "x", 1)),
            (InventoryService.import_stock, (pid, 0, 1)),
            (InventoryService.import_stock, (pid, 1, "bad")),
            (InventoryService.import_stock, (pid, 1, 0)),
            (InventoryService.export_stock, (pid, "x")),
            (InventoryService.export_stock, (pid, 0)),
            (InventoryService.export_stock, (pid, 999)),
            (InventoryService.update_stock, (pid, "x")),
            (InventoryService.update_stock, (pid, -1)),
            (InventoryService.restore_stock, (pid, "x")),
            (InventoryService.restore_stock, (pid, 0)),
        ]
        for fn, args in calls:
            with self.subTest(fn=fn.__name__, args=args), self.assertRaises(ValueError):
                fn(*args)
        with self.assertRaises(ValueError):
            InventoryService.get_inventory_transactions(transaction_type="BAD")

    def test_create_zero_inventory_and_noop_adjustment(self):
        inventory = InventoryService.create_inventory(self.seed["spare_product"].product_id, 0, 100)
        self.assertEqual(inventory.status, "HẾT HÀNG")
        self.assertEqual(InventoryTransaction.query.filter_by(inventory_id=inventory.inventory_id).count(), 0)
        InventoryService.update_stock(self.seed["spare_product"].product_id, 0)
        self.assertEqual(InventoryTransaction.query.filter_by(inventory_id=inventory.inventory_id).count(), 0)


class CartServiceTests(DatabaseTestCase, unittest.TestCase):
    def test_cart_stock_and_preorder_lifecycle(self):
        uid = self.seed["customer"].user_id
        cart = CartService.get_or_create_cart(uid)
        self.assertEqual(CartService.get_or_create_cart(uid).cart_id, cart.cart_id)
        stock_item = CartService.add_item(uid, self.seed["stock_product"].product_id, 2)
        self.assertIsNone(stock_item.preorder_id)
        stock_item = CartService.add_item(uid, self.seed["stock_product"].product_id, 1)
        self.assertEqual(stock_item.quantity, 3)
        preorder_item = CartService.add_item(uid, self.seed["preorder_product"].product_id, 2)
        self.assertEqual(preorder_item.preorder_id, self.seed["preorder"].preorder_id)
        self.assertEqual(CartService.update_quantity(uid, stock_item.cart_item_id, 4).quantity, 4)
        self.assertEqual(CartService.update_quantity(uid, preorder_item.cart_item_id, 3).quantity, 3)
        CartService.remove_item(uid, stock_item.cart_item_id)
        self.assertIsNone(db.session.get(CartItem, stock_item.cart_item_id))
        CartService.clear_cart(uid)
        self.assertEqual(len(CartService.get_cart(uid).items), 0)

    def test_add_item_validation_paths(self):
        uid = self.seed["customer"].user_id
        stock_id = self.seed["stock_product"].product_id
        preorder_id = self.seed["preorder_product"].product_id
        for product_id, qty in [(999, 1), (stock_id, "x"), (stock_id, 0), (stock_id, 999)]:
            with self.subTest(product=product_id, qty=qty), self.assertRaises(ValueError):
                CartService.add_item(uid, product_id, qty)
        inventory = self.seed["stock_product"].inventories[0]
        inventory.quantity = 0
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "hết hàng"):
            CartService.add_item(uid, stock_id, 1)

        self.seed["preorder"].active = False
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "không có đợt preorder"):
            CartService.add_item(uid, preorder_id, 1)
        self.seed["preorder"].active = True
        self.seed["preorder"].start_date = date.today() + timedelta(days=2)
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "hiện không mở"):
            CartService.add_item(uid, preorder_id, 1)

    def test_update_and_remove_validation_paths(self):
        uid = self.seed["customer"].user_id
        item = CartService.add_item(uid, self.seed["stock_product"].product_id, 1)
        other_uid = self.seed["other"].user_id
        CartService.get_or_create_cart(other_uid)
        for target_uid, item_id, qty in [(other_uid, item.cart_item_id, 1), (uid, item.cart_item_id, "x"), (uid, item.cart_item_id, 0), (uid, item.cart_item_id, 999)]:
            with self.subTest(uid=target_uid, qty=qty), self.assertRaises(ValueError):
                CartService.update_quantity(target_uid, item_id, qty)
        with self.assertRaises(ValueError):
            CartService.remove_item(other_uid, item.cart_item_id)

    def test_preorder_update_closed_and_invalid_product_status(self):
        uid = self.seed["customer"].user_id
        item = CartService.add_item(uid, self.seed["preorder_product"].product_id, 1)
        self.seed["preorder"].active = False
        db.session.commit()
        with self.assertRaisesRegex(ValueError, "đã đóng"):
            CartService.update_quantity(uid, item.cart_item_id, 2)
        bad = SimpleNamespace(product_id=999, active=True, status="BAD")
        with patch.object(db.session, "get", return_value=bad):
            with self.assertRaisesRegex(ValueError, "Trạng thái sản phẩm"):
                CartService.add_item(uid, 999, 1)


if __name__ == "__main__":
    unittest.main()
