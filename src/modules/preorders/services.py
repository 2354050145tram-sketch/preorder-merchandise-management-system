from config import db
from sqlalchemy import or_
import re
from werkzeug.security import generate_password_hash, check_password_hash
from modules.preorders.models import PreOrder
class PreOrderService:

    @staticmethod
    def create_preorder():
        pass

    @staticmethod
    def get_all_preorders():
        pass
    
    @staticmethod
    def get_preorder_by_id():
        pass

    @staticmethod
    def update_preorder():
        pass

    @staticmethod
    def update_progress():
        pass

    @staticmethod
    def delete_preorder():
        pass