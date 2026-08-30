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

## 7.1 Sơ đồ thực thể - liên kế (ERD)
![ERD](./screenshots/SRS%20resources/erd.png)

## 7.2 Data Entities

### Quản lý người dùng và phân quyền (User & Access Management) 
| Entity Name | Description                                     |
|-------------|-------------------------------------------------|
| `User`      | Đại diện cho người dùng                         |
| `Profile`   | Đại diện cho thông tin người dùng               |
| `Role`      | Đại diện cho vai trò người dùng                 |


### Quản lý sản phẩm và preorder (Product & Preorder Management)
| Entity Name | Description                                       |
|-------------|---------------------------------------------------|
| `Product`   | Đại diện cho sản phẩm                             |
| `PreOrder`  | Đại diện cho sản phẩm preorder                    |
| `Tag`       | Đại diện cho thẻ của sản phẩm                     |
| `Inventory` | Đại diện cho kho                                  |


### Quản lý đơn hàng và thanh toán (Order & Payment Management)
| Entity Name  | Description                                   |
|--------------|-----------------------------------------------|
| `Order`      | Đại diện cho đơn hàng                         |
| `OrderItem`  | Đại diện cho chi tiết sản phẩm trong đơn hàng |
| `Payment`    | Đại diện cho giao dịch thanh toán             |


### Quản lý thông báo (Notification Management)
| Entity Name      | Description                                      |
|------------------|--------------------------------------------------|
| 'Notification`   | Đại diện cho thông báo cập nhật tiến độ đơn hàng |

---

## 7.3 Entity Attributes

### 7.3.1. User

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `id`            | INT          |  PK  | AI               | Mã người dùng                                  |
| `email`         | VARCHAR(255) |      | UNIQUE, NOT NULL | Địa chỉ email                                  |
| `username`      | VARCHAR(100) |      | UNIQUE, NOT NULL | Tên đăng nhập                                  |
| `password`      | VARCHAR(255) |      |                  | Mật khẩu xác thực                              |
| `auth_provider` | ENUM         |      |                  | Kiểu login của tài khoản                       |
| `provider_id`   | VARCHAR(255) |      |                  | Mã xác thực từ nhà cung cấp dịch vụ bên thứ ba |
| `role_id`       | INT          |  FK  | NOT NULL         | Khóa ngoại tham chiếu tới bảng `Role`          |
| `active`        | BIT          |      |                  | Trạng thái hoạt động                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo tài khoản                        |
| `updated_at`    | DATETIME     |      |                  | Thời gian cập nhật tài khoản cho lần gần nhất  |


### 7.3.2. Profile

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `user_id`            | INT          |  PK,FK  | NOT NULL, UNIQUE               | Mã người dùng, khóa ngoại tham chiếu tới bảng user                                  |
| `full_name`         | VARCHAR(255) |      | NOT NULL | Tên đầy đủ của người                                  |
| `avatar`      | VARCHAR(255) |      |  | Ảnh đại diện người dùng            |
| `phone_num`      | VARCHAR(10) |      | NOT NULL                 | Số điện thoại người dùng                              |
| `address` | VARCHAR(255)         |      | NOT NULL                 | Địa chỉ của người dùng                       |
| `background_music`   | VARCHAR(255) |      |                  | Nhạc nền của người dùng |

---

### 7.3.3. Role

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `role_id`            | INT          |  PK | AI               | Mã vai trò                                  |
| `name`         | VARCHAR(255) |      | NOT NULL, UNIQUE | Vai trò                                  |
| `active`        | BIT          |      |                  | Trạng thái hoạt động                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |
| `updated_at`    | DATETIME     |      |                  | Thời gian cập nhật gần nhất  |


### 7.3.4. Product

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `product_id`            | INT          |  PK | AI               | Mã vai trò                                  |
| `product_name`         | VARCHAR(255) |      | NOT NULL, UNIQUE | Tên sản phẩm                                  |
| `price`            | DECIMAL(8,2)          |   | NOT NULL               |  Giá của sản phẩm                                  |
| `description`         | VARCHAR(255) |      | NOT NULL | Mô tả về sản phẩm                                  |
| `image`            | VARCHAR(255)          |   | NOT NULL               | Hình ảnh sản phẩm                                  |
| `status`         | ENUM |      | NOT NULL, UNIQUE | Trạng thái sản phẩm: Pre-order hoặc In Stock                                  |
| `active`        | BIT          |      |                  | Trạng thái hoạt động                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |
| `updated_at`    | DATETIME     |      |                  | Thời gian cập nhật gần nhất  |

---

