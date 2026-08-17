import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = '@#$%^876$%^&*0IUYTRTYUIJ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/preorder_merchandise_db?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

app.config['MAIL_USERNAME'] = os.getenv(
    'MAIL_USERNAME'
)

app.config['MAIL_PASSWORD'] = os.getenv(
    'MAIL_PASSWORD'
)

app.config['MAIL_DEFAULT_SENDER'] = os.getenv(
    'MAIL_DEFAULT_SENDER'
)

db = SQLAlchemy(app=app)

mail=Mail(app)