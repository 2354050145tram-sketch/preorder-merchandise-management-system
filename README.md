# preorder-merchandise-management-system

## Mô tả
Ứng dụng web quản lý dịch vụ pre-order merchandise là hệ thống hỗ trợ quản lý sản phẩm, đơn đặt trước, khách hàng, đơn hàng và phân quyền người dùng. Hệ thống được xây dựng theo mô hình Client–Server, trong đó Backend (Python FLask) cung cấp API và Frontend (HTML, CSS, JavaScript) giao tiếp thông qua HTTP requests.

## Công nghệ sử dụng
- Backend: Python Flask
- Frontend: HTML, CSS, JavaScript
- Database: MySQL

## Cài đặt và chạy

### Chạy Backend
```bash
cd backend

# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường
venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Tạo và cập nhật database
cd src
python manage.py makemigrations
python manage.py migrate


### Chạy test report 
```bash
### BACKEND
# Cài dependencies
pip install -r requirements.txt

# Chạy test report
python -m pytest -q --cov=src/modules --cov=src/utils --cov-report=term-missing --cov-report=html
