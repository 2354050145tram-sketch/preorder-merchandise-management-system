from flask_mail import Message
from config import mail


def send_email(recipient, subject, body):
    recipient = recipient.strip() if recipient else ""

    subject = subject.strip() if subject else ""

    body = body.strip() if body else ""

    if not recipient:
        raise ValueError("Email người nhận không được để trống")

    if not subject:
        raise ValueError("Tiêu đề email không được để trống")

    if not body:
        raise ValueError("Nội dung email không được để trống")

    message = Message(subject=subject, recipients=[recipient], body=body)

    mail.send(message)
