SET NAMES utf8mb4;
USE app_db;

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

INSERT INTO user_games (
    user_id,
    game_id,
    rank_id,
    role_id,
    in_game_id
) VALUES
-- User 1: League of Legends
(1, 1, 1, 1, 'ShadowKnight#VN1'),

-- User 2: Valorant
(2, 2, 5, 6, 'DragonSlayer#VN2'),

-- User 3: League of Legends
(3, 1, 2, 3, 'MoonLight#VN3'),

-- User 4: Valorant
(4, 2, 6, 7, 'SilentWolf#VN4'),

-- User 5: League of Legends
(5, 1, 3, 4, 'CyberFox#VN5'),

-- User 6: Valorant
(6, 2, 7, 8, 'StarGamer#VN6'),

-- User 7: League of Legends
(7, 1, 4, 5, 'NightHunter#VN7'),

-- User 8: Valorant
(8, 2, 8, 9, 'IcePhoenix#VN8');
