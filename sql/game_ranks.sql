SET NAMES utf8mb4;
USE app_db;

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

INSERT INTO game_ranks (game_id, rank_name, rank_order) VALUES
-- League of Legends (game_id = 1)
(1, 'Iron', 1),
(1, 'Bronze', 2),
(1, 'Silver', 3),
(1, 'Gold', 4),

-- Valorant (game_id = 2)
(2, 'Iron', 1),
(2, 'Bronze', 2),
(2, 'Silver', 3),
(2, 'Gold', 4);
