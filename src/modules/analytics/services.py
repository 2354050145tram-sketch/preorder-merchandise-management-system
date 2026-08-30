from config import db
from sqlalchemy import select, func
from modules.orders.models import Order, OrderItem, Payment
from modules.products.models import Product
from modules.inventories.models import Inventory
from modules.users.models import User
from modules.wallets.models import WalletTransaction


class AnalyticsService:

    @staticmethod
    def get_dashboard_summary():
        # Tổng tiền khách đã thanh toán
        paid_stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.payment_status.in_(["ĐÃ THANH TOÁN", "ĐÃ HOÀN TIỀN"])
        )
        total_paid = db.session.scalar(paid_stmt) or 0

        # Tổng tiền đã hoàn về Ví Verd
        refund_stmt = select(
            func.coalesce(func.sum(WalletTransaction.amount), 0)
        ).where(
            WalletTransaction.transaction_type == "HOÀN TIỀN",
            WalletTransaction.transaction_status == "THÀNH CÔNG",
        )
        total_refunded = db.session.scalar(refund_stmt) or 0

        total_revenue = float(total_paid) - float(total_refunded)

        # Tổng đơn hàng
        order_stmt = select(func.count(Order.order_id)).where(Order.active.is_(True))
        total_orders = db.session.scalar(order_stmt) or 0

        # Tổng khách hàng
        customer_stmt = select(func.count(User.user_id)).where(
            User.active.is_(True), User.role_id != 0
        )
        total_customers = db.session.scalar(customer_stmt) or 0

        # Tổng sản phẩm
        product_stmt = select(func.count(Product.product_id)).where(
            Product.active.is_(True)
        )
        total_products = db.session.scalar(product_stmt) or 0

        # Đếm số lượng sản phẩm sắp hết / hết hàng (quantity <= 5)
        low_stock_stmt = select(func.count(Inventory.inventory_id)).where(
            Inventory.active.is_(True), Inventory.quantity <= 5
        )
        low_stock_count = db.session.scalar(low_stock_stmt) or 0

        return {
            "total_revenue": total_revenue,
            "total_orders": int(total_orders),
            "total_customers": int(total_customers),
            "total_products": int(total_products),
            "low_stock_count": int(low_stock_count),
        }

    @staticmethod
    def get_revenue_report(start_date=None, end_date=None):
        # Tiền thanh toán theo ngày
        paid_stmt = select(
            func.date(Payment.paid_at).label("date"),
            func.coalesce(func.sum(Payment.amount), 0).label("amount"),
        ).where(
            Payment.payment_status.in_(["ĐÃ THANH TOÁN", "ĐÃ HOÀN TIỀN"]),
            Payment.paid_at.is_not(None),
        )

        if start_date is not None:
            paid_stmt = paid_stmt.where(Payment.paid_at >= start_date)

        if end_date is not None:
            paid_stmt = paid_stmt.where(Payment.paid_at <= end_date)

        paid_stmt = paid_stmt.group_by(func.date(Payment.paid_at))

        paid_results = db.session.execute(paid_stmt).all()

        # Tiền hoàn về Ví Verd theo ngày
        refund_stmt = select(
            func.date(WalletTransaction.created_at).label("date"),
            func.coalesce(func.sum(WalletTransaction.amount), 0).label("amount"),
        ).where(
            WalletTransaction.transaction_type == "HOÀN TIỀN",
            WalletTransaction.transaction_status == "THÀNH CÔNG",
        )

        if start_date is not None:
            refund_stmt = refund_stmt.where(WalletTransaction.created_at >= start_date)

        if end_date is not None:
            refund_stmt = refund_stmt.where(WalletTransaction.created_at <= end_date)

        refund_stmt = refund_stmt.group_by(func.date(WalletTransaction.created_at))

        refund_results = db.session.execute(refund_stmt).all()

        # Gộp dữ liệu theo ngày
        report = {}

        for row in paid_results:
            report[row.date] = {
                "date": row.date,
                "paid": float(row.amount or 0),
                "refunded": 0.0,
            }

        for row in refund_results:
            if row.date not in report:
                report[row.date] = {
                    "date": row.date,
                    "paid": 0.0,
                    "refunded": 0.0,
                }

            report[row.date]["refunded"] = float(row.amount or 0)

        results = []

        for data in report.values():
            results.append(
                {
                    "date": data["date"],
                    "paid": data["paid"],
                    "refunded": data["refunded"],
                    "revenue": (data["paid"] - data["refunded"]),
                }
            )

        results.sort(key=lambda item: str(item["date"]))

        return results

    @staticmethod
    def get_order_statistics():
        stmt = (
            select(
                Order.order_status,
                func.count(Order.order_id).label("total"),
            )
            .where(Order.active.is_(True))
            .group_by(Order.order_status)
        )

        results = db.session.execute(stmt).all()

        return [
            {
                "order_status": row.order_status,
                "total": int(row.total or 0),
            }
            for row in results
        ]

    @staticmethod
    def get_best_selling_products(limit=10):
        stmt = (
            select(
                Product.product_id,
                Product.product_name,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("quantity_sold"),
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
                "quantity_sold": int(row.quantity_sold or 0),
            }
            for row in results
        ]

    @staticmethod
    def get_low_stock_products(threshold=5):
        stmt = (
            select(
                Inventory.product_id,
                Product.product_name,
                Inventory.quantity,
            )
            .join(Product, Inventory.product_id == Product.product_id)
            .where(
                Inventory.active.is_(True),
                Product.active.is_(True),
                Inventory.quantity <= threshold,
            )
            .order_by(Inventory.quantity.asc())
        )

        results = db.session.execute(stmt).all()

        return [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "quantity": int(row.quantity or 0),
                "status": "HẾT HÀNG" if int(row.quantity or 0) == 0 else "SẮP HẾT HÀNG",
            }
            for row in results
        ]

    @staticmethod
    def get_customer_statistics(limit=10):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            raise ValueError("Giới hạn không hợp lệ")

        if limit <= 0:
            raise ValueError("Giới hạn phải lớn hơn 0")

        # Tổng số khách hàng đang hoạt động
        total_customer_stmt = select(func.count(User.user_id)).where(
            User.active.is_(True),
            User.role_id != 0,
        )

        total_customers = db.session.scalar(total_customer_stmt) or 0

        paid_subquery = (
            select(
                Order.user_id.label("user_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("total_paid"),
            )
            .join(Payment, Payment.order_id == Order.order_id)
            .where(Payment.payment_status.in_(["ĐÃ THANH TOÁN", "ĐÃ HOÀN TIỀN"]))
            .group_by(Order.user_id)
            .subquery()
        )

        refund_subquery = (
            select(
                Order.user_id.label("user_id"),
                func.coalesce(func.sum(WalletTransaction.amount), 0).label(
                    "total_refunded"
                ),
            )
            .join(WalletTransaction, WalletTransaction.order_id == Order.order_id)
            .where(
                WalletTransaction.transaction_type == "HOÀN TIỀN",
                WalletTransaction.transaction_status == "THÀNH CÔNG",
            )
            .group_by(Order.user_id)
            .subquery()
        )

        order_subquery = (
            select(
                Order.user_id.label("user_id"),
                func.count(Order.order_id).label("total_orders"),
            )
            .where(
                Order.active.is_(True),
                Order.order_status != "ĐÃ HỦY",
            )
            .group_by(Order.user_id)
            .subquery()
        )

        total_spent_expression = func.coalesce(
            paid_subquery.c.total_paid, 0
        ) - func.coalesce(refund_subquery.c.total_refunded, 0)

        top_customer_stmt = (
            select(
                User.user_id,
                User.username,
                func.coalesce(order_subquery.c.total_orders, 0).label("total_orders"),
                func.coalesce(paid_subquery.c.total_paid, 0).label("total_paid"),
                func.coalesce(refund_subquery.c.total_refunded, 0).label(
                    "total_refunded"
                ),
                total_spent_expression.label("total_spent"),
            )
            .outerjoin(order_subquery, User.user_id == order_subquery.c.user_id)
            .outerjoin(paid_subquery, User.user_id == paid_subquery.c.user_id)
            .outerjoin(refund_subquery, User.user_id == refund_subquery.c.user_id)
            .where(
                User.active.is_(True),
                User.role_id != 0,
            )
            .order_by(
                total_spent_expression.desc(),
                User.user_id.asc(),
            )
            .limit(limit)
        )

        top_customers = db.session.execute(top_customer_stmt).all()

        return {
            "total_customers": int(total_customers),
            "top_customers": [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "total_orders": int(row.total_orders or 0),
                    "total_paid": float(row.total_paid or 0),
                    "total_refunded": float(row.total_refunded or 0),
                    "total_spent": float(row.total_spent or 0),
                }
                for row in top_customers
            ],
        }
