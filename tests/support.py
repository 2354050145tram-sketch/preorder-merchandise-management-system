import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ["APP_ENV"] = "testing"
os.environ["TEST_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault(
    "FLASK_SECRET_KEY",
    "unit-test-secret",
)

from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash

from config import app, db

from modules.users.models import Profile, Role, User
from modules.products.models import Category, Product, ProductTag, SubCategory, Tag
from modules.preorders.models import PreOrder
from modules.orders.models import Order, OrderItem, Payment
from modules.inventories.models import Inventory, InventoryTransaction
from modules.notifications.models import Notification, UserNotification
from modules.wallets.models import Wallet, WalletTransaction
from modules.carts.models import Cart, CartItem

from modules.users.routes import user_bp
from modules.products.routes import product_bp
from modules.preorders.routes import preorder_bp
from modules.orders.routes import order_bp
from modules.inventories.routes import inventory_bp
from modules.notifications.routes import notification_bp
from modules.wallets.routes import wallet_bp
from modules.analytics.routes import analytics_bp
from modules.carts.routes import cart_bp

app.config.update(
    TESTING=True,
    JWT_SECRET_KEY="unit-test-jwt-secret-at-least-32-bytes",
    SECRET_KEY="unit-test-secret",
)

if "flask-jwt-extended" not in app.extensions:
    JWTManager(app)

for blueprint in (
    user_bp,
    product_bp,
    preorder_bp,
    order_bp,
    inventory_bp,
    notification_bp,
    wallet_bp,
    analytics_bp,
    cart_bp,
):
    if blueprint.name not in app.blueprints:
        app.register_blueprint(blueprint)


def ensure_safe_test_database():
    database_url = db.engine.url

    if os.getenv("APP_ENV") != "testing":
        raise RuntimeError("ĐÃ CHẶN: APP_ENV không phải testing.")

    if "PYTEST_CURRENT_TEST" not in os.environ:
        raise RuntimeError("ĐÃ CHẶN: chỉ được thao tác database bằng pytest.")

    if not app.config.get("TESTING"):
        raise RuntimeError("ĐÃ CHẶN: Flask chưa bật TESTING.")

    if database_url.get_backend_name() != "sqlite":
        raise RuntimeError("ĐÃ CHẶN MYSQL: " f"database hiện tại là {database_url}")

    if database_url.database != ":memory:":
        raise RuntimeError(
            "ĐÃ CHẶN: test chỉ được dùng SQLite RAM, " f"hiện tại là {database_url}"
        )


class DatabaseTestCase:
    """Mixin tạo database SQLite sạch cho từng test."""

    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

        try:
            ensure_safe_test_database()

            db.create_all()

            self.client = app.test_client()
            self.seed = self.seed_database()

        except Exception:
            db.session.remove()
            db.engine.dispose()
            self.app_context.pop()
            raise

    def tearDown(self):
        try:
            ensure_safe_test_database()

            db.session.rollback()
            db.session.remove()
            db.engine.dispose()

        finally:
            self.app_context.pop()

    def seed_database(self):
        admin_role = Role(role_id=0, name="ADMIN")
        customer_role = Role(role_id=1, name="CUSTOMER")
        db.session.add_all([admin_role, customer_role])

        admin = User(
            email="admin@example.com",
            username="admin",
            password=generate_password_hash("admin123"),
            provider="LOCAL",
            role_id=0,
        )
        customer = User(
            email="customer@example.com",
            username="customer",
            password=generate_password_hash("customer123"),
            provider="LOCAL",
            role_id=1,
        )
        other = User(
            email="other@example.com",
            username="other",
            password=generate_password_hash("other123"),
            provider="LOCAL",
            role_id=1,
        )
        db.session.add_all([admin, customer, other])
        db.session.flush()

        db.session.add_all(
            [
                Profile(
                    user_id=admin.user_id,
                    full_name="Admin",
                    phone_num="0900000001",
                    address="HCM",
                ),
                Profile(
                    user_id=customer.user_id,
                    full_name="Customer",
                    phone_num="0900000002",
                    address="HCM",
                ),
                Profile(
                    user_id=other.user_id,
                    full_name="Other",
                    phone_num="0900000003",
                    address="HN",
                ),
                Wallet(user_id=admin.user_id, balance=Decimal("1000000")),
                Wallet(user_id=customer.user_id, balance=Decimal("500000")),
                Wallet(user_id=other.user_id, balance=Decimal("100000")),
            ]
        )

        category = Category(name="Thời trang")
        db.session.add(category)
        db.session.flush()
        sub_category = SubCategory(category_id=category.category_id, name="Áo")
        other_sub = SubCategory(category_id=category.category_id, name="Phụ kiện")
        db.session.add_all([sub_category, other_sub])
        db.session.flush()
        tag = Tag(name="Oversize", sub_category_id=sub_category.sub_category_id)
        other_tag = Tag(name="Limited", sub_category_id=other_sub.sub_category_id)
        db.session.add_all([tag, other_tag])
        db.session.flush()

        stock_product = Product(
            product_name="Áo có sẵn",
            price=Decimal("100000"),
            description="Áo tồn kho",
            image="stock.jpg",
            status="IN_STOCK",
        )
        preorder_product = Product(
            product_name="Áo preorder",
            price=Decimal("200000"),
            description="Áo đặt trước",
            image="preorder.jpg",
            status="PREORDER",
        )
        spare_product = Product(
            product_name="Sản phẩm phụ",
            price=Decimal("50000"),
            description="Dùng cho test",
            image="spare.jpg",
            status="IN_STOCK",
        )
        db.session.add_all([stock_product, preorder_product, spare_product])
        db.session.flush()
        db.session.add_all(
            [
                ProductTag(product_id=stock_product.product_id, tag_id=tag.tag_id),
                ProductTag(product_id=preorder_product.product_id, tag_id=tag.tag_id),
                Inventory(
                    product_id=stock_product.product_id,
                    quantity=20,
                    price=Decimal("60000"),
                ),
            ]
        )
        preorder = PreOrder(
            product_id=preorder_product.product_id,
            start_date=date.today() - timedelta(days=2),
            end_date=date.today() + timedelta(days=7),
            quantity_order=0,
            progress_status="MỞ PREORDER",
            progress_note="Đang nhận đơn",
        )
        db.session.add(preorder)
        db.session.commit()

        return {
            "admin": admin,
            "customer": customer,
            "other": other,
            "category": category,
            "sub_category": sub_category,
            "other_sub": other_sub,
            "tag": tag,
            "other_tag": other_tag,
            "stock_product": stock_product,
            "preorder_product": preorder_product,
            "spare_product": spare_product,
            "preorder": preorder,
        }

    def access_headers(self, user_key="customer"):
        token = create_access_token(identity=str(self.seed[user_key].user_id))
        return {"Authorization": f"Bearer {token}"}

    def refresh_headers(self, user_key="customer"):
        token = create_refresh_token(identity=str(self.seed[user_key].user_id))
        return {"Authorization": f"Bearer {token}"}
