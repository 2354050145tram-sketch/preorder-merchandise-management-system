from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from modules.wallets.services import WalletService
from modules.wallets.helpers import (
    check_admin,
    serialize_wallet,
    serialize_wallet_transaction,
)
from utils.helpers import response_success, response_error

wallet_bp = Blueprint(
    "wallets",
    __name__,
    url_prefix="/api/wallets",
)


@wallet_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_wallet():
    try:
        user_id = int(get_jwt_identity())

        wallet = WalletService.get_wallet_by_user(user_id)

        return response_success(
            {"wallet": serialize_wallet(wallet)},
            "Lấy thông tin ví thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            404,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy thông tin ví",
            500,
        )


@wallet_bp.route(
    "/me/transactions",
    methods=["GET"],
)
@jwt_required()
def get_my_transactions():
    try:
        user_id = int(get_jwt_identity())

        transaction_type = request.args.get("transaction_type")

        transaction_status = request.args.get("transaction_status")

        transactions = WalletService.get_transactions(
            user_id=user_id,
            transaction_type=transaction_type,
            transaction_status=transaction_status,
        )

        return response_success(
            {
                "transactions": [
                    serialize_wallet_transaction(transaction)
                    for transaction in transactions
                ]
            },
            "Lấy lịch sử giao dịch thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi lấy lịch sử giao dịch",
            500,
        )


@wallet_bp.route(
    "/deposit",
    methods=["POST"],
)
@jwt_required()
def create_deposit_request():
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}

        transaction = WalletService.create_deposit_request(
            user_id=user_id,
            amount=data.get("amount"),
            description=data.get("description"),
        )

        return response_success(
            {"transaction": serialize_wallet_transaction(transaction)},
            "Tạo yêu cầu nạp tiền thành công",
            201,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi tạo yêu cầu nạp tiền",
            500,
        )


@wallet_bp.route(
    "/withdraw",
    methods=["POST"],
)
@jwt_required()
def create_withdraw_request():
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}

        transaction = WalletService.create_withdraw_request(
            user_id=user_id,
            amount=data.get("amount"),
            description=data.get("description"),
        )

        return response_success(
            {"transaction": serialize_wallet_transaction(transaction)},
            "Tạo yêu cầu rút tiền thành công",
            201,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi tạo yêu cầu rút tiền",
            500,
        )


@wallet_bp.route(
    "/pay/<int:order_id>",
    methods=["POST"],
)
@jwt_required()
def pay_with_wallet(order_id):
    try:
        user_id = int(get_jwt_identity())

        data = request.get_json() or {}

        transaction = WalletService.pay_with_wallet(
            user_id=user_id,
            order_id=order_id,
            payment_type=data.get("payment_type"),
        )

        return response_success(
            {"transaction": serialize_wallet_transaction(transaction)},
            "Thanh toán bằng Ví Verd thành công",
            200,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi thanh toán bằng ví",
            500,
        )


@wallet_bp.route(
    "/admin/deposits/" "<int:wallet_transaction_id>/approve",
    methods=["PUT"],
)
@jwt_required()
def approve_deposit(wallet_transaction_id):
    try:
        check_admin()

        transaction = WalletService.approve_deposit(wallet_transaction_id)

        return response_success(
            {"transaction": serialize_wallet_transaction(transaction)},
            "Duyệt nạp tiền thành công",
            200,
        )

    except PermissionError as error:
        return response_error(
            str(error),
            403,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi duyệt nạp tiền",
            500,
        )


@wallet_bp.route(
    "/admin/withdrawals/" "<int:wallet_transaction_id>/approve",
    methods=["PUT"],
)
@jwt_required()
def approve_withdraw(wallet_transaction_id):
    try:
        check_admin()

        transaction = WalletService.approve_withdraw(wallet_transaction_id)

        return response_success(
            {"transaction": serialize_wallet_transaction(transaction)},
            "Duyệt rút tiền thành công",
            200,
        )

    except PermissionError as error:
        return response_error(
            str(error),
            403,
        )

    except ValueError as error:
        return response_error(
            str(error),
            400,
        )

    except Exception:
        return response_error(
            "Có lỗi xảy ra khi duyệt rút tiền",
            500,
        )