### 7.3.5. PreOrder

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `preorder_id`            | INT          |  PK | AI               | Mã preorder                                  |
| `product_id`         | INT | FK     | NOT NULL | Khóa ngoại tham chiếu tới bảng product                                  |
| `started_date`            | DATETIME          |   | NOT NULL               |  Thời gian đặt hàng trước của sản phẩm                                  |
| `end_date`         | DATETIME          |   | NOT NULL               |  Thời hạn đặt hàng trước của sản phẩm                                  |
| `quantity_order`            | INT          |   | NOT NULL               | Số lượng sản phẩm cần order                                  |
| `progress_status`         | ENUM |      | NOT NULL | Trạng thái tiến độ của đợt pre-order                                  |
| `progress_note`         | VARCHAR(255) |      | NOT NULL | Nội dung cập nhật tiến độ                                  |
| `active`        | BIT          |      |                  | Trạng thái hoạt động                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |
| `updated_at`    | DATETIME     |      |                  | Thời gian cập nhật gần nhất  |

---

### 7.3.6. Tag

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `tag_id`            | INT          |  PK | AI               | Mã thẻ                                  |
| `name`         | VARCHAR(255) |      | NOT NULL, UNIQUE | Tên thẻ                                  |
| `active`        | BIT          |      |                  | Trạng thái hoạt động                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |
| `updated_at`    | DATETIME     |      |                  | Thời gian cập nhật gần nhất  |

---

### 7.3.7. ProductTag

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `tag_id`            | INT          |  FK | NOT NULL               | Khóa ngoại tham chiếu tới bảng tag                                  |
| `product_id`         | INT |  FK  | NOT NULL | Khóa ngoại tham chiếu tới bảng product                                  |

---

### 7.3.8. Order

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `order_id`            | INT          |  PK | AI               | Mã preorder                                  |
| `user_id`         | INT | FK     | NOT NULL | Khóa ngoại tham chiếu tới bảng product                                  |
| `order_date`            | DATETIME          |   | NOT NULL               |  Thời gian đặt hàng                                  |
| `total_amount`         | DECIMAL(8,2)          |   | NOT NULL               |  Tổng giá trị đơn hàng                                  |
| `payment_status`            | ENUM          |   | NOT NULL               | Trạng thái thanh toán của đơn hàng                                  |
| `order_status`         | ENUM |      | NOT NULL | Trạng thái xử lý của đơn hàng                                  |
| `shipping_method`            | ENUM          |   | NOT NULL               |  Phương thức vận chuyển                                  |
| `shipping_fee`         | DECIMAL(8,2)          |   | NOT NULL               |  Phí vận chuyển của đơn hàng                                  |
| `tracking_code`            | VARCHAR(255)          |   | NOT NULL               | Mã vận đơn                                  |
| `shipping_status`         | ENUM |      | NOT NULL | Trạng thái vận chuyển của đơn hàng                                  |
| `active`        | BIT          |      |                  | Trạng thái hoạt động                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |

---

### 7.3.9. OrderItem

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `order_item_id`            | INT          |  PK | AI               | Mã chi tiết đơn hàng                                  |
| `order_id`         | INT | FK     | NOT NULL | Khóa ngoại tham chiếu tới bảng order                                  |
| `product_id`            | INT          | FK  | NOT NULL               |  Khóa ngoại tham chiếu tới bảng product                                  |
| `quantity`         | INT          |   | NOT NULL               |  Số lượng sản phẩm trong đơn hàng                                  |
| `price`            | DECIMAL(8,2)          |   | NOT NULL               | Đơn giá của sản phẩm                                  |

---

### 7.3.10. Payment

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `payment_id`            | INT          |  PK | AI               | Mã preorder                                  |
| `order_id`         | INT | FK     | NOT NULL | Khóa ngoại tham chiếu tới bảng order                                  |
| `amount`            | DECIMAL(8,2)          |   | NOT NULL               |  Số tiền thanh toán                                  |
| `payment_method`         | ENUM          |   | NOT NULL               |  Phương thức thanh toán                                  |
| `payment_status`            | ENUM          |   | NOT NULL               | Trạng thái thanh toán                                  |
| `transaction_id`         | VARCHAR(255) |      | NOT NULL | Định danh từ cổng thanh toán                                  |
| `paid_at`        | DATETIME          |      |                  | Thời điểm thanh toán thành công                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |

---

