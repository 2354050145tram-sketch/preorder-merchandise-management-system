from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from datetime import date
from modules.preorders.services import PreOrderService
from modules.preorders.helpers import serialize_preorder, check_admin
from utils.helpers import response_success, response_error

preorder_bp = Blueprint("preorders", __name__, url_prefix="/api/preorders")


@preorder_bp.route("", methods=["GET"])
def get_all_preorders():
    try:
        keyword = request.args.get("keyword")

        min_price = request.args.get("min_price")

        max_price = request.args.get("max_price")

        tag_ids = request.args.getlist("tag_ids", type=int)

        preorders = PreOrderService.get_all_preorders(
            keyword=keyword,
            tag_ids=tag_ids or None,
            min_price=min_price,
            max_price=max_price,
            active=True,
        )

        return (
            response_success(
                {"preorders": [serialize_preorder(preorder) for preorder in preorders]}
            ),
            200,
        )

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy danh sách preorder", 500)


@preorder_bp.route("/<int:preorder_id>", methods=["GET"])
def get_preorder_by_id(preorder_id):
    try:
        preorder = PreOrderService.get_preorder_by_id(preorder_id, active=True)

        return response_success(
            {"preorder": serialize_preorder(preorder)},
            "Lấy preorder thành công",
            200,
        )

    except ValueError as error:
        return response_error(str(error), 404)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy preorder", 500)


@preorder_bp.route("/admin", methods=["GET"])
@jwt_required()
def get_all_preorders_admin():
    try:
        check_admin()

        keyword = request.args.get("keyword")

        min_price = request.args.get("min_price")

        max_price = request.args.get("max_price")

        tag_ids = request.args.getlist("tag_ids", type=int)

        active_param = request.args.get("active")

        if active_param is None:
            active = None

        elif active_param.lower() == "true":
            active = True

        elif active_param.lower() == "false":
            active = False

        else:
            raise ValueError("Trạng thái active không hợp lệ")

        preorders = PreOrderService.get_all_preorders(
            keyword=keyword,
            tag_ids=tag_ids or None,
            min_price=min_price,
            max_price=max_price,
            active=active,
        )

        return response_success(
            {"preorders": [serialize_preorder(preorder) for preorder in preorders]},
            "Lấy danh sách preorder thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi lấy danh sách preorder", 500)


@preorder_bp.route("/admin", methods=["POST"])
@jwt_required()
def create_preorder():
    try:
        check_admin()

        data = request.get_json() or {}

        try:
            start_date = date.fromisoformat(data.get("start_date", ""))

            end_date = date.fromisoformat(data.get("end_date", ""))

        except (TypeError, ValueError):
            raise ValueError("Ngày bắt đầu hoặc kết thúc không hợp lệ")

        preorder = PreOrderService.create_preorder(
            product_id=data.get("product_id"),
            start_date=start_date,
            end_date=end_date,
            progress_note=data.get("progress_note"),
        )

        return response_success(
            {"preorder": serialize_preorder(preorder)}, "Tạo preorder thành công", 201
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi tạo preorder", 500)


@preorder_bp.route("/admin/<int:preorder_id>", methods=["PUT"])
@jwt_required()
def update_preorder(preorder_id):
    try:
        check_admin()

        data = request.get_json() or {}

        if "start_date" in data and data["start_date"]:
            try:
                data["start_date"] = date.fromisoformat(data["start_date"])
            except ValueError:
                raise ValueError("Ngày bắt đầu không hợp lệ")

        if "end_date" in data and data["end_date"]:
            try:
                data["end_date"] = date.fromisoformat(data["end_date"])
            except ValueError:
                raise ValueError("Ngày kết thúc không hợp lệ")

        preorder = PreOrderService.update_preorder(preorder_id, data)

        return response_success(
            {"preorder": serialize_preorder(preorder)},
            "Cập nhật preorder thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi cập nhật preorder", 500)


@preorder_bp.route("/admin/<int:preorder_id>/progress", methods=["PUT"])
@jwt_required()
def update_progress(preorder_id):
    try:
        check_admin()

        data = request.get_json() or {}

        preorder = PreOrderService.update_progress(
            preorder_id=preorder_id,
            progress_status=data.get("progress_status"),
            progress_note=data.get("progress_note"),
        )

        return response_success(
            {"preorder": serialize_preorder(preorder)},
            "Cập nhật tiến độ thành công",
            200,
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi cập nhật tiến độ preorder", 500)


@preorder_bp.route("/admin/<int:preorder_id>", methods=["DELETE"])
@jwt_required()
def delete_preorder(preorder_id):
    try:
        check_admin()

        preorder = PreOrderService.delete_preorder(preorder_id)

        return response_success(
            {"preorder_id": preorder.preorder_id}, "Preorder đã được đóng", 200
        )

    except PermissionError as error:
        return response_error(str(error), 403)

    except ValueError as error:
        return response_error(str(error), 400)

    except Exception:
        return response_error("Có lỗi xảy ra khi đóng preorder", 500)
