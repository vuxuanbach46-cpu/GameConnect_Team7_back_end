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
    user_id INT NOT NULL UNIQUE,

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
