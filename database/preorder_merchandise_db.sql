CREATE DATABASE preorder_merchandise_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
USE preorder_merchandise_db;

CREATE TABLE `roles` (
    `role_id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `active` TINYINT(1) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`role_id`),
    CONSTRAINT `uk_role_name`
        UNIQUE (`name`)
);

CREATE TABLE `users` (
    `user_id` INT NOT NULL AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL,
    `username` VARCHAR(255) NOT NULL,
    `password` VARCHAR(255) NOT NULL,
    `provider` ENUM('LOCAL','GOOGLE','FACEBOOK','INSTAGRAM','X') NOT NULL,
    `provider_user_id` VARCHAR(255),
    `role_id` INT NOT NULL,
    `active` TINYINT(1) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`user_id`),
    CONSTRAINT `uk_user_email`
        UNIQUE (`email`),
    CONSTRAINT `uk_user_username`
        UNIQUE (`username`),
    CONSTRAINT `fk_user_role`
        FOREIGN KEY (`role_id`)
        REFERENCES `roles`(`role_id`)
);

CREATE TABLE `profiles` (
    `user_id` INT NOT NULL,
    `full_name` VARCHAR(255) NOT NULL,
    `avatar` VARCHAR(255),
    `phone_num` VARCHAR(10) NOT NULL,
    `address` VARCHAR(255) NOT NULL,
    `background_music` VARCHAR(255),
    PRIMARY KEY (`user_id`),
    CONSTRAINT `fk_profile_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users`(`user_id`)
        ON DELETE CASCADE
);

CREATE TABLE `products` (
    `product_id` INT NOT NULL AUTO_INCREMENT,
    `product_name` VARCHAR(255) NOT NULL,
    `price` DECIMAL(8,2) NOT NULL,
    `description` VARCHAR(255) NOT NULL,
    `image` VARCHAR(255) NOT NULL,
    `status` ENUM('PREORDER','IN_STOCK') NOT NULL,
    `active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL,
    `updated_at` DATETIME NOT NULL,
    PRIMARY KEY (`product_id`),
    CONSTRAINT `uk_product_name`
        UNIQUE (`product_name`)
);

CREATE TABLE `preorders` (
    `preorder_id` INT NOT NULL AUTO_INCREMENT,
    `product_id` INT NOT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `quantity_order` INT NOT NULL,
    `progress_status` ENUM('MỞ PREORDER', 'ĐÃ ĐẶT HÀNG', 'ĐANG SẢN XUẤT', 'ĐÃ VỀ KHO TRUNG QUỐC', 'ĐÃ VỀ KHO VIỆT NAM', 'ĐANG GÓI HÀNG', 'ĐÃ VẬN CHUYỂN', 'HOÀN THÀNH') NOT NULL,
    `progress_note` VARCHAR(255) NOT NULL,
    `active` TINYINT(1) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`preorder_id`),
    CONSTRAINT `fk_preorder_product`
        FOREIGN KEY (`product_id`)
        REFERENCES `products`(`product_id`)
);

CREATE TABLE `tags` (
    `tag_id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    `active` TINYINT(1) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`tag_id`),
    CONSTRAINT `uk_tag_name`
        UNIQUE (`name`)
);

CREATE TABLE `product_tags` (
    `product_id` INT NOT NULL,
    `tag_id` INT NOT NULL,
    PRIMARY KEY (`product_id`, `tag_id`),
    CONSTRAINT `fk_producttag_product`
        FOREIGN KEY (`product_id`)
        REFERENCES `products`(`product_id`)
        ON DELETE CASCADE,
    CONSTRAINT `fk_producttag_tag`
        FOREIGN KEY (`tag_id`)
        REFERENCES `tags`(`tag_id`)
        ON DELETE CASCADE
);

CREATE TABLE `orders` (
    `order_id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `order_date` DATE NOT NULL,
    `total_amount` DECIMAL(8,2) NOT NULL,
    `order_status` ENUM('CHỜ XÁC NHẬN','ĐÃ XÁC NHẬN','ĐANG XỬ LÝ','HOÀN THÀNH','ĐÃ HỦY') NOT NULL,
    `shipping_method` ENUM('TIÊU CHUẨN','GIAO NHANH') NOT NULL,
    `shipping_fee` DECIMAL(8,2) NOT NULL,
    `tracking_code` VARCHAR(255),
    `shipping_status` ENUM('ĐANG LẤY HÀNG','ĐANG GIAO HÀNG','ĐÃ GIAO','ĐÃ HỦY') NOT NULL,
    `active` TINYINT(1) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`order_id`),
    CONSTRAINT `fk_order_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users`(`user_id`)
);

CREATE TABLE `order_items` (
    `order_item_id` INT NOT NULL AUTO_INCREMENT,
    `order_id` INT NOT NULL,
    `product_id` INT NOT NULL,
    `preorder_id` INT NULL,
    `quantity` INT NOT NULL,
    `price` DECIMAL(8,2) NOT NULL,
    PRIMARY KEY (`order_item_id`),
    CONSTRAINT `fk_orderitem_order`
        FOREIGN KEY (`order_id`)
        REFERENCES `orders`(`order_id`),
    CONSTRAINT `fk_orderitem_product`
        FOREIGN KEY (`product_id`)
        REFERENCES `products`(`product_id`),
    CONSTRAINT `fk_orderitem_preorder`
        FOREIGN KEY (`preorder_id`)
        REFERENCES `preorders`(`preorder_id`)
);

CREATE TABLE `payments` (
    `payment_id` INT NOT NULL AUTO_INCREMENT,
    `order_id` INT NOT NULL,
    `amount` DECIMAL(8,2) NOT NULL,
    `payment_method` ENUM('MOMO') NOT NULL,
    `payment_status` ENUM('ĐANG THANH TOÁN','ĐÃ THANH TOÁN','ĐÃ HỦY','ĐÃ HOÀN TIỀN') NOT NULL,
    `transaction_id` VARCHAR(255) NOT NULL,
    `paid_at` DATETIME(6) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`payment_id`),
    CONSTRAINT `fk_payment_order`
        FOREIGN KEY (`order_id`)
        REFERENCES `orders`(`order_id`)
);

CREATE TABLE `inventories` (
    `inventory_id` INT NOT NULL AUTO_INCREMENT,
    `product_id` INT NOT NULL,
    `quantity` INT NOT NULL,
    `price` DECIMAL(8,2) NOT NULL,
    `status` ENUM('CÒN HÀNG','HẾT HÀNG','SẮP HẾT HÀNG') NOT NULL,
    `active` TINYINT(1) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`inventory_id`),
    CONSTRAINT `fk_inventory_product`
        FOREIGN KEY (`product_id`)
        REFERENCES `products`(`product_id`)
);

CREATE TABLE notifications (
    `notification_id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `preorder_id` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `message` VARCHAR(255) NOT NULL,
    `created_at` DATETIME(6) NOT NULL,
    PRIMARY KEY (`notification_id`),
    CONSTRAINT `fk_notification_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users`(`user_id`),
    CONSTRAINT `fk_notification_preorder`
        FOREIGN KEY (`preorder_id`)
        REFERENCES `preorders`(`preorder_id`)
);