### 7.3.11. Inventory

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `inventory_id`            | INT          |  PK | AI               | Mã tồn kho                                  |
| `product_id`         | INT | FK     | NOT NULL | Khóa ngoại tham chiếu tới bảng product                                  |
| `quantity`            | INT          |   | NOT NULL               |  Số lượng hàng tồn kho                                  |
| `price`         | DECIMAL(8,2)          |   | NOT NULL               |  Giá tiền của sản phẩm tồn kho                                  |
| `status`            | VARCHAR(255)          |   | NOT NULL               | Trạng thái của sản phẩm tồn kho                                  |
| `active`        | BIT          |      |                  | Trạng thái hoạt động                           |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |
| `updated_at`    | DATETIME     |      |                  | Thời gian cập nhật gần nhất  |

---

### 7.3.12. Notification

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `notification_id`            | INT          |  PK | AI               | Mã preorder                                  |
| `user_id`         | INT | FK     | NOT NULL | Khóa ngoại tham chiếu tới bảng user                                  |
| `preorder_id`            | INT | FK     | NOT NULL | Khóa ngoại tham chiếu tới bảng preorder                                  |
| `title`         | VARCHAR(255)          |   | NOT NULL               |  Tiêu đề thông báo                                  |
| `message`            | VARCHAR(255)          |   | NOT NULL               | Nội dung cần thông bấo                                  |
| `created_at`    | DATETIME     |      |                  | Thời gian tạo                        |

---

### 7.3.13. UserNotification

| Tên cột         | Kiểu dữ liệu | Khóa | Ràng buộc        | Mô tả                                          |
| :-------------- | :----------- | :--: | :--------------- | :--------------------------------------------- |
| `user_id`            | INT          |  FK | NOT NULL               | Khóa ngoại tham chiếu tới bảng user                                  |
| `notification_id`         | INT |  FK  | NOT NULL | Khóa ngoại tham chiếu tới bảng notification                                  |
| `send_at`         | DATETIME     |      |                  | Thời gian gửi              |

---

## 7.4 Relationships
| A          | B                  | Relationship | Description                                                                                      |
|------------|--------------------|--------------|--------------------------------------------------------------------------------------------------|
| User       | Profile            | 1:1          | Một người dùng có một hồ sơ thông tin riêng biệt                                                  |
| Role       | User               | 1:N          | Một vai trò được gắn cho nhiều người dùng                                                        |
| Product    | PreOrder           | 1:N          | Một sản phẩm có thể có nhiều đợt pre-order                                                   |
| Product    | Tag                | N:N          | Một sản phẩm có nhiều thẻ và một thẻ được gắn cho nhiều sản phẩm                                 |
| User       | Order              | 1:N          | Một khách hàng có thể mua nhiều đơn hàng                                                        |
| Order      | OrderItem          | 1:N          | Một đơn hàng có thể chứa nhiều sản phẩm                                                        |
| Product    | OrderItem          | 1:N          | Một sản phẩm có thể xuất hiện nhiều lần trong chi tiết đơn hàng                                     |
| PreOrder   | OrderItem          | 1:N          | Một đợt preorder có thể có nhiều sản phẩm được đặt mua trong các đơn hàng                        |
| Order      | Payment            | 1:N          | Một đơn hàng có thể có nhiều giao dịch thanh toán                                                        |
| Product    | Inventory          | 1:N          | Một sản phẩm có thể có nhiều bản ghi tồn kho                                                     |
| User       | Notification       | N:N          | Một khách hàng có thể nhận nhiều thông báo và một thông báo có thể gửi nhiều khách hàng                    |
| PreOrder   | Notification       | 1:N          | Một đợt pre-order có thể có nhiều thông báo đến cho khách hàng                                      |
---


# 8. System Models
## 8.1 Use Case Diagram
![UseCase](./screenshots/SRS%20resources/usecase.png)
---


