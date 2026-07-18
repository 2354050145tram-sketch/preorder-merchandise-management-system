# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)  
## Preorder merchandise management system


---


# 1. Giới thiệu


## 1.1 Mục đích
Hệ thống quản lý pre-order merchandise được xây dựng để admin cũng là chủ shop quản lý quy trình kinh doanh pre-order merchandise của các tựa game, các bộ phim hay hoạt hình ở nước ngoài. Thay thế phương pháp thủ công như Excel, Notion bằng một hệ thống quản lý tập trung nhằm nâng cao hiệu suất, giảm sai sót và tiết kiệm thời gian trong quá trình vận hành.


Hệ thống sẽ giúp khách hàng trong việc đặt hàng, thanh toán, theo dõi đơn hàng. Với admin, hệ thống hỗ trợ việc quản lý các sản phẩm pre-order, đơn hàng pre-order, các sản phẩm tồn kho, thông báo tiến độ đến khách hàng, theo dõi đơn hàng và báo cáo doanh thu. Góp phần nâng cao hiệu quả hoạt động và chất lượng của shop.


## 1.2 Phạm vi
Hệ thống bao gồm các chức năng phục vụ cho hai nhóm người dùng chính: khách hàng và admin. Cho phép khách hàng thao tác liên quan đến sản phẩm như xem thông tin sản phẩm, đặt hàng và theo dõi tiến độ. Hỗ trợ admin quản lý sản phẩm có sẵn, quản lý các đợt pre-order, đơn hàng, thanh toán, khách hàng, cập nhật tiến độ qua thông báo tự động, tồn kho sau khi hàng về và xem các báo cáo thống kê doanh thu.


## 1.3 Đối tượng sử dụng
Admin (cũng là chủ cửa hàng).  
Khách hàng.


## 1.4 Các thuật ngữ, từ ngữ viết tắt


|   Term   |          Meaning           |
|----------|----------------------------|
|   Admin  |  Quản trị viên             |
|  Pre-order  |  Hàng đặt trước             |


---


# 2. Overall Description


## 2.1 Product Perspective
Hệ thống là web độc lập được phát triển bằng Flask. Người dùng truy cập và sử dụng thông qua trình duyệt web.


Được xây dựng theo kiến trúc Client–Server. Phía server sẽ chịu trách nhiệm xử lý logic nghiệp vụ và giao tiếp với cơ sở dữ liệu; phía client sẽ hiển thị giao diện và gửi yêu cầu đến server thông qua giao thức HTTP.


Hệ thống sử dụng hệ quản trị cơ sở dữ liệu MySQL để lưu trữ và quản lý dữ liệu.


Ứng dụng có tích hợp với các dịch vụ bên thứ ba nhằm mở rộng chức năng và đảm bảo tính bảo mật, bao gồm:


* Dịch vụ xác thực của Google, Facebook, Instagram để hỗ trợ đăng nhập tài khoản.


* Cổng thanh toán MoMo để xử lý giao dịch thanh toán.


Để vận hành, hệ thống yêu cầu môi trường server có cài đặt Python và các thư viện cần thiết của FLask. Người dùng cần có kết nối Internet để truy cập.


## 2.2 System Overview
Hệ thống được xây dựng hỗ trợ admin trong việc quản lý sản phẩm có sẵn, sản phẩm có đợt pre-order, khách hàng, đơn hàng và tồn kho một cách hiệu quả, thay thế các phương pháp quản lý thủ công của các shop order hiện tại. Cung cấp các chức năng hỗ trợ như báo cáo thống kê, nạp, rút tiền ví ảo, cập nhật tiến độ hàng.


Hệ thống phục vụ các đối tượng người dùng bao gồm quản trị viên cũng là chủ shop và khách hàng. Mỗi nhóm người dùng sẽ được cung cấp các chức năng phù hợp với vai trò của mình.


Các chức năng chính của hệ thống bao gồm:


* Khách hàng đặt hàng các sản phẩm có sẵn tại shop hoặc các sản phẩm có đợt pre-order, theo dõi tiến độ đơn hàng.


* Quản trị viên quản lý sản phẩm, đơn hàng, khách hàng, tồn kho và xem hoặc xuất báo cáo thống kê khi cần.


Hệ thống sử dụng cơ chế xác thực và phân quyền người dùng nhằm bảo mật và kiểm soát quyền truy cập theo vai trò.




## 2.3 User Roles


| Role | Description |
|------|------------|
| Admin | Quản lý toàn bộ hoạt động của hệ thống. Có quyền truy cập cao nhất trong hệ thống. |
| Khách hàng | Đặt hàng trực tuyến các sản phẩm có sẵn, sản phẩm pre-order, thanh toán online,theo dõi tiến độ,  quản lý thông tin cá nhân của mình. |




## 2.4 Assumptions & Constraints


