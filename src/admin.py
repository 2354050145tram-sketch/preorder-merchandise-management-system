from config import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from modules.users.models import User, Profile, Role
from modules.products.models import Product, Tag
from modules.orders.models import Order, Payment
from modules.preorders.models import PreOrder
from modules.inventories.models import Inventory
from modules.wallets.models import Wallet
from modules.notifications.models import Notification, UserNotification

admin = Admin(
    app=app,
    name="E-commerce Administration",
    url="/system-admin",
    endpoint="system_admin",
)


class ReadOnlyView(ModelView):
    can_create = False
    can_delete = False
    can_edit = False


class EditOnlyView(ModelView):
    can_create = False
    can_delete = False
    can_edit = True


admin.add_view(ReadOnlyView(User, db.session))
admin.add_view(ReadOnlyView(Profile, db.session))
admin.add_view(ReadOnlyView(Role, db.session))

admin.add_view(ModelView(Product, db.session))
admin.add_view(ModelView(Tag, db.session))

admin.add_view(EditOnlyView(Order, db.session))
admin.add_view(ReadOnlyView(Payment, db.session))

admin.add_view(ModelView(PreOrder, db.session))

admin.add_view(EditOnlyView(Inventory, db.session))

admin.add_view(ReadOnlyView(Wallet, db.session))

admin.add_view(ModelView(Notification, db.session))
admin.add_view(ReadOnlyView(UserNotification, db.session))