## 8.2 Use Case Specification
### 8.2.1. Đặt hàng
| Field | Content |
|---|---|
| Usecase ID | UC-01 |
| Usecase Name | Đặt hàng |
| Actor | Khách hàng |
| Description | Cho phép khách hàng đặt hàng trực tuyến |
| Pre-Condition(s) |- Khách hàng đăng nhập thành công<br>- Hệ thống hoạt động bình thường<br>- Sản phẩm còn tồn tại |
| Post-Condition(s) | - Đơn hàng được ghi nhận<br>- Số lượng đơn hàng tăng lên đối với preorder hoặc giảm xuống với sản phẩm có sẵn<br>- Gửi thông báo về email người dùng |
| Main Flow | <ol><li>Khách hàng mở trang web để xem sản phẩm.</li><li>Khách hàng chọn sản phẩm.</li><li>Hệ thống hiển thị thông tin chi tiết sản phẩm.</li><li>Khách hàng bấm đặt hàng hoặc thêm vào giỏ hàng và chọn loại sản phẩm cần mua.</li><li>Hệ thống tạo bản ghi với trạng thái “đang xử lý”.</li><li>Hệ thống yêu cầu khách hàng thanh toán.</li><li>Khách hàng chọn phương thức thanh toán toàn bộ theo quy định mua hàng.</li><li>Khách hàng nhấn “Thanh toán”.</li><li>Hệ thống chuyển hướng đến cổng thanh toán với số tiền và địa chỉ nhận hàng.</li><li>Khách hàng thực hiện thanh toán.</li><li>Cổng thanh toán trả về kết quả thành công cho hệ thống.</li><li>Hệ thống xử lý dữ liệu và cập nhật trạng thái "Thành công".</li><li>Hệ thống thông báo thành công ra màn hình</li><li>Hệ thống gửi mail thông báo cho khách hàng.</li></ol> |
| Alternative Flow | 10a. Khách hàng chọn phương thức thanh toán “Cọc 70%” với đơn hàng preorder cho khách hàng mua hàng từ lần thứu 2. <br> *Usecase tiếp tục từ bước 8 đến 14.* <br> 12a. Hệ thống xử lý dữ liệu: <ul><li> Cập nhật trạng thái đăng ký “Thành công - cọc 70%”.</li><li> Tạo bản ghi trạng thái thanh toán “Thành công”. <br><br> 10a. Khách hàng nhấn "Back" hoặc không thanh toán trong ngày. <ul><li> Hệ thống xóa bản ghi đặt hàng -> *usecase kết thúc*.</li><li> Khách hàng chọn "Thanh toán" -> *quay lại bước 9*.</li></ul> |
| Exception Flow | 4a. Hệ thống thông báo sản phẩm hết hạn preorder hoặc hết hàng có sẵn và không cho phép khách hàng đặt hàng -> *quay lại bước 2 usecase*. <br> 4b. Hệ thống thông báo khách hàng đặt quá số lượng đối với hàng có sẵn và yêu cầu khách hàng nhập lại số lượng -> *quay lại bước 2 usecase*. <br> 4c. Hệ thống yêu cầu khách hàng đăng nhập trước khi thực hiện đặt hàng -> *quay lại bước 2 usecase*.|

---

### 8.2.2 Thanh toán
| Field | Content |
|---|---|
| Usecase ID | UC-02 |
| Usecase Name | Thanh toán đơn hàng |
| Actor | Khách hàng, Cổng thanh toán bên thứ 3 |
| Description | Khách hàng thanh toán đơn hàng trực tiếp qua kênh thứ 3 |
| Pre-Condition(s) | Khách hàng đăng nhập vào hệ thống <br>Khách hàng bấm mua hàng và thanh toán |
| Post-Condition(s) | Khách hàng thanh toán đơn hàng thành công <br>Khách hàng xem được tiến độ đơn hàng |
| Main Flow | <ol><li>Khách hàng nhấn "Thanh toán" </li><li>Hệ thống truy xuất dữ liệu và hiển thị chi tiết đơn hàng</li><li>Khách hàng chọn phương thức thanh toán "Toàn bộ" và "Thanh toán" </li><li>Hệ thống chuyển hướng sang cổng thanh toán</li><li>Khách hàng thanh toán qua cổng thanh toán</li><li>Hệ thống kiểm tra tình trạng thanh toán được gửi về từ cổng thanh toán bên thứ ba</li><li>Hệ thống cập nhật trạng thái thanh toán</li><li>Hệ thống cập nhật trạng thái đơn hàng |
| Alternative Flow | 3a. Khách hàng chọn phương thức thanh toán "Cọc"<br>3b. Hệ thống kiểm tra số lần mua hàng<br>*Usecase tiếp tục từ bước 4 đến 8* <br><br>5a. Nếu học viên không thanh toán mà bấm nút "Quay lại" trên cổng thanh toán<br>5b. Cổng thanh toán trả kết quả "Đã hủy" về hệ thống<br>5c. Hệ thống hiển thị thông báo: "Giao dịch đã bị hủy", sau đó quay lại màn hình chọn phương thức thanh toán<br><br> 6a. Nếu số dư không đủ hoặc thẻ bị lỗi, cổng thanh toán trả về kết quả thất bại<br> 6b. Hệ thống hiển thị thông báo: "Thanh toán thất bại. Vui lòng kiểm tra lại số dư hoặc thử phương thức thanh toán khác". Hệ thống quay lại màn hình chọn phương thức thanh toán |
| Exception Flow | 6c. Nếu xảy ra sự cố mạng, cổng thanh toán không phản hồi hoặc hết thời gian giao dịch mà chưa thanh toán<br> 6d. Hệ thống hiển thị thông báo lỗi: "Giao dịch quá thời gian xử lý". Hệ thống quay về màn hình chọn chức năng thanh toán. |

