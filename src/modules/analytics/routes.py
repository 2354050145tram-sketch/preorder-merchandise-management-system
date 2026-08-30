from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from modules.analytics.services import AnalyticsService
from modules.analytics.helpers import (
    check_admin,
    serialize_dashboard_summary,
    serialize_revenue_report,
    serialize_order_statistic,
    serialize_best_selling_product,
    serialize_low_stock_product,
    serialize_customer_statistics,
)
from utils.helpers import response_success, response_error

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    try:
        check_admin()
        summary = AnalyticsService.get_dashboard_summary()
        return response_success({"dashboard": serialize_dashboard_summary(summary)})

    except PermissionError as error:
        return response_error(str(error), 403)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy dữ liệu dashboard", 500)


@analytics_bp.route("/revenue", methods=["GET"])
@jwt_required()
def get_revenue_report():
    try:
        check_admin()

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        try:
            start_date = datetime.fromisoformat(start_date) if start_date else None
            end_date = datetime.fromisoformat(end_date) if end_date else None
        except ValueError:
            raise ValueError("Ngày bắt đầu hoặc ngày kết thúc không hợp lệ")

        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("Ngày bắt đầu không được lớn hơn ngày kết thúc")

        report = AnalyticsService.get_revenue_report(
            start_date=start_date,
            end_date=end_date,
        )

        return response_success(
            {"revenue": [serialize_revenue_report(item) for item in report]}
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy báo cáo doanh thu", 500)


@analytics_bp.route("/orders", methods=["GET"])
@jwt_required()
def get_order_statistics():
    try:
        check_admin()
        statistics = AnalyticsService.get_order_statistics()
        return response_success(
            {"orders": [serialize_order_statistic(item) for item in statistics]}
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy thống kê đơn hàng", 500)


@analytics_bp.route("/products/best-selling", methods=["GET"])
@jwt_required()
def get_best_selling_products():
    try:
        check_admin()

        limit = request.args.get("limit", default=10, type=int)
        if limit is None or limit <= 0:
            raise ValueError("Giới hạn phải lớn hơn 0")

        products = AnalyticsService.get_best_selling_products(limit=limit)

        return response_success(
            {
                "products": [
                    serialize_best_selling_product(product) for product in products
                ]
            }
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy sản phẩm bán chạy", 500)


@analytics_bp.route("/inventory/low-stock", methods=["GET"])
@jwt_required()
def get_low_stock_products():
    try:
        check_admin()
        products = AnalyticsService.get_low_stock_products(threshold=5)
        return response_success({"products": products})

    except PermissionError as error:
        return response_error(str(error), 403)

    except Exception as error:
        return response_error("Có lỗi xảy ra khi lấy sản phẩm sắp hết hàng", 500)


@analytics_bp.route("/customers", methods=["GET"])
@jwt_required()
def get_customer_statistics():
    try:
        check_admin()

        limit = request.args.get("limit", default=10, type=int)
        if limit is None or limit <= 0:
            raise ValueError("Giới hạn phải lớn hơn 0")

        statistics = AnalyticsService.get_customer_statistics(limit=limit)
        return response_success(
            {"customers": serialize_customer_statistics(statistics)}
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy thống kê khách hàng", 500)


@analytics_bp.route("/admin/stats", methods=["GET"])
@jwt_required()
def get_dashboard_stats():
    try:
        check_admin()

        low_stock_list = AnalyticsService.get_low_stock_products(threshold=5)

        return response_success(
            {
                "low_stock_products": low_stock_list,
            },
            "Lấy dữ liệu dashboard thành công",
            200,
        )

    except Exception as error:
        return response_error(f"Lỗi: {str(error)}", 500)