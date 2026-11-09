-- Thiết lập mã hóa và tối ưu thực thi
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Chạy file khởi tạo bảng và seed dữ liệu của users (file gộp của bạn)
SOURCE ./users.sql;

-- 2. Chạy tiếp các file của bảng khác (nếu có, theo thứ tự từ cha đến con)
-- SOURCE ./02_profiles.sql;
-- SOURCE ./03_posts.sql;

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'Khởi tạo database và dữ liệu mẫu thành công!' AS message;