---                                                                                      

### 8.2.3. Quản lý sản phẩm
| Field | Content |
|---|---|
| Usecase ID | UC-03 |
| Usecase Name | Quản lý sản phẩm |
| Actor | Admin |
| Description | Cho phép admin thực hiện các thao tác quản lý sản phẩm merchandise trên hệ thống |
| Pre-Condition(s) |- Admin đăng nhập thành công vào hệ thống <br>- Hệ thống hoạt động bình thường. |
| Post-Condition(s) | Thông tin sản phẩm được thêm mới, cập nhật hoặc xóa thành công và lưu vào cơ sở dữ liệu |
| Main Flow | <ol><li>Admin truy cập chức năng Sản phẩm</b>.</li><li>Hệ thống hiển thị danh sách sản phẩm hiện có.</li><li>Admin chọn chức năng "Thêm", "Chỉnh sửa"</li><li>Nếu thêm hoặc chỉnh sửa, hệ thống hiển thị trang tương ứng.</li><li>Admin nhập hoặc cập nhật thông tin sản phẩm</li><li>Admin chọn "Lưu"</li><li>Hệ thống kiểm tra tính hợp lệ của dữ liệu</li><li>Hệ thống lưu thông tin sản phẩm vào cơ sở dữ liệu |
| Alternative Flow | 3a. Admin chọn "Xóa"<br>3b. Hệ thống yêu cầu xác nhận xóa</br>3c. Admin xác nhận<br>3d. Hệ thống cập nhật trạng thái sản phẩm thành "Không hoạt động"<br>5a. Admin chọn "Hủy" khi đang thêm hoặc chỉnh sửa<br>5b. Hệ thống yêu cầu xác nhận hủy</br>5c. Admin xác nhận<br>5d. Hệ thống không lưu thay đổi và quay về danh sách sản phẩm |
| Exception Flow | 7a. Hệ thống kiểm tra tên sản phẩm bị trùng, hiển thị thông báo "Sản phẩm đã tồn tại" -> quay lại usecase bước 5. <br>7b. Hệ thống kiểm tra dữ liệu bắt buộc bị thiếu, hiển thị thông báo "Vui lòng nhập___" -> quay lại bước 5 |


### 8.2.4 Cập nhật tiến độ
| Field | Content |
|---|---|
| Usecase ID | UC-04 |
| Usecase Name | Cập nhật tiến độ |
| Actor | Admin |
| Description | Cho phép Admin cập nhật tiến độ và tự động gửi thông báo đến tất cả khách hàng đã đặt |
| Pre-Condition(s) | Admin đã đăng nhập hệ thống<br>Đợt pre-order đã được tạo |
| Post-Condition(s) | Tiến độ của đợt pre-order được cập nhật thành công và thông báo được gửi đến khách hàng đã đặt sản phẩm |
| Main Flow | <ol><li>Admin truy cập chức năng "Pre-order"</li><li>Hệ thống hiển thị danh sách các đợt pre-order</li><li>Admin chọn một đợt pre-order</li><li>Hệ thống hiển thị thông tin chi tiết của đợt pre-order</li><li>Quản trị viên chọn chức năng "Cập nhật tiến độ"</li><li>Hệ thống hiển thị trạng thái hiện tại và trang cập nhật</li><li>Admin chọn trạng thái tiến độ và nhập nội dung </li><li>Quản trị viên chọn "Gửi"</li><li>Hệ thống cập nhật tiến độ vào cơ sở dữ liệu</li><li>Hệ thống tự động gửi thông báo đến các khách hàng đã đặt sản phẩm|
| Alternative Flow | 7a. Quản trị viên chỉ thay đổi trạng thái tiến độ mà không nhập ghi chú<br>7b. Hệ thống vẫn cho phép lưu tiến độ<br>7c. Hệ thống gửi thông báo chỉ chứa trạng thái mới.<br><br>8a. Quản trị viên chọn "Hủy"<br>8b. Hệ thống yêu cầu xác nhận hủy.</br>8c. Admin xác nhận.<br>8d. Hệ thống không lưu thay đổi và quay về danh sách pre-order|
| Exception Flow | 9a. Hệ thống kiểm tra trạng thái tiến độ không hợp lệ, hiển thị thông báo "Trạng thái tiến độ không hợp lệ", quay lại bước 7 |
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