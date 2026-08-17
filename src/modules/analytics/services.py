from config import db
from sqlalchemy import select, func
from modules.orders.models import Order, OrderItem, Payment
from modules.products.models import Product
from modules.inventories.models import Inventory, InventoryTransaction
from modules.users.models import User


class AnalyticsService:

    @staticmethod
    def get_dashboard_summary():
        # Tổng doanh thu
        revenue_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.payment_status == "ĐÃ THANH TOÁN"
        )

        total_revenue = db.session.scalar(revenue_stmt)

        # Tổng đơn hàng
        order_stmt = select(func.count(Order.order_id)).where(Order.active.is_(True))

        total_orders = db.session.scalar(order_stmt)

        # Tổng khách hàng
        customer_stmt = select(func.count(User.user_id)).where(User.active.is_(True))

        total_customers = db.session.scalar(customer_stmt)

        # Tổng sản phẩm
        product_stmt = select(func.count(Product.product_id)).where(
            Product.active.is_(True)
        )

        total_products = db.session.scalar(product_stmt)

        # Sản phẩm sắp hết hoặc hết hàng
        inventories = db.session.scalars(
            select(Inventory).where(Inventory.active.is_(True))
        ).all()

        low_stock_products = [
            inventory
            for inventory in inventories
            if inventory.status in ["SẮP HẾT HÀNG", "HẾT HÀNG"]
        ]

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_products": total_products,
            "low_stock_count": len(low_stock_products),
        }

    @staticmethod
    def get_revenue_report(start_date=None, end_date=None):
        stmt = select(
            func.date(Payment.paid_at).label("date"),
            func.sum(Payment.amount).label("revenue"),
        ).where(Payment.payment_status == "ĐÃ THANH TOÁN", Payment.paid_at.is_not(None))

        if start_date is not None:
            stmt = stmt.where(Payment.paid_at >= start_date)

        if end_date is not None:
            stmt = stmt.where(Payment.paid_at <= end_date)

        stmt = stmt.group_by(func.date(Payment.paid_at)).order_by(
            func.date(Payment.paid_at)
        )

        results = db.session.execute(stmt).all()

        return [{"date": row.date, "revenue": row.revenue} for row in results]

    @staticmethod
    def get_order_statistics():
        stmt = (
            select(Order.order_status, func.count(Order.order_id).label("total"))
            .where(Order.active.is_(True))
            .group_by(Order.order_status)
        )

        results = db.session.execute(stmt).all()

        return [
            {"order_status": row.order_status, "total": row.total} for row in results
        ]

    @staticmethod
    def get_best_selling_products(limit=10):
        stmt = (
            select(
                Product.product_id,
                Product.product_name,
                func.sum(OrderItem.quantity).label("quantity_sold"),
            )
            .join(OrderItem, Product.product_id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.order_id)
            .where(
                Product.active.is_(True),
                Order.active.is_(True),
                Order.order_status != "ĐÃ HỦY",
                OrderItem.item_status != "ĐÃ HỦY",
            )
            .group_by(Product.product_id, Product.product_name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )

        results = db.session.execute(stmt).all()

        return [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "quantity_sold": row.quantity_sold,
            }
            for row in results
        ]

    @staticmethod
    def get_low_stock_products():
        stmt = (
            select(Inventory)
            .join(Product, Inventory.product_id == Product.product_id)
            .where(Inventory.active.is_(True), Product.active.is_(True))
        )

        inventories = db.session.scalars(stmt).all()

        results = []

        for inventory in inventories:
            if inventory.status in ["SẮP HẾT HÀNG", "HẾT HÀNG"]:
                results.append(
                    {
                        "product_id": inventory.product_id,
                        "product_name": inventory.product.product_name,
                        "quantity": inventory.quantity,
                        "status": inventory.status,
                    }
                )

        return results

    @staticmethod
    def get_customer_statistics(limit=10):
        # Tổng số khách
        total_customer_stmt = select(func.count(User.user_id)).where(
            User.active.is_(True)
        )

        total_customers = db.session.scalar(total_customer_stmt)

        # Khách mua nhiều nhất
        top_customer_stmt = (
            select(
                User.user_id,
                User.username,
                func.count(Order.order_id).label("total_orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("total_spent"),
            )
            .join(Order, User.user_id == Order.user_id)
            .where(
                User.active.is_(True),
                Order.active.is_(True),
                Order.order_status != "ĐÃ HỦY",
            )
            .group_by(User.user_id, User.username)
            .order_by(func.sum(Order.total_amount).desc())
            .limit(limit)
        )

        top_customers = db.session.execute(top_customer_stmt).all()

        return {
            "total_customers": total_customers,
            "top_customers": [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "total_orders": row.total_orders,
                    "total_spent": row.total_spent,
                }
                for row in top_customers
            ],
        }

    @staticmethod
    def get_inventory_report():
        stmt = select(
            InventoryTransaction.transaction_type,
            func.sum(InventoryTransaction.quantity).label("total_quantity"),
        ).group_by(InventoryTransaction.transaction_type)

        results = db.session.execute(stmt).all()

        return [
            {
                "transaction_type": row.transaction_type,
                "total_quantity": row.total_quantity,
            }
            for row in results
        ]
