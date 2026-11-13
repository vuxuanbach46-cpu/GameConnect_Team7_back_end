SET NAMES utf8mb4;
USE app_db;

-- 1. Chèn dữ liệu mẫu cho bảng games
INSERT IGNORE INTO games (id, name, image, genre) VALUES
(1, 'Liên Minh Huyền Thoại', 'https://example.com/lol.jpg', 'MOBA'),
(2, 'Valorant', 'https://example.com/valo.jpg', 'FPS'),
(3, 'PUBG Mobile', 'https://example.com/pubg.jpg', 'Battle Royale'),
(4, 'Free Fire', 'https://example.com/ff.jpg', 'Battle Royale'),
(5, 'Liên Quân Mobile', 'https://example.com/lqm.jpg', 'MOBA');

-- 2. Chèn dữ liệu mẫu cho bảng game_ranks
-- LOL (game_id = 1)
INSERT IGNORE INTO game_ranks (id, game_id, rank_name, rank_order) VALUES
(1, 1, 'Sắt', 1),
(2, 1, 'Đồng', 2),
(3, 1, 'Bạc', 3),
(4, 1, 'Vàng', 4),
(5, 1, 'Bạch Kim', 5),
(6, 1, 'Kim Cương', 6),
(7, 1, 'Cao Thủ', 7),
(8, 1, 'Thách Đấu', 8),

-- Valorant (game_id = 2)
(9, 2, 'Iron', 1),
(10, 2, 'Bronze', 2),
(11, 2, 'Silver', 3),
(12, 2, 'Gold', 4),
(13, 2, 'Platinum', 5),
(14, 2, 'Diamond', 6),
(15, 2, 'Ascendant', 7),
(16, 2, 'Immortal', 8),
(17, 2, 'Radiant', 9);

-- 3. Chèn dữ liệu mẫu cho bảng game_roles
-- LOL (game_id = 1)
INSERT IGNORE INTO game_roles (id, game_id, role_name) VALUES
(1, 1, 'Top'),
(2, 1, 'Jungle'),
(3, 1, 'Mid'),
(4, 1, 'ADC'),
(5, 1, 'Support'),

-- Valorant (game_id = 2)
(6, 2, 'Duelist'),
(7, 2, 'Initiator'),
(8, 2, 'Controller'),
(9, 2, 'Sentinel');
