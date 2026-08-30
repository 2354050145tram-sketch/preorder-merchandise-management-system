from flask import render_template
from config import app
from flask_jwt_extended import JWTManager
from modules.users.routes import user_bp
from modules.products.routes import product_bp
from modules.preorders.routes import preorder_bp
from modules.orders.routes import order_bp
from modules.inventories.routes import inventory_bp
from modules.notifications.routes import notification_bp
from modules.wallets.routes import wallet_bp
from modules.analytics.routes import analytics_bp
from modules.carts.routes import cart_bp

app.config["JWT_SECRET_KEY"] = "super-secret-key"

jwt = JWTManager(app)


app.register_blueprint(user_bp)
app.register_blueprint(product_bp)
app.register_blueprint(preorder_bp)
app.register_blueprint(order_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(wallet_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(cart_bp)

import admin


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about_page():
    return render_template("customer/about.html")


@app.route("/products")
def products_page():
    return render_template("customer/products.html")


@app.route("/products/<int:product_id>")
def product_detail_page(product_id):
    return render_template(
        "customer/product_details.html",
        product_id=product_id,
    )


@app.route("/cart")
def cart_page():
    return render_template("customer/cart.html")


@app.route("/checkout")
def checkout_page():
    return render_template("customer/checkout.html")


@app.route("/profile")
def profile_page():
    return render_template("customer/profile.html")


@app.route("/orders/<int:order_id>")
def order_details_page(order_id):
    return render_template(
        "customer/order_details.html",
        order_id=order_id,
    )


@app.route("/payment/<int:order_id>")
def payment_page(order_id):
    return render_template(
        "customer/payment.html",
        order_id=order_id,
    )


@app.route("/admin")
def admin_page():
    return render_template("admin/dashboard.html")


@app.route("/admin/dashboard")
def admin_dashboard_page():
    return render_template("admin/dashboard.html")


@app.route("/admin/products")
def admin_products_page():
    return render_template("admin/products.html")


@app.route("/admin/orders")
def admin_orders_page():
    return render_template("admin/orders.html")


@app.route("/admin/inventory")
def admin_inventory_page():
    return render_template("admin/inventories.html")


@app.route("/admin/users")
def admin_users_page():
    return render_template("admin/users.html")


@app.route("/admin/deposits")
def admin_deposits_page():
    return render_template("admin/deposits.html")


@app.route("/login")
def login():
    return render_template("auth/login.html")


if __name__ == "__main__":

    app.run(debug=True)
