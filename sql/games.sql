SET NAMES utf8mb4;
USE app_db;

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

INSERT INTO games (name, image, genre) VALUES
('League of Legends', 'https://cdn.example.com/games/lol.jpg', 'MOBA'),
('Valorant', 'https://cdn.example.com/games/valorant.jpg', 'FPS'),
('PUBG: Battlegrounds', 'https://cdn.example.com/games/pubg.jpg', 'Battle Royale'),
('Counter-Strike 2', 'https://cdn.example.com/games/cs2.jpg', 'FPS'),
('Dota 2', 'https://cdn.example.com/games/dota2.jpg', 'MOBA'),
('Genshin Impact', 'https://cdn.example.com/games/genshin.jpg', 'Action RPG'),
('Minecraft', 'https://cdn.example.com/games/minecraft.jpg', 'Sandbox'),
('Mobile Legends: Bang Bang', 'https://cdn.example.com/games/mlbb.jpg', 'MOBA');
