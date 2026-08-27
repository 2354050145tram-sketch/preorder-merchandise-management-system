from config import db
from sqlalchemy import select
from decimal import Decimal, InvalidOperation
from modules.preorders.models import PreOrder
from modules.products.models import Product, ProductTag
from modules.notifications.services import NotificationService


class PreOrderService:

    @staticmethod
    def create_preorder(product_id, start_date, end_date, progress_note):
        if not all([product_id, start_date, end_date, progress_note]):
            raise ValueError("Thông tin sản phẩm không được để trống")

        progress_note = progress_note.strip()

        if not progress_note:
            raise ValueError("Ghi chú tiến độ không được để trống")

        # Kiểm tra sản phẩm
        product = db.session.get(Product, product_id)

        if not product or not product.active:
            raise ValueError("Sản phẩm không tồn tại")

        # Kiểm tra sản phẩm được mở đợt preorder
        if product.status not in ["PREORDER", "IN_STOCK"]:
            raise ValueError("Sản phẩm không hợp lệ để mở preorder")

        # Kiểm tra ngày mở preorder
        if start_date > end_date:
            raise ValueError("Ngày bắt đầu hoặc kết thúc không hợp lệ")

        # Kiểm tra sản phẩm có preorder đang hoạt động chưa
        stmt = select(PreOrder).where(
            PreOrder.product_id == product_id, PreOrder.active.is_(True)
        )

        existing_preorder = db.session.scalar(stmt)

        if existing_preorder:
            raise ValueError("Sản phẩm đang có đợt preorder")

        # Tạo preorder
        preorder = PreOrder(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            quantity_order=0,
            progress_status="MỞ PREORDER",
            progress_note=progress_note,
        )

        try:
            db.session.add(preorder)
            db.session.commit()

            return preorder

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all_preorders(
        keyword=None, tag_ids=None, min_price=None, max_price=None, active=True
    ):
        stmt = select(PreOrder).join(Product, PreOrder.product_id == Product.product_id)

        # Lọc active
        if active is not None:
            stmt = stmt.where(PreOrder.active == active)

        # Tìm kiếm theo tên sản phẩm
        if keyword and keyword.strip():
            keyword = keyword.strip()

            stmt = stmt.where(Product.product_name.ilike(f"%{keyword}%"))

        if min_price is not None:
            try:
                min_price = Decimal(str(min_price))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError("Giá tối thiểu không hợp lệ")

            if not min_price.is_finite() or min_price < 0:
                raise ValueError("Giá tối thiểu không hợp lệ")

        if max_price is not None:
            try:
                max_price = Decimal(str(max_price))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError("Giá tối đa không hợp lệ")

            if not max_price.is_finite() or max_price < 0:
                raise ValueError("Giá tối đa không hợp lệ")

        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValueError("Khoảng giá không hợp lệ")

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        # Lọc theo thẻ
        if tag_ids:
            stmt = stmt.join(
                ProductTag, Product.product_id == ProductTag.product_id
            ).where(ProductTag.tag_id.in_(tag_ids))

        return db.session.scalars(stmt).unique().all()

    @staticmethod
    def get_preorder_by_id(preorder_id, active=None):
        preorder = db.session.get(PreOrder, preorder_id)

        if not preorder:
            raise ValueError("Preorder không tồn tại")

        if active is not None and preorder.active != active:
            raise ValueError("Preorder không tồn tại")

        return preorder

    @staticmethod
    def update_preorder(preorder_id, data):
        preorder = PreOrderService.get_preorder_by_id(preorder_id)

        # Cập nhật ngày bắt đầu
        if "start_date" in data and data["start_date"]:
            preorder.start_date = data["start_date"]

        # Cập nhật ngày kết thúc
        if "end_date" in data and data["end_date"]:
            preorder.end_date = data["end_date"]

        # Kiểm tra lại ngày
        if preorder.start_date > preorder.end_date:
            raise ValueError("Ngày bắt đầu hoặc kết thúc không hợp lệ")

        # Cập nhật ghi chú
        if "progress_note" in data:
            progress_note = (
                data["progress_note"].strip() if data["progress_note"] else ""
            )

            if not progress_note:
                raise ValueError("Ghi chú tiến độ không được để trống")

            preorder.progress_note = progress_note

        # Mở / đóng preorder
        if "active" in data:
            new_active = data["active"]

            if not isinstance(new_active, bool):
                raise ValueError("Trạng thái active không hợp lệ")

            if new_active and not preorder.active:
                stmt = select(PreOrder).where(
                    PreOrder.product_id == preorder.product_id,
                    PreOrder.preorder_id != preorder.preorder_id,
                    PreOrder.active.is_(True),
                )

                existing_preorder = db.session.scalar(stmt)

                if existing_preorder:
                    raise ValueError("Sản phẩm đang có đợt preorder khác")

                if preorder.progress_status == "HOÀN THÀNH":
                    preorder.progress_status = "MỞ PREORDER"

            preorder.active = new_active

        try:
            db.session.commit()

            return preorder

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_progress(preorder_id, progress_status, progress_note=None):
        preorder = PreOrderService.get_preorder_by_id(preorder_id, active=True)

        valid_statuses = [
            "MỞ PREORDER",
            "ĐÃ ĐẶT HÀNG",
            "ĐANG SẢN XUẤT",
            "ĐÃ VỀ KHO TRUNG QUỐC",
            "ĐÃ VỀ KHO VIỆT NAM",
            "ĐANG GÓI HÀNG",
            "ĐÃ VẬN CHUYỂN",
            "HOÀN THÀNH",
        ]

        if progress_status not in valid_statuses:
            raise ValueError("Tiến độ không hợp lệ")

        if preorder.progress_status == progress_status:
            raise ValueError("Preorder đã ở tiến độ này")

        current_index = valid_statuses.index(preorder.progress_status)

        new_index = valid_statuses.index(progress_status)

        if new_index < current_index:
            raise ValueError("Không thể cập nhật lùi tiến độ preorder")

        preorder.progress_status = progress_status

        if progress_note:
            progress_note = progress_note.strip()

            if progress_note:
                preorder.progress_note = progress_note

        # Hoàn thành thì tự đóng preorder
        if progress_status == "HOÀN THÀNH":
            preorder.active = False

        try:
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        try:
            NotificationService.send_preorder_notification(
                preorder_id=preorder.preorder_id,
                title="Cập nhật preorder",
                message=(
                    f"Tiến độ preorder đã được cập nhật: " f"{preorder.progress_status}"
                ),
            )
        except Exception as error:
            print(f"Không thể gửi thông báo preorder: " f"{error}")

        return preorder

    @staticmethod
    def delete_preorder(preorder_id):
        preorder = PreOrderService.get_preorder_by_id(preorder_id, active=True)

        preorder.active = False

        try:
            db.session.commit()
            return preorder

        except Exception:
            db.session.rollback()
            raise