### Assumptions
* Người dùng có kết nối Internet ổn định.
* Server được cấu hình đúng và hoạt động liên tục trong quá trình sử dụng.
* Người dùng biết sử dụng trình duyệt web.
* Dữ liệu được nhập vào hệ thống là chính xác và hợp lệ.
* Các dịch vụ hoạt động bình thường.


### Constraints
* Hệ thống phải được phát triển bằng ngôn ngữ Python và framework Flask.
* Hệ thống phải sử dụng hệ quản trị cơ sở dữ liệu MySQL.
* Phạm vi dự án chỉ bao gồm web.
* Hệ thống phải hoạt động theo mô hình Client–Server và sử dụng giao thức HTTPS khi triển khai.
* Người dùng phù hợp mới được truy cập các chức năng tương ứng.
---


# 3. System Features (Functional Requirements)


#### Nhóm 1: Tất cả người dùng
* FR-01: Đăng nhập tài khoản
  + Hệ thống cho phép người dùng đăng nhập để sử dụng các tính năng.


#### Nhóm 2: Khách hàng
* FR-02: Đăng ký tài khoản
    + Hệ thống cho phép khách hàng tạo tài khoản mới để sử dụng các chức năng.
* FR-03: Đặt hàng sản phẩm
  + Hệ thống cho phép khách hàng đặt hàng sản phẩm có sẵn hoặc sản phẩm có đợt pre-order.
* FR-04: Thanh toán trực tuyến
  + Hệ thống cho phép khách hàng thanh toán trực tuyến thông qua các cổng thanh toán của bên thứ ba.
* FR-05 Xem biên lai
  + Hệ thống cho phép học viên xem biên lai điện tử sau khi đã thanh toán thành công.
* FR-06: Xem tiến độ hàng hóa
  + Hệ thống hiển thị tiến độ sản phẩm pre-order mà khách đã đặt mua.


#### Nhóm 3: Admin
* FR-07: Quản lý người dùng và phân quyền
  + Hệ thống cho phép admin tạo mới tài khoản, cập nhật thông tin và theo dõi trạng thái hoạt động của người dùng.
  + Hệ thống cho phép admin phân quyền người dùng bằng cách gán hoặc thay đổi vai trò cho tài khoản người dùng.
* FR-08: Quản lý sản phẩm
  + Hệ thống cho phép admin xem, thêm, sửa, xóa và theo dõi các sản phẩm.
* FR-09: Quản lý đơn hàng
  + Hệ thống cho phép admin xem, xác nhận, cập nhật trạng thái và theo dõi các đơn hàng.
  + Hệ thống cho phép admin kiểm tra trạng thái thanh toán và xem biên lai thanh toán của từng đơn hàng.
* FR-10: Quản lý khách hàng
  + Hệ thống cho phép admin xem danh sách khách hàng, tìm kiếm, xem thông tin chi tiết và lịch sử mua hàng của khách hàng.
* FR-11: Quản lý tiến độ
  + Hệ thống cho phép admin cập nhật tiến độ của các đợt pre-order.
  + Khi cập nhật tiến độ, hệ thống tự động gửi thông báo đến tất cả khách hàng đã đặt mua sản phẩm thuộc đợt pre-order.
* FR-12: Quản lý tồn kho
  + Hệ thống cho phép admin quản lý các sản phẩm tồn kho sau khi hàng được giao từ nhà cung cấp.
  + Hệ thống cập nhật số lượng hàng dư, thông tin và trạng thái của các sản phẩm tồn kho để tiếp tục bán dưới dạng sản phẩm có sẵn.
* FR-13: Xem báo cáo thống kê
  + Hệ thống cho phép admin xem báo cáo thống kê theo tháng, in và xuất báo cáo.
---


# 4. External Interface Requirements


## 4.1 User Interface
Phương thúc tương tác: Khi sử dụng người dùng thao tác bằng chuột, bàn phím hoặc cảm ứng. Tương tác thông qua menu, nút bấm, biểu mẫu.  
Loại giao diện: Giao diện Web  
Giao diện:
  * Quản trị:
    + Admin: Đăng nhập quản trị; Quản lý sản phẩm; Quản lý đơn hàng; Quản lý tồn kho; Quản lý khách hàng; Báo cáo, thống kê.
  * Người dùng:
    + Khách hàng: Trang chủ; Đăng ký; Đăng nhập; Sản phẩm, thanh toán; Xem tiến độ.
## 4.2 Hardware Interface
 Yêu cầu: thiết bị có khả năng kết nối Internet.  
 Thiết bị: máy tính, laptop, điện thoại thông minh.
