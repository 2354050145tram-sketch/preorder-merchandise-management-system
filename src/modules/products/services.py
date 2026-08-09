from config import db
from decimal import Decimal, InvalidOperation
from sqlalchemy import select, delete
from modules.products.models import Product, Tag, ProductTag

class ProductService:

    @staticmethod
    def create_product(product_name, price, description, image, status, tag_ids = None):
        product_name = product_name.strip()
        description = description.strip()
        image = image.strip()

        # Kiểm tra dữ liệu bắt buộc
        if not all([product_name, price, description, image, status]):
            raise ValueError("Thông tin sản phẩm không được để trống")

        # Kiểm tra giá
        try:
            price = Decimal(str(price))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Giá sản phẩm không hợp lệ")

        if not price.is_finite() or price <=0:
            raise ValueError("Giá sản phẩm phải lớn hơn 0")

        # Kiểm tra status
        if status not in ["PREORDER", "IN_STOCK"]:
            raise ValueError("Trạng thái sản phẩm không hợp lệ")

        # Kiểm tra tên sản phẩm trùng
        stmt = select(Product).where(
            Product.product_name == product_name
        )

        existing_product = db.session.scalar(stmt)

        if existing_product:
            raise ValueError("Tên sản phẩm đã tồn tại")

        # Kiểm tra Tag
        tags = []

        if tag_ids:
            tag_ids = list(set(tag_ids))

            stmt = select(Tag).where(
                Tag.tag_id.in_(tag_ids),
                Tag.active.is_(True)
            )

            tags = db.session.scalars(stmt).all()

            if len(tags) != len(tag_ids):
                raise ValueError("Thẻ không tồn tại")

        # Tạo product
        product = Product(
            product_name = product_name,
            price = price,
            description = description,
            image = image,
            status = status
        )
        try:
            db.session.add(product)
            db.session.flush()

            # Tạo dữ liệu bảng trung gian ProductTag
            for tag in tags:
                product_tag = ProductTag(
                    product_id = product.product_id,
                    tag_id = tag.tag_id
                )

                db.session.add(product_tag)

            db.session.commit()

            return product

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all_products(keyword=None, status=None, tag_ids=None, min_price=None, max_price=None, active=True):
        stmt = select(Product)

        # Active
        if active is not None:
            stmt = stmt.where(
                Product.active == active
            )

        # Tìm kiếm theo tên
        if keyword and keyword.strip():
            keyword = keyword.strip()

            stmt = stmt.where(Product.product_name.ilike(f"%{keyword}%"))

        # Lọc theo trạng thái
        if status:
            if status not in ["PREORDER", "IN_STOCK"]:
                raise ValueError("Trạng thái sản phẩm không hợp lệ")

            stmt = stmt.where(Product.status == status)

        # Lọc theo giá tiền
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price) 

        # Lọc theo thẻ
        if tag_ids:
            stmt = (stmt.join(ProductTag, Product.product_id == ProductTag.product_id).where(ProductTag.tag_id.in_(tag_ids)))

        return (db.session.scalars(stmt).unique().all())

    @staticmethod
    def get_product_by_id(product_id):
        product = db.session.get(Product, product_id)

        if not product or not product.active:
            raise ValueError("Sản phẩm không tồn tại")

        return product

    @staticmethod
    def update_product(product_id, data, tag_ids=None):

        product = ProductService.get_product_by_id(product_id)

        # Cập nhật tên sản phẩm
        if "product_name" in data and data["product_name"]:
            product_name = data["product_name"].strip()

            if product_name and product_name != product.product_name:
                stmt = select(Product).where(
                    Product.product_name == product_name,
                    Product.product_id != product_id
                )

                existing_product = (db.session.scalar(stmt))

                if existing_product:
                    raise ValueError("Tên sản phẩm đã tồn tại")

                product.product_name = product_name

        # Cập nhật giá sản phẩm
        if "price" in data and data["price"] not in [None, ""]:
            try:
                price = Decimal(str(data["price"]))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError("Giá sản phẩm không hợp lệ")

            if not price.is_finite() or price <= 0:
                raise ValueError("Giá sản phẩm phải lớn hơn 0")

            product.price = price

        # Cập nhật mô tả sản phẩm
        if "description" in data and data["description"]:
            description = data["description"].strip()

            if description:
                product.description = description

        # Cập nhật hình ảnh sản phẩm
        if "image" in data and data["image"]:
            image = data["image"].strip()

            if image:
                product.image = image

        # Cập nhật trạng thái sản phẩm
        if "status" in data and data["status"]:
            if data["status"] not in ["PREORDER", "IN_STOCK"]:
                raise ValueError("Trạng thái sản phẩm không hợp lệ")

            product.status = data["status"]

        # Kiểm tra thẻ mới
        tags = None

        if tag_ids is not None:
            tag_ids = list(set(tag_ids))

            if tag_ids:
                stmt = select(Tag).where(
                    Tag.tag_id.in_(tag_ids),
                    Tag.active.is_(True)
                )

                tags = (db.session.scalars(stmt).all())

                if len(tags) != len(tag_ids):
                    raise ValueError("Thẻ không tồn tại")

            else:
                tags = []

        try:
            # Cập nhật bảng ProductTag
            if tags is not None:
                stmt = delete(ProductTag).where(
                    ProductTag.product_id
                    == product.product_id
                )

                db.session.execute(stmt)

                for tag in tags:
                    db.session.add(
                        ProductTag(
                            product_id=product.product_id,
                            tag_id=tag.tag_id
                        )
                    )

            db.session.commit()

            return product

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_product(product_id):
        product = ProductService.get_product_by_id(product_id)

        product.active = False

        try:
            db.session.commit()
            return product

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def create_tag(name):
        name = name.strip() if name else ""

        if not name:
            raise ValueError("Tên thẻ không được để trống")

        stmt = select(Tag).where(Tag.name == name)

        existing_tag = db.session.scalar(stmt)

        if existing_tag:
            raise ValueError("Tên thẻ đã tồn tại")

        tag = Tag(name=name)

        try:
            db.session.add(tag)
            db.session.commit()

            return tag

        except Exception:
            db.session.rollback()
            raise
        
    @staticmethod
    def get_all_tags():
        stmt = select(Tag).where(Tag.active.is_(True))

        return db.session.scalars(stmt).all()