CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt hash',
    role ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER',
    status ENUM('ACTIVE', 'LOCKED') NOT NULL DEFAULT 'ACTIVE',
    locked_until DATETIME NULL,
    last_seen DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO users (email, username, password_hash, role, status, locked_until, last_seen) VALUES
-- 1 Tài khoản Admin
('admin.gameconnect@example.com', 'admin_boss', '$2b$12$e8Y...sample_bcrypt_hash_admin...', 'ADMIN', 'ACTIVE', NULL, NOW()),

-- 20 Game thủ mẫu
('gammer01@example.com', 'vuxuanbach', '$2b$12$e8Y...sample_bcrypt_hash_1...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer02@example.com', 'huyptg', '$2b$12$e8Y...sample_bcrypt_hash_2...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer03@example.com', 'pro_gamer99', '$2b$12$e8Y...sample_bcrypt_hash_3...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer04@example.com', 'thanh_an', '$2b$12$e8Y...sample_bcrypt_hash_4...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer05@example.com', 'minh_duc', '$2b$12$e8Y...sample_bcrypt_hash_5...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer06@example.com', 'quoc_trung', '$2b$12$e8Y...sample_bcrypt_hash_6...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer07@example.com', 'gia_huy', '$2b$12$e8Y...sample_bcrypt_hash_7...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer08@example.com', 'tuan_anh', '$2b$12$e8Y...sample_bcrypt_hash_8...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer09@example.com', 'hoang_trung', '$2b$12$e8Y...sample_bcrypt_hash_9...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer10@example.com', 'nhat_anh', '$2b$12$e8Y...sample_bcrypt_hash_10...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer11@example.com', 'duc_anh_hn', '$2b$12$e8Y...sample_bcrypt_hash_11...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer12@example.com', 'van_cuong', '$2b$12$e8Y...sample_bcrypt_hash_12...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer13@example.com', 'xuan_hung', '$2b$12$e8Y...sample_bcrypt_hash_13...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer14@example.com', 'nhat_long', '$2b$12$e8Y...sample_bcrypt_hash_14...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer15@example.com', 'quang_huy', '$2b$12$e8Y...sample_bcrypt_hash_15...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer16@example.com', 'minh_duy', '$2b$12$e8Y...sample_bcrypt_hash_16...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer17@example.com', 'thuat_pro', '$2b$12$e8Y...sample_bcrypt_hash_17...', 'USER', 'LOCKED', DATE_ADD(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),
('gammer18@example.com', 'vinh_gamer', '$2b$12$e8Y...sample_bcrypt_hash_18...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer19@example.com', 'cuc_cute', '$2b$12$e8Y...sample_bcrypt_hash_19...', 'USER', 'ACTIVE', NULL, NOW()),
('gammer20@example.com', 'doanh_fit', '$2b$12$e8Y...sample_bcrypt_hash_20...', 'USER', 'ACTIVE', NULL, NOW());