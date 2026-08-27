from config import db
from decimal import Decimal, InvalidOperation
from sqlalchemy import select
from modules.inventories.models import Inventory, InventoryTransaction
from modules.products.models import Product


class InventoryService:

    @staticmethod
    def get_all_inventory(keyword=None, status=None, active=True):
        stmt = select(Inventory).join(
            Product, Inventory.product_id == Product.product_id
        )

        # Lọc active
        if active is not None:
            stmt = stmt.where(Inventory.active == active)

        # Tìm theo tên sản phẩm
        if keyword and keyword.strip():
            keyword = keyword.strip()

            stmt = stmt.where(Product.product_name.ilike(f"%{keyword}%"))

        inventories = db.session.scalars(stmt).all()

        # Lọc theo trạng thái tồn kho
        if status:
            valid_statuses = ["CÒN HÀNG", "SẮP HẾT HÀNG", "HẾT HÀNG"]

            if status not in valid_statuses:
                raise ValueError("Trạng thái tồn kho không hợp lệ")

            inventories = [
                inventory for inventory in inventories if inventory.status == status
            ]

        return inventories

    @staticmethod
    def get_inventory_by_product(product_id):
        stmt = select(Inventory).where(
            Inventory.product_id == product_id, Inventory.active.is_(True)
        )

        inventory = db.session.scalar(stmt)

        if not inventory:
            raise ValueError("Sản phẩm chưa có tồn kho")

        return inventory

    @staticmethod
    def create_inventory(product_id, quantity, price):
        product = db.session.get(Product, product_id)

        if not product or not product.active:
            raise ValueError("Sản phẩm không tồn tại")

        # Kiểm tra sản phẩm đã có tồn kho chưa
        stmt = select(Inventory).where(Inventory.product_id == product_id)

        existing_inventory = db.session.scalar(stmt)

        if existing_inventory:
            raise ValueError("Sản phẩm đã có tồn kho")

        # Kiểm tra số lượng
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Số lượng không hợp lệ")

        if quantity < 0:
            raise ValueError("Số lượng không được nhỏ hơn 0")

        # Kiểm tra giá nhập
        try:
            price = Decimal(str(price))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Giá nhập không hợp lệ")

        if not price.is_finite() or price <= 0:
            raise ValueError("Giá nhập phải lớn hơn 0")

        inventory = Inventory(product_id=product_id, quantity=quantity, price=price)

        try:
            db.session.add(inventory)
            db.session.flush()

            if quantity > 0:
                transaction = InventoryTransaction(
                    inventory_id=inventory.inventory_id,
                    transaction_type="NHẬP",
                    quantity=quantity,
                    price=price,
                )

                db.session.add(transaction)

            db.session.commit()

            return inventory

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def import_stock(product_id, quantity, price):
        inventory = InventoryService.get_inventory_by_product(product_id)

        # Kiểm tra số lượng nhập
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Số lượng nhập không hợp lệ")

        if quantity <= 0:
            raise ValueError("Số lượng nhập phải lớn hơn 0")

        # Kiểm tra giá nhập
        try:
            price = Decimal(str(price))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Giá nhập không hợp lệ")

        if not price.is_finite() or price <= 0:
            raise ValueError("Giá nhập phải lớn hơn 0")

        old_quantity = inventory.quantity
        old_price = inventory.price

        new_quantity = old_quantity + quantity

        new_price = ((old_quantity * old_price) + (quantity * price)) / new_quantity

        inventory.quantity = new_quantity
        inventory.price = new_price

        try:
            transaction = InventoryTransaction(
                inventory_id=inventory.inventory_id,
                transaction_type="NHẬP",
                quantity=quantity,
                price=price,
            )

            db.session.add(transaction)

            db.session.commit()

            return inventory

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def export_stock(product_id, quantity):
        inventory = InventoryService.get_inventory_by_product(product_id)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Số lượng xuất không hợp lệ")

        if quantity <= 0:
            raise ValueError("Số lượng xuất phải lớn hơn 0")

        if inventory.quantity < quantity:
            raise ValueError("Số lượng tồn kho không đủ")

        inventory.quantity -= quantity

        try:
            transaction = InventoryTransaction(
                inventory_id=inventory.inventory_id,
                transaction_type="XUẤT",
                quantity=quantity,
                price=None,
            )

            db.session.add(transaction)

            db.session.commit()

            return inventory

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_stock(product_id, quantity):
        inventory = InventoryService.get_inventory_by_product(product_id)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Số lượng không hợp lệ")

        if quantity < 0:
            raise ValueError("Số lượng không được nhỏ hơn 0")

        # Lưu số lượng cũ để tính chênh lệch
        old_quantity = inventory.quantity

        # Cập nhật số lượng mới
        inventory.quantity = quantity

        # Tính số lượng điều chỉnh
        difference = quantity - old_quantity

        try:
            # Chỉ ghi lịch sử nếu số lượng thật sự thay đổi
            if difference != 0:
                transaction = InventoryTransaction(
                    inventory_id=inventory.inventory_id,
                    transaction_type="ĐIỀU CHỈNH",
                    quantity=difference,
                    price=None,
                )

                db.session.add(transaction)

            db.session.commit()

            return inventory

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_inventory_status(product_id):
        inventory = InventoryService.get_inventory_by_product(product_id)

        return inventory.status

    @staticmethod
    def restore_stock(product_id, quantity):
        inventory = InventoryService.get_inventory_by_product(product_id)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            raise ValueError("Số lượng hoàn kho không hợp lệ")

        if quantity <= 0:
            raise ValueError("Số lượng hoàn kho phải lớn hơn 0")

        inventory.quantity += quantity

        try:
            transaction = InventoryTransaction(
                inventory_id=inventory.inventory_id,
                transaction_type="HOÀN KHO",
                quantity=quantity,
                price=None,
            )

            db.session.add(transaction)

            db.session.commit()

            return inventory

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_inventory_transactions(product_id=None, transaction_type=None):
        stmt = select(InventoryTransaction).join(
            Inventory, InventoryTransaction.inventory_id == Inventory.inventory_id
        )

        if product_id is not None:
            stmt = stmt.where(Inventory.product_id == product_id)

        if transaction_type:
            valid_types = ["NHẬP", "XUẤT", "ĐIỀU CHỈNH", "HOÀN KHO"]

            if transaction_type not in valid_types:
                raise ValueError("Loại giao dịch tồn kho không hợp lệ")

            stmt = stmt.where(InventoryTransaction.transaction_type == transaction_type)

        return db.session.scalars(stmt).all()