## 4.3 Software Interface
- Môi trường server: có cài đặt Python và Flask.  
- Hệ quản trị cơ sở dữ liệu: MySQL.  
- Trình duyệt hỗ trợ: Google Chrome, Microsoft Edge,...  
- Dịch vụ tích hợp:
  + Dịch vụ xác thực đăng nhập (OAuth 2.0).
  + Dịch vụ xử lý thanh toán trực tuyến (MoMo).
---


# 5. Non-functional Requirements
NFR-01: Yêu cầu giao diện
* Giao diện dễ sử dụng và phải đảm bảo tính đồng bộ trên tất cả các trang hệ thống.
* Các thành phần giao diện phải được thiết kế nhất quán giữa các chức năng.
* Hệ thống phải hiển thị thông báo lỗi khi nhập sai dữ liệu.


NFR-02: Bảo mật
* Hệ thống phải yêu cầu xác thực người dùng trước khi truy cập các chức năng quản lý.
* Mật khẩu người dùng phải có ít nhất 6 kí tự. Phải được băm trước khi lưu trữ trong cơ sở dữ liệu.


NFR-03: Hiệu năng
* Hệ thống phải hỗ trợ tối thiếu 100 người dùng truy cập đồng thời mà không xảy ra lỗi nghiêm trọng.
* Thời gian phản hồi trung bình cho mỗi yêu cầu không vượt quá 3 giây.


NFR-04: Độ tin cậy & khả năng bảo trì
* Hệ thống phải đảm bảo không mất dữ liệu khi xảy ra sự cố đột ngột.
* Hệ thống phải có cơ chế sao lưu cơ sở dữ liệu định kỳ.
* Cập nhật hệ thống không được làm ảnh hưởng đến các chức năng trước đó.
---


# 6. Business Rules
Business Rules mô tả các quy tắc nghiệp vụ mà hệ thống phải tuân thủ trong quá trình vận hành.  


## 6.1. User Account Management  
BR-01: Khách hàng được phép tự tạo tài khoản.  
BR-02: Khách hàng được phép chỉnh sửa thông tin cá nhân của mình.  
BR-03: Người dùng được phép xuất dữ liệu mà họ có quyền truy cập ra file.    
BR-04: Người dùng có quyền đổi mật khẩu của mình. Admin có quyền hỗ trợ khi người dùng gặp rắc rối.  


## 6.2. Product Management  
BR-05: Mỗi sản phẩm phải có mã sản phẩm duy .  
BR-06: Mỗi sản phẩm phải thuộc ít nhất 1 danh mục.  
BR-07: Giá bán của sản phẩm phải lớn hơn 0.    
BR-08: Không cho phép xóa sản phẩm.  
BR-09: Sản phẩm bán sẵn được hình thành từ số lượng hàng dư sau khi hoàn thành đợt pre-order hoặc các nguồn hàng hợp lệ khác do admin cập nhật.


## 6.3. Pre-order Management
BR-10: Đối với sản phẩm pre-order, Admin phải có thời gian mở và thời gian kết thúc.  
BR-11: Sau khi kết thúc thời gian pre-order, không cho phép khách hàng đặt thêm đơn hàng.  
BR-12: Sản phẩm không được trùng thời gian pre-order.    
BR-14: Admin cập nhật tiến độ của đợt pre-order theo từng giai đoạn.  
BR-15: Khi tiến độ được cập nhật, hệ thống tự động gửi thông báo đến tất cả khách hàng đã đặt sản phẩm.  
BR-16: Khách hàng chỉ được theo dõi tiến độ của các đợt pre-order mà mình đã tham gia.  
BR-17: Trạng thái pre-order bao gồm:
  * Đặt hàng thành công.  
  * Đã hủy.  


BR-18: Trạng thái tiến độ bao gồm:
  * Chưa mở.  
  * Đang mở.  
  * Đã đóng.
  * Cập nhật lần 1.
  * Cập nhật lần 2.
  * Cập nhật lần 3.
  * Hàng về kho Trung.
  * Hàng về kho Việt.


## 6.3. Order Management  
BR-19: Mỗi đơn hàng phải có một mã đơn hàng duy nhất.  
BR-20: Đơn hàng chỉ được phép hủy khi chưa chuyển sang trạng thái giao hàng.  


## 6.4. Payment
BR-21: Đơn hàng chỉ thành công sau khi hệ thống được ghi nhận thanh toán thành công.  
BR-22: Một đơn hàng chỉ có một trạng thái thanh toán tại một thời điểm.  
BR-23: Quy định thanh toán:
  * Khách hàng mới bắt buộc thanh toán 100% giá trị đơn hàng.  
  * Khách hàng cũ có thể cọc 70% giá trị đơn hàng và hoàn cọc trong 45 ngày.        


BR-24: Trạng thái thanh toán gồm:  
  * Thanh toán thành công.  
  * Thanh toán thất bại.  
  * Đã cọc ___ VND.
  * Chờ xử lý.    
 
