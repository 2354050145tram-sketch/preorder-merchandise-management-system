from config import app
from utils.email import send_email
from modules.users.models import User, Profile
from modules.products.models import Product
from modules.preorders.models import PreOrder
from modules.orders.models import Order, OrderItem, Payment
from modules.inventories.models import Inventory
from modules.notifications.models import Notification, UserNotification
from modules.wallets.models import Wallet, WalletTransaction
from flask_jwt_extended import JWTManager
from modules.users.routes import user_bp
from modules.notifications.routes import (
    notification_bp
)

app.register_blueprint(
    notification_bp
)
app.config["JWT_SECRET_KEY"] = "super-secret-key"
jwt = JWTManager(app)
app.register_blueprint(user_bp, url_prefix="/api")
import admin

if __name__ == "__main__":
    app.run(debug=True)