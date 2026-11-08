
-- ==========================================
-- 1. TAO DATABASE
-- ==========================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS app_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE app_db;


-- ==========================================
-- 2. BANG GAMER_PROFILES
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


-- ==========================================
-- 3. BANG GAMES
-- ==========================================

CREATE TABLE IF NOT EXISTS games (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(150) NOT NULL UNIQUE,
    image VARCHAR(500) NULL,
    genre VARCHAR(100) NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 4. BANG GAME_RANKS
-- ==========================================

CREATE TABLE IF NOT EXISTS game_ranks (
    id INT AUTO_INCREMENT PRIMARY KEY,

    game_id INT NOT NULL,
    rank_name VARCHAR(100) NOT NULL,
    rank_order INT NOT NULL DEFAULT 0,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_game_ranks_game
        FOREIGN KEY (game_id)
        REFERENCES games(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_game_rank (game_id, rank_name)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 5. BANG GAME_ROLES
-- ==========================================

CREATE TABLE IF NOT EXISTS game_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,

    game_id INT NOT NULL,
    role_name VARCHAR(100) NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_game_roles_game
        FOREIGN KEY (game_id)
        REFERENCES games(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_game_role (game_id, role_name)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 6. BANG USER_GAMES
-- ==========================================

CREATE TABLE IF NOT EXISTS user_games (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    game_id INT NOT NULL,
    rank_id INT NULL,
    role_id INT NULL,

    in_game_id VARCHAR(150) NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_games_game
        FOREIGN KEY (game_id)
        REFERENCES games(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_games_rank
        FOREIGN KEY (rank_id)
        REFERENCES game_ranks(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_user_games_role
        FOREIGN KEY (role_id)
        REFERENCES game_roles(id)
        ON DELETE SET NULL,

    UNIQUE KEY unique_user_game (user_id, game_id),

    INDEX idx_user_games_user (user_id),
    INDEX idx_user_games_game (game_id)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- ==========================================
-- 1. TAO DATABASE
-- ==========================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS app_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE app_db;


-- ==========================================
-- 2. BANG GAMER_PROFILES
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


-- ==========================================
-- 3. BANG GAMES
-- ==========================================

CREATE TABLE IF NOT EXISTS games (
    id INT AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(150) NOT NULL UNIQUE,
    image VARCHAR(500) NULL,
    genre VARCHAR(100) NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 4. BANG GAME_RANKS
-- ==========================================

CREATE TABLE IF NOT EXISTS game_ranks (
    id INT AUTO_INCREMENT PRIMARY KEY,

    game_id INT NOT NULL,
    rank_name VARCHAR(100) NOT NULL,
    rank_order INT NOT NULL DEFAULT 0,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_game_ranks_game
        FOREIGN KEY (game_id)
        REFERENCES games(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_game_rank (game_id, rank_name)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 5. BANG GAME_ROLES
-- ==========================================

CREATE TABLE IF NOT EXISTS game_roles (
    id INT AUTO_INCREMENT PRIMARY KEY,

    game_id INT NOT NULL,
    role_name VARCHAR(100) NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_game_roles_game
        FOREIGN KEY (game_id)
        REFERENCES games(id)
        ON DELETE CASCADE,

    UNIQUE KEY unique_game_role (game_id, role_name)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ==========================================
-- 6. BANG USER_GAMES
-- ==========================================

CREATE TABLE IF NOT EXISTS user_games (
    id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,
    game_id INT NOT NULL,
    rank_id INT NULL,
    role_id INT NULL,

    in_game_id VARCHAR(150) NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_games_game
        FOREIGN KEY (game_id)
        REFERENCES games(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_games_rank
        FOREIGN KEY (rank_id)
        REFERENCES game_ranks(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_user_games_role
        FOREIGN KEY (role_id)
        REFERENCES game_roles(id)
        ON DELETE SET NULL,

    UNIQUE KEY unique_user_game (user_id, game_id),

    INDEX idx_user_games_user (user_id),
    INDEX idx_user_games_game (game_id)

) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;
