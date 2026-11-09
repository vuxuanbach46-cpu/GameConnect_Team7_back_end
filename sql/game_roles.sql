SET NAMES utf8mb4;
USE app_db;

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