# preorder-merchandise-management-system

## Mô tả
Ứng dụng web quản lý dịch vụ pre-order merchandise được phát triển theo quy trình Agile. Hệ thống hỗ trợ quản lý sản phẩm, đơn đặt trước, khách hàng, đơn hàng và phân quyền người dùng sử dụng Django REST framework (viết tắt là DRF). Hệ thống được xây dựng theo mô hình Client–Server, trong đó Backend (Django) cung cấp RESTful API và Frontend (ReactJS) giao tiếp thông qua HTTP requests.

## Công nghệ sử dụng
- Backend: Python (Django, RESTful API)
- Frontend: ReactJS
- Database: MySQL

## Cài đặt và chạy

### Chạy Backend
```bash
cd backend

# Tạo môi trường ảo (virtual environment)
python -m venv venv

# Kích hoạt môi trường
source venv/bin/activate   # Windows: venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Tạo và cập nhật database
cd src
python manage.py makemigrations
python manage.py migrate

# Chạy server
python manage.py runserver_plus --cert-file cert.crt --key-file cert.key
```

### Chạy Frontend
```bash
cd frontend

# Cài dependencies
npm install

# Chạy development server
npm run dev
```

### Chạy test report 
```bash
### BACKEND DJANGO
# Cài dependencies
pip install -r requirements.txt

# Chạy test report
pytest -q --cov=src --cov-report=term-missing


### FRONTEND REACTJS VITE
# Cài dependencies
npm install

# Chạy test
npm run test:run
npm run test:run -- --reporter=verbose 2>&1 
npm run test 
npm run test -- --coverage
```

### Truy cập hệ thống
- Frontend: http://localhost:5173/
- Backend API: https://localhost:8000/

## Demo
[Demo sản phẩm](./docs/demo.md) 
