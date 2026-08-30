from config import db
from decimal import Decimal, InvalidOperation
from sqlalchemy import select, delete
from modules.products.models import Product, Tag, ProductTag, Category, SubCategory


class ProductService:

    @staticmethod
    def create_product(product_name, price, description, image, status, tag_ids=None):
        product_name = product_name.strip() if product_name else ""

        description = description.strip() if description else ""

        image = image.strip() if image else ""

        if not all([product_name, price, description, image, status]):
            raise ValueError("Thông tin sản phẩm không được để trống")

        try:
            price = Decimal(str(price))

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            raise ValueError("Giá sản phẩm không hợp lệ")

        if not price.is_finite() or price <= 0:
            raise ValueError("Giá sản phẩm phải lớn hơn 0")

        if status not in [
            "PREORDER",
            "IN_STOCK",
        ]:
            raise ValueError("Trạng thái sản phẩm không hợp lệ")

        stmt = select(Product).where(Product.product_name == product_name)

        existing_product = db.session.scalar(stmt)

        if existing_product:
            raise ValueError("Tên sản phẩm đã tồn tại")

        tags = []

        if tag_ids:
            tag_ids = list(set(tag_ids))

            stmt = select(Tag).where(
                Tag.tag_id.in_(tag_ids),
                Tag.active.is_(True),
            )

            tags = db.session.scalars(stmt).all()

            if len(tags) != len(tag_ids):
                raise ValueError("Thẻ không tồn tại")

            sub_category_ids = {tag.sub_category_id for tag in tags}

            if len(sub_category_ids) > 1:
                raise ValueError(
                    "Các thẻ của sản phẩm phải thuộc " "cùng một danh mục phụ"
                )

        product = Product(
            product_name=product_name,
            price=price,
            description=description,
            image=image,
            status=status,
        )

        try:
            db.session.add(product)

            db.session.flush()

            for tag in tags:
                product_tag = ProductTag(
                    product_id=product.product_id,
                    tag_id=tag.tag_id,
                )

                db.session.add(product_tag)

            db.session.commit()

            return product

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all_products(
        keyword=None,
        status=None,
        tag_ids=None,
        category_id=None,
        sub_category_id=None,
        min_price=None,
        max_price=None,
        active=True,
    ):
        stmt = select(Product)

        if active is not None:
            stmt = stmt.where(Product.active == active)

        if keyword and keyword.strip():
            keyword = keyword.strip()

            stmt = stmt.where(Product.product_name.ilike(f"%{keyword}%"))

        if status:
            if status not in [
                "PREORDER",
                "IN_STOCK",
            ]:
                raise ValueError("Trạng thái sản phẩm không hợp lệ")

            stmt = stmt.where(Product.status == status)

        if min_price is not None:
            try:
                min_price = Decimal(str(min_price))

            except (
                InvalidOperation,
                TypeError,
                ValueError,
            ):
                raise ValueError("Giá tối thiểu không hợp lệ")

            if not min_price.is_finite() or min_price < 0:
                raise ValueError("Giá tối thiểu không hợp lệ")

        if max_price is not None:
            try:
                max_price = Decimal(str(max_price))

            except (
                InvalidOperation,
                TypeError,
                ValueError,
            ):
                raise ValueError("Giá tối đa không hợp lệ")

            if not max_price.is_finite() or max_price < 0:
                raise ValueError("Giá tối đa không hợp lệ")

        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValueError("Khoảng giá không hợp lệ")

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)

        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        need_tag_join = (
            category_id is not None or sub_category_id is not None or bool(tag_ids)
        )

        if need_tag_join:
            stmt = stmt.join(
                ProductTag,
                Product.product_id == ProductTag.product_id,
            ).join(
                Tag,
                ProductTag.tag_id == Tag.tag_id,
            )

        if category_id is not None:
            category = db.session.get(Category, category_id)

            if not category or not category.active:
                raise ValueError("Danh mục không tồn tại")

            stmt = stmt.join(
                SubCategory,
                Tag.sub_category_id == SubCategory.sub_category_id,
            ).where(
                SubCategory.category_id == category_id,
                SubCategory.active.is_(True),
                Tag.active.is_(True),
            )

        if sub_category_id is not None:
            sub_category = db.session.get(SubCategory, sub_category_id)

            if not sub_category or not sub_category.active:
                raise ValueError("Danh mục phụ không tồn tại")

            if category_id is not None and sub_category.category_id != category_id:
                raise ValueError("Danh mục phụ không thuộc danh mục đã chọn")

            stmt = stmt.where(
                Tag.sub_category_id == sub_category_id,
                Tag.active.is_(True),
            )

        if tag_ids:
            tag_ids = list(set(tag_ids))

            tags = db.session.scalars(
                select(Tag).where(
                    Tag.tag_id.in_(tag_ids),
                    Tag.active.is_(True),
                )
            ).all()

            if len(tags) != len(tag_ids):
                raise ValueError("Thẻ không tồn tại")

            if sub_category_id is not None:
                for tag in tags:
                    if tag.sub_category_id != sub_category_id:
                        raise ValueError("Thẻ không thuộc danh mục phụ đã chọn")

            stmt = stmt.where(Tag.tag_id.in_(tag_ids))

        stmt = stmt.distinct().order_by(Product.created_at.desc())

        return db.session.scalars(stmt).all()

    @staticmethod
    def get_product_by_id(
        product_id,
        active=None,
    ):
        product = db.session.get(Product, product_id)

        if not product:
            raise ValueError("Sản phẩm không tồn tại")

        if active is not None and product.active != active:
            raise ValueError("Sản phẩm không tồn tại")

        return product

    @staticmethod
    def update_product(
        product_id,
        data,
        tag_ids=None,
    ):
        product = ProductService.get_product_by_id(
            product_id,
            active=True,
        )

        if "product_name" in data and data["product_name"]:
            product_name = data["product_name"].strip()

            if product_name and product_name != product.product_name:
                stmt = select(Product).where(
                    Product.product_name == product_name,
                    Product.product_id != product_id,
                )

                existing_product = db.session.scalar(stmt)

                if existing_product:
                    raise ValueError("Tên sản phẩm đã tồn tại")

                product.product_name = product_name

        if "price" in data and data["price"] not in [None, ""]:
            try:
                price = Decimal(str(data["price"]))

            except (
                InvalidOperation,
                TypeError,
                ValueError,
            ):
                raise ValueError("Giá sản phẩm không hợp lệ")

            if not price.is_finite() or price <= 0:
                raise ValueError("Giá sản phẩm phải lớn hơn 0")

            product.price = price

        if "description" in data and data["description"]:
            description = data["description"].strip()

            if description:
                product.description = description

        if "image" in data and data["image"]:
            image = data["image"].strip()

            if image:
                product.image = image

        if "status" in data and data["status"]:
            if data["status"] not in [
                "PREORDER",
                "IN_STOCK",
            ]:
                raise ValueError("Trạng thái sản phẩm không hợp lệ")

            product.status = data["status"]

        tags = None

        if tag_ids is not None:
            tag_ids = list(set(tag_ids))

            if tag_ids:
                stmt = select(Tag).where(
                    Tag.tag_id.in_(tag_ids),
                    Tag.active.is_(True),
                )

                tags = db.session.scalars(stmt).all()

                if len(tags) != len(tag_ids):
                    raise ValueError("Thẻ không tồn tại")

                sub_category_ids = {tag.sub_category_id for tag in tags}

                if len(sub_category_ids) > 1:
                    raise ValueError(
                        "Các thẻ của sản phẩm phải thuộc " "cùng một danh mục phụ"
                    )

            else:
                tags = []

        try:
            if tags is not None:
                stmt = delete(ProductTag).where(
                    ProductTag.product_id == product.product_id
                )

                db.session.execute(stmt)

                for tag in tags:
                    db.session.add(
                        ProductTag(
                            product_id=product.product_id,
                            tag_id=tag.tag_id,
                        )
                    )

            db.session.commit()

            return product

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_product(product_id):
        product = ProductService.get_product_by_id(
            product_id,
            active=True,
        )

        product.active = False

        try:
            db.session.commit()

            return product

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def create_tag(
        name,
        sub_category_id,
    ):
        name = name.strip() if name else ""

        if not name:
            raise ValueError("Tên thẻ không được để trống")

        sub_category = db.session.get(SubCategory, sub_category_id)

        if not sub_category or not sub_category.active:
            raise ValueError("Danh mục phụ không tồn tại")

        stmt = select(Tag).where(
            Tag.name == name,
            Tag.sub_category_id == sub_category_id,
        )

        existing_tag = db.session.scalar(stmt)

        if existing_tag:
            raise ValueError("Thẻ đã tồn tại trong danh mục phụ này")

        tag = Tag(
            name=name,
            sub_category_id=sub_category_id,
        )

        try:
            db.session.add(tag)

            db.session.commit()

            return tag

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all_tags():
        stmt = select(Tag).where(Tag.active.is_(True)).order_by(Tag.name)

        return db.session.scalars(stmt).all()

    @staticmethod
    def get_categories():
        stmt = select(Category).where(Category.active.is_(True)).order_by(Category.name)

        return db.session.scalars(stmt).all()

    @staticmethod
    def get_sub_categories(category_id):
        category = db.session.get(Category, category_id)

        if not category or not category.active:
            raise ValueError("Danh mục không tồn tại")

        stmt = (
            select(SubCategory)
            .where(
                SubCategory.category_id == category_id,
                SubCategory.active.is_(True),
            )
            .order_by(SubCategory.name)
        )

        return db.session.scalars(stmt).all()

    @staticmethod
    def get_tags_by_sub_category(sub_category_id):
        sub_category = db.session.get(SubCategory, sub_category_id)

        if not sub_category or not sub_category.active:
            raise ValueError("Danh mục phụ không tồn tại")

        stmt = (
            select(Tag)
            .where(
                Tag.sub_category_id == sub_category_id,
                Tag.active.is_(True),
            )
            .order_by(Tag.name)
        )

        return db.session.scalars(stmt).all()
