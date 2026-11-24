SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS app_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE app_db;

-- ==========================================
-- 2. BANG GAMER_PROFILES
-- Luu thong tin ho so game thu cua nguoi dung
-- ==========================================
CREATE TABLE IF NOT EXISTS gamer_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,

    display_name VARCHAR(100) NOT NULL,
    avatar VARCHAR(500) NULL,
    bio TEXT NULL,
    region VARCHAR(100) NULL,
    play_time VARCHAR(100) NULL,
    has_mic BOOLEAN NOT NULL DEFAULT FALSE,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

INSERT INTO gamer_profiles (
    user_id,
    display_name,
    avatar,
    bio,
    region,
    play_time,
    has_mic
) VALUES
(1, 'ShadowKnight',
 'https://cdn.example.com/avatars/user1.jpg',
 'Thích chơi game MOBA và phối hợp cùng đồng đội.',
 'Hà Nội',
 'Buổi tối (19:00 - 23:00)',
 TRUE),

(2, 'DragonSlayer',
 'https://cdn.example.com/avatars/user2.jpg',
 'Người chơi FPS, thích leo rank và thi đấu.',
 'TP. Hồ Chí Minh',
 'Buổi tối (20:00 - 00:00)',
 TRUE),

(3, 'MoonLight',
 'https://cdn.example.com/avatars/user3.jpg',
 'Yêu thích các game nhập vai và khám phá thế giới mở.',
 'Đà Nẵng',
 'Buổi chiều (14:00 - 18:00)',
 FALSE),

(4, 'SilentWolf',
 'https://cdn.example.com/avatars/user4.jpg',
 'Chơi game giải trí, ưu tiên teamwork.',
 'Hải Phòng',
 'Cuối tuần',
 TRUE),

(5, 'CyberFox',
 'https://cdn.example.com/avatars/user5.jpg',
 'Main Valorant, thích chơi Duelist.',
 'Cần Thơ',
 'Buổi tối (18:00 - 22:00)',
 TRUE),

(6, 'StarGamer',
 'https://cdn.example.com/avatars/user6.jpg',
 'Thích Minecraft và các game sáng tạo.',
 'Bắc Ninh',
 'Buổi chiều và tối',
 FALSE),

(7, 'NightHunter',
 'https://cdn.example.com/avatars/user7.jpg',
 'Đam mê game chiến thuật và cạnh tranh.',
 'Vĩnh Phúc',
 'Buổi tối (19:00 - 23:00)',
 TRUE),

(8, 'IcePhoenix',
 'https://cdn.example.com/avatars/user8.jpg',
 'Tìm kiếm đồng đội vui vẻ, thân thiện.',
 'Nam Định',
 'Buổi tối và cuối tuần',
 FALSE);
