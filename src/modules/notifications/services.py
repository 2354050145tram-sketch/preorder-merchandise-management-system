from config import db
from sqlalchemy import select
from utils.email import send_email
from modules.notifications.models import Notification, UserNotification
from modules.users.models import User
from modules.preorders.models import PreOrder
from modules.orders.models import Order, OrderItem, Payment


class NotificationService:

    @staticmethod
    def send_preorder_notification(preorder_id, title, message):
        preorder = db.session.get(PreOrder, preorder_id)

        if not preorder:
            raise ValueError("Đợt preorder không tồn tại")

        title = title.strip() if title else ""
        message = message.strip() if message else ""

        if not title or not message:
            raise ValueError("Thông tin thông báo không được để trống")

        stmt = (
            select(User)
            .join(Order, User.user_id == Order.user_id)
            .join(OrderItem, Order.order_id == OrderItem.order_id)
            .join(Payment, Order.order_id == Payment.order_id)
            .where(
                OrderItem.preorder_id == preorder_id,
                OrderItem.item_status != "ĐÃ HỦY",
                User.active.is_(True),
                Payment.payment_status == "ĐÃ THANH TOÁN",
            )
            .distinct()
        )

        users = db.session.scalars(stmt).all()

        if not users:
            return None

        notification = Notification(
            preorder_id=preorder_id, title=title, message=message
        )

        try:
            db.session.add(notification)
            db.session.flush()

            for user in users:
                user_notification = UserNotification(
                    user_id=user.user_id, notification_id=(notification.notification_id)
                )

                db.session.add(user_notification)

            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        for user in users:
            try:
                send_email(recipient=user.email, subject=title, body=message)

            except Exception as error:
                print(f"Không thể gửi email cho " f"{user.email}: {error}")

        return notification

    @staticmethod
    def get_user_notifications(user_id):

        user = db.session.get(User, user_id)

        if not user or not user.active:
            raise ValueError("User không tồn tại")

        stmt = (
            select(Notification)
            .join(
                UserNotification,
                Notification.notification_id == UserNotification.notification_id,
            )
            .where(
                UserNotification.user_id == user_id,
            )
            .order_by(UserNotification.send_at.desc())
        )

        return db.session.scalars(stmt).all()
