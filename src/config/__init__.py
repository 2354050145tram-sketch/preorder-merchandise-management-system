import os
from dotenv import load_dotenv
from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

load_dotenv()


app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static",
)


MYSQL_DATABASE_URL = (
    "mysql+pymysql://root:root@localhost/" "preorder_merchandise_db?charset=utf8mb4"
)


if os.getenv("APP_ENV") == "testing":
    test_database_url = os.getenv("TEST_DATABASE_URL")

    if test_database_url != "sqlite:///:memory:":
        raise RuntimeError(
            "ĐÃ CHẶN: môi trường test bắt buộc " "phải dùng sqlite:///:memory:"
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = test_database_url

else:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        MYSQL_DATABASE_URL,
    )


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-secret-key",
)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")

app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")


db = SQLAlchemy(app=app)

mail = Mail(app)