## 6.5. Inventory Management  
BR-25: Sau khi hoàn tất việc giao hàng cho khách, số lượng hàng dư có thể được chuyển sang trạng thái hàng sẵn để tiếp tục kinh doanh.  
BR-26: Mọi thay đổi về số lượng hàng sẵn phải được hệ thống ghi nhận và cập nhật vào tồn kho.  


## 6.6. Shipping
BR-27: Đơn hàng chỉ được chuyển sang trạng thái vận chuyển sau khi đã được xác nhận thanh toán.  
BR-28: Mỗi đơn hàng chỉ có một trạng thái vận chuyển tại một thời điểm.  
BR-29: Trạng thái cho hàng sẵn bao gồm:
  * Chờ xác nhận.  
  * Chờ lấy hàng.
  * Chờ giao hàng.
  * Giao hàng thành công.
  * Giao hàng thất bại.
  * Đã hủy.  


BR-30: Trạng thái cho hàng pre-order bao gồm:
  * Thu phụ phí.    
  * Chờ giao hàng.
  * Giao hàng thành công.
  * Giao hàng thất bại.  


## 6.7. Báo cáo (Reporting)  
BR-33: Hệ thống cung cấp báo cáo thống kê tháng, năm theo:  
 * Tổng doanh thu.
 * Tổng sản phẩm.  
 * Tổng đơn hàng.  
 * Tổng khách hàng.  
---


# 7. Data Requirements


## 7.1 Data Entities
---


## 7.2 Entity Attributes
---


## 7.3 Relationships                                            
---


## 7.4 Data Constraints
---


# 8. System Models
## 8.1 Use Case Diagram
---


## 8.2 Use Case Specification
---


# 9. Wireframes UI
### 9.1 UI About Me
![UI About Me](./screenshots/SRS%20resources/about-me.png)

### 9.2 UI Đăng nhập
![UI Đăng nhập](./screenshots/SRS%20resources/dang-nhap.png)

### 9.3 UI Đăng ký
![UI Đăng ký](./screenshots/SRS%20resources/dang-ky.png)

### 9.4 UI Quản lý sản phẩm
![UI Quản lý sản phẩm](./screenshots/SRS%20resources/quan-ly-san-pham.png)

### 9.5 UI Quản lý Pre-order
![UI Quản lý Pre-order](./screenshots/SRS%20resources/quan-ly-pre-order.png)

### 9.6 UI Quản lý khách hàng
![UI Quản lý khách hàng](./screenshots/SRS%20resources/quan-ly-khach-hang.png)

### 9.7 UI Quản lý đơn hàng
![UI Quản lý đơn hàng](./screenshots/SRS%20resources/quan-ly-don-hang.png)

### 9.8 UI Quản lý tồn kho
![UI Quản lý tồn kho](./screenshots/SRS%20resources/quan-ly-kho.png)

### 9.9 UI Báo cáo
![UI Báo cáo](./screenshots/SRS%20resources/bao-cao.png)

### 9.10 UI Thông tin cá nhân khách hàng
![UI Thông tin cá nhân khách hàng](./screenshots/SRS%20resources/thong-tin-ca-nhan.png)

### 9.11 UI Trang chủ / Sản phẩm
![UI Trang chủ / Sản phẩm](./screenshots/SRS%20resources/trang-san-pham.png)

### 9.12 UI Giỏ hàng
![UI Giỏ hàng](./screenshots/SRS%20resources/gio-hang.png)

### 9.13 UI Thanh toán
![UI Thanh toán](./screenshots/SRS%20resources/thanh-toan.png)

### 9.14 UI Biên lai
![UI Thanh toán](./screenshots/SRS%20resources/bien-lai.png)

### 9.15 UI Thêm sản phẩm
![UI Thêm sản phẩm](./screenshots/SRS%20resources/them-san-pham.png)

### 9.16 UI Chi tiết sản phẩm
![UI Chi tiết sản phẩm](./screenshots/SRS%20resources/chi-tiet-san-pham.png)

### 9.17 UI Chi tiết khách hàng
![UI Chi tiết khách hàng](./screenshots/SRS%20resources/chi-tiet-khach-hang.png)

### 9.18 UI Thêm Pre-order
![UI Thêm Pre-order](./screenshots/SRS%20resources/them-pre-order.png)

### 9.19 UI Nhập hàng
![UI Nhập hàng](./screenshots/SRS%20resources/nhap-hang.png)

### 9.20 UI Nạp Ví ảo
![UI Nạp Ví ảo](./screenshots/SRS%20resources/nap-vi-ao.png)

### 9.21 UI Rút Ví ảo
![UI Rút Ví ảo](./screenshots/SRS%20resources/rut-vi-ao.png)

### 9.22 UI Lịch sử giao dịch
![UI Lịch sử giao dịch](./screenshots/SRS%20resources/lich-su-giao-dich.png)