-- T3CCC1C: Schema đầy đủ cho team_posts, team_post_roles, team_post_applications.
-- Khớp với DBML GameConnect schema (kể cả composite FK).
--
-- Cách chạy:
--   MySQL Workbench: File > Open SQL Script... > chọn file này > Execute (tia sét)
-- Chạy lại nhiều lần KHÔNG lỗi (IF NOT EXISTS).
-- Seed data chỉ chèn khi bảng team_posts đang rỗng.
--
-- Lưu ý: Bảng users, games, game_ranks, game_roles phải được tạo TRƯỚC
--         (do các task khác implement). File này tạo stub tối giản nếu chưa có.

SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- 0. Stub tables (tạo tối giản để FK hoạt động khi test độc lập)
--    Các task khác sẽ ALTER/REPLACE bảng này bằng cấu trúc đầy đủ.
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  email      VARCHAR(255) NOT NULL UNIQUE,
  username   VARCHAR(50)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL DEFAULT '',
  role       ENUM('USER','ADMIN') NOT NULL DEFAULT 'USER',
  status     ENUM('ACTIVE','LOCKED') NOT NULL DEFAULT 'ACTIVE',
  locked_until DATETIME NULL,
  last_seen    DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS games (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(150) NOT NULL UNIQUE,
  image_url  VARCHAR(500) NULL,
  genre      VARCHAR(100) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS game_ranks (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  game_id    BIGINT NOT NULL,
  rank_name  VARCHAR(100) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  UNIQUE KEY uq_game_ranks_game_rank (game_id, rank_name),
  UNIQUE KEY uq_game_ranks_game_id   (game_id, id),
  CONSTRAINT fk_game_ranks_game FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS game_roles (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  game_id    BIGINT NOT NULL,
  role_name  VARCHAR(100) NOT NULL,
  UNIQUE KEY uq_game_roles_game_role (game_id, role_name),
  UNIQUE KEY uq_game_roles_game_id   (game_id, id),
  CONSTRAINT fk_game_roles_game FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 1. team_posts
-- ============================================================
CREATE TABLE IF NOT EXISTS team_posts (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id        BIGINT       NOT NULL                 COMMENT 'FK → users.id',
  game_id        BIGINT       NOT NULL                 COMMENT 'FK → games.id',
  title          VARCHAR(150) NOT NULL                 COMMENT 'Tiêu đề bài đăng',
  min_rank_id    BIGINT       NULL                     COMMENT 'Composite FK → game_ranks(game_id, id)',
  max_rank_id    BIGINT       NULL                     COMMENT 'Composite FK → game_ranks(game_id, id)',
  needed_players INT          NOT NULL DEFAULT 1       COMMENT 'Số người cần tuyển',
  play_time      VARCHAR(100) NULL                     COMMENT 'Khung giờ chơi',
  region         VARCHAR(100) NULL                     COMMENT 'Khu vực / server',
  description    TEXT         NULL,
  status         ENUM('OPEN','FULL','CLOSED') NOT NULL DEFAULT 'OPEN',
  expires_at     DATETIME     NULL                     COMMENT 'Hạn hiển thị',
  created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  -- Indexes theo DBML schema
  UNIQUE KEY uq_team_posts_game_id      (game_id, id),   -- composite FK target từ team_post_roles
  INDEX      ix_team_posts_game_status  (game_id, status),
  INDEX      ix_team_posts_user_id      (user_id),

  -- Foreign keys
  CONSTRAINT fk_team_posts_user     FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
  CONSTRAINT fk_team_posts_game     FOREIGN KEY (game_id)  REFERENCES games(id)  ON DELETE CASCADE,
  CONSTRAINT fk_team_posts_min_rank FOREIGN KEY (game_id, min_rank_id)
      REFERENCES game_ranks(game_id, id) ON DELETE SET NULL,
  CONSTRAINT fk_team_posts_max_rank FOREIGN KEY (game_id, max_rank_id)
      REFERENCES game_ranks(game_id, id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. team_post_roles  (junction: vai trò cần tuyển)
-- ============================================================
CREATE TABLE IF NOT EXISTS team_post_roles (
  team_post_id BIGINT NOT NULL,
  game_id      BIGINT NOT NULL COMMENT 'Phải trùng game_id của team_post VÀ game_role',
  game_role_id BIGINT NOT NULL,

  PRIMARY KEY (team_post_id, game_role_id),

  -- Composite FK: (game_id, team_post_id) → team_posts(game_id, id)
  CONSTRAINT fk_tpr_post FOREIGN KEY (game_id, team_post_id)
      REFERENCES team_posts(game_id, id) ON DELETE CASCADE,

  -- Composite FK: (game_id, game_role_id) → game_roles(game_id, id)
  CONSTRAINT fk_tpr_role FOREIGN KEY (game_id, game_role_id)
      REFERENCES game_roles(game_id, id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. team_post_applications
-- ============================================================
CREATE TABLE IF NOT EXISTS team_post_applications (
  id           BIGINT AUTO_INCREMENT PRIMARY KEY,
  team_post_id BIGINT NOT NULL,
  user_id      BIGINT NOT NULL COMMENT 'FK → users.id (người ứng tuyển)',
  message      TEXT   NULL     COMMENT 'Lời nhắn khi ứng tuyển',
  status       ENUM('PENDING','ACCEPTED','REJECTED','CANCELLED') NOT NULL DEFAULT 'PENDING',
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE KEY uq_team_post_apps_post_user  (team_post_id, user_id),
  INDEX      ix_team_post_apps_user_status (user_id, status),

  CONSTRAINT fk_tpa_post FOREIGN KEY (team_post_id)
      REFERENCES team_posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_tpa_user FOREIGN KEY (user_id)
      REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. Seed data (games + ranks + roles)
-- ============================================================
-- Games
INSERT IGNORE INTO games (id, name, genre) VALUES
  (1, 'Liên Minh Huyền Thoại', 'MOBA'),
  (2, 'VALORANT',               'FPS'),
  (3, 'PUBG Mobile',            'Battle Royale'),
  (4, 'Free Fire',              'Battle Royale'),
  (5, 'Liên Quân Mobile',       'MOBA');

-- Ranks – Liên Minh Huyền Thoại (game_id=1)
INSERT IGNORE INTO game_ranks (game_id, rank_name, sort_order) VALUES
  (1,'Iron',1),(1,'Bronze',2),(1,'Silver',3),(1,'Gold',4),
  (1,'Platinum',5),(1,'Emerald',6),(1,'Diamond',7),(1,'Master',8),
  (1,'Grandmaster',9),(1,'Challenger',10);

-- Ranks – VALORANT (game_id=2)
INSERT IGNORE INTO game_ranks (game_id, rank_name, sort_order) VALUES
  (2,'Iron',1),(2,'Bronze',2),(2,'Silver',3),(2,'Gold',4),
  (2,'Platinum',5),(2,'Diamond',6),(2,'Ascendant',7),
  (2,'Immortal',8),(2,'Radiant',9);

-- Ranks – PUBG Mobile (game_id=3)
INSERT IGNORE INTO game_ranks (game_id, rank_name, sort_order) VALUES
  (3,'Bronze',1),(3,'Silver',2),(3,'Gold',3),(3,'Platinum',4),
  (3,'Diamond',5),(3,'Crown',6),(3,'Ace',7),(3,'Conqueror',8);

-- Ranks – Free Fire (game_id=4)
INSERT IGNORE INTO game_ranks (game_id, rank_name, sort_order) VALUES
  (4,'Đồng',1),(4,'Bạc',2),(4,'Vàng',3),(4,'Bạch Kim',4),
  (4,'Kim Cương',5),(4,'Tinh Anh',6),(4,'Huyền Thoại',7);

-- Ranks – Liên Quân Mobile (game_id=5)
INSERT IGNORE INTO game_ranks (game_id, rank_name, sort_order) VALUES
  (5,'Đồng',1),(5,'Bạc',2),(5,'Vàng',3),(5,'Bạch Kim',4),
  (5,'Kim Cương',5),(5,'Tinh Anh',6),(5,'Vinh Dự',7),(5,'Thách Đấu',8);

-- Roles – Liên Minh Huyền Thoại (game_id=1)
INSERT IGNORE INTO game_roles (game_id, role_name) VALUES
  (1,'Top'),(1,'Jungle'),(1,'Mid'),(1,'ADC'),(1,'Support');

-- Roles – VALORANT (game_id=2)
INSERT IGNORE INTO game_roles (game_id, role_name) VALUES
  (2,'Duelist'),(2,'Initiator'),(2,'Controller'),(2,'Sentinel');

-- Roles – PUBG Mobile (game_id=3)
INSERT IGNORE INTO game_roles (game_id, role_name) VALUES
  (3,'IGL'),(3,'Fragger'),(3,'Support'),(3,'Sniper');

-- Roles – Free Fire (game_id=4)
INSERT IGNORE INTO game_roles (game_id, role_name) VALUES
  (4,'Xạ Thủ'),(4,'Hỗ Trợ'),(4,'Trinh Sát'),(4,'Xe');

-- Roles – Liên Quân Mobile (game_id=5)
INSERT IGNORE INTO game_roles (game_id, role_name) VALUES
  (5,'Đường Trên'),(5,'Rừng'),(5,'Đường Giữa'),(5,'Đường Dưới'),(5,'Đỡ Đòn');

-- Users (stub seed)
INSERT IGNORE INTO users (id, email, username, password_hash) VALUES
  (1,'user1@gc.vn','player1','$2b$12$stub'),
  (2,'user2@gc.vn','player2','$2b$12$stub'),
  (3,'user3@gc.vn','player3','$2b$12$stub'),
  (4,'user4@gc.vn','player4','$2b$12$stub'),
  (5,'user5@gc.vn','player5','$2b$12$stub'),
  (6,'user6@gc.vn','player6','$2b$12$stub'),
  (7,'user7@gc.vn','player7','$2b$12$stub'),
  (8,'user8@gc.vn','player8','$2b$12$stub'),
  (9,'user9@gc.vn','player9','$2b$12$stub'),
  (10,'user10@gc.vn','player10','$2b$12$stub'),
  (11,'user11@gc.vn','player11','$2b$12$stub'),
  (12,'user12@gc.vn','player12','$2b$12$stub'),
  (13,'user13@gc.vn','player13','$2b$12$stub'),
  (14,'user14@gc.vn','player14','$2b$12$stub'),
  (15,'user15@gc.vn','player15','$2b$12$stub'),
  (16,'user16@gc.vn','player16','$2b$12$stub'),
  (17,'user17@gc.vn','player17','$2b$12$stub'),
  (18,'user18@gc.vn','player18','$2b$12$stub'),
  (19,'user19@gc.vn','player19','$2b$12$stub'),
  (20,'user20@gc.vn','player20','$2b$12$stub');

-- ============================================================
-- 5. Seed 20 bài đăng (chỉ chèn khi bảng đang rỗng)
-- ============================================================
-- game_ranks IDs (tham khảo):
--   LOL:  Iron=1,Bronze=2,Silver=3,Gold=4,Platinum=5,Emerald=6,Diamond=7,Master=8
--   VAL:  Iron=11,Bronze=12,Silver=13,Gold=14,Platinum=15,Diamond=16,Ascendant=17,Immortal=18,Radiant=19
--   PUBG: Bronze=20,Silver=21,Gold=22,Platinum=23,Diamond=24,Crown=25,Ace=26,Conqueror=27
--   FF:   Đồng=28,Bạc=29,Vàng=30,Bạch Kim=31,Kim Cương=32,Tinh Anh=33,Huyền Thoại=34
--   LQM:  Đồng=35,Bạc=36,Vàng=37,Bạch Kim=38,Kim Cương=39,Tinh Anh=40,Vinh Dự=41,Thách Đấu=42
-- (ID thực phụ thuộc vào thứ tự INSERT IGNORE ở trên; dùng subquery an toàn hơn)

INSERT INTO team_posts (user_id, game_id, title, min_rank_id, max_rank_id, needed_players, play_time, region, description, status, expires_at)
SELECT u, g, t, mnr, mxr, np, pt, rg, dsc, st, ea FROM (
  SELECT 1  u,1 g,'[LOL-VN] Tìm Jungle + Support leo Plat',(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Silver'),(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Platinum'),2,'20:00-23:00','VN','Mic on bắt buộc, không toxic, leo rank flex.','OPEN','2026-11-30 23:59:59' UNION ALL
  SELECT 2, 1,'[LOL-VN] Cần Support chăm chỉ',(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Gold'),(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Diamond'),1,'21:00-24:00','VN','Biết roam đúng lúc, main enchanter hoặc engage.','OPEN','2026-11-25 23:59:59' UNION ALL
  SELECT 3, 1,'[LOL-VN] Team thiếu Mid và ADC',(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Platinum'),(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Master'),2,'Cuối tuần','VN','Chơi ranked flex, cần người có kinh nghiệm.','OPEN','2026-11-20 23:59:59' UNION ALL
  SELECT 4, 2,'[VAL-SEA] Tìm Duelist biết entry',(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Silver'),(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Diamond'),1,'19:00-22:00','SEA','Không toxic, biết communicate bằng tiếng Anh hoặc tiếng Việt.','OPEN','2026-11-28 23:59:59' UNION ALL
  SELECT 5, 2,'[VAL-SEA] Cần Controller + Initiator',(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Gold'),(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Immortal'),2,'20:00-23:00','SEA','Team ranked đang thiếu 2 util players.','OPEN','2026-11-22 23:59:59' UNION ALL
  SELECT 6, 3,'[PUBG Mobile-VN] Squad tìm thêm 3 thành viên',NULL,NULL,3,'Tối hàng ngày','VN','Chơi vui vẻ, không cần trình cao.','OPEN','2026-12-01 23:59:59' UNION ALL
  SELECT 7, 4,'[Free Fire-VN] Clash squad cuối tuần',(SELECT id FROM game_ranks WHERE game_id=4 AND rank_name='Bạch Kim'),(SELECT id FROM game_ranks WHERE game_id=4 AND rank_name='Kim Cương'),2,'18:00-21:00','VN','Tìm Xạ Thủ và Hỗ Trợ cho clash squad.','OPEN','2026-11-29 23:59:59' UNION ALL
  SELECT 8, 5,'[LQM-VN] Team thiếu Đỡ Đòn',(SELECT id FROM game_ranks WHERE game_id=5 AND rank_name='Vàng'),(SELECT id FROM game_ranks WHERE game_id=5 AND rank_name='Tinh Anh'),1,'20:30-23:00','VN','Ưu tiên người dùng Thủ hoặc Ryoma.','OPEN','2026-11-21 23:59:59' UNION ALL
  SELECT 9, 5,'[LQM-VN] Tìm Đường Trên farm tốt',(SELECT id FROM game_ranks WHERE game_id=5 AND rank_name='Bạc'),(SELECT id FROM game_ranks WHERE game_id=5 AND rank_name='Vàng'),1,'Cuối tuần','VN','Chịu lắng nghe, không rủi ro lên rank với bọn mình.','OPEN','2026-11-23 23:59:59' UNION ALL
  SELECT 10,1,'[LOL-VN] Tìm ADC newbie cùng leo',(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Bronze'),(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Silver'),1,'22:00-24:00','VN','Tìm ADC chịu khó luyện, cùng học game.','FULL','2026-11-15 23:59:59' UNION ALL
  SELECT 11,2,'[VAL-SEA] Sentinel biết giữ site',(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Platinum'),(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Immortal'),1,'21:00-23:00','SEA','Calm dưới áp lực, main Cypher hoặc Killjoy.','OPEN','2026-11-27 23:59:59' UNION ALL
  SELECT 12,1,'[LOL-VN] Team Challenger tìm sub',(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Diamond'),(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Challenger'),2,'20:00-22:00','VN','Tìm Top hoặc Jungle sub cho giải đấu nội bộ.','OPEN','2026-11-18 23:59:59' UNION ALL
  SELECT 13,3,'[PUBG-AS] Squad TPP cuối tuần',NULL,NULL,3,'Cuối tuần','AS','1 người cần thêm 3 chơi TPP squad.','OPEN','2026-11-30 23:59:59' UNION ALL
  SELECT 14,2,'[VAL-SEA] Cần Lifeline / Support',(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Gold'),(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Platinum'),1,'20:00-23:00','SEA','Có Discord, không troll, ranked seriously.','OPEN','2026-11-26 23:59:59' UNION ALL
  SELECT 15,2,'[VAL-SEA] Tìm Recon / Initiator',(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Platinum'),(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Diamond'),1,'21:00-24:00','SEA','Main Bloodhound hoặc Sova, biết đọc map.','CLOSED','2026-11-10 23:59:59' UNION ALL
  SELECT 16,5,'[LQM-VN] ADC Vinh Dự biết phối hợp',(SELECT id FROM game_ranks WHERE game_id=5 AND rank_name='Tinh Anh'),(SELECT id FROM game_ranks WHERE game_id=5 AND rank_name='Vinh Dự'),1,'20:00-22:30','VN','Team Vinh Dự cần ADC cho ranked solo/duo.','OPEN','2026-11-24 23:59:59' UNION ALL
  SELECT 17,4,'[Free Fire-VN] Leo rank mùa mới',(SELECT id FROM game_ranks WHERE game_id=4 AND rank_name='Bạch Kim'),(SELECT id FROM game_ranks WHERE game_id=4 AND rank_name='Tinh Anh'),3,'Tối hàng ngày','VN','Tìm squad 4 người leo rank từ Bạch Kim trở lên.','OPEN','2026-12-10 23:59:59' UNION ALL
  SELECT 18,1,'[LOL-VN] Nhóm newbie học game',(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Iron'),(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Bronze'),4,'Linh hoạt','VN','Nhóm mới bắt đầu, tìm thêm thành viên học cùng.','OPEN','2026-12-15 23:59:59' UNION ALL
  SELECT 19,2,'[VAL-VN] Học kỹ năng Unrated',(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Iron'),(SELECT id FROM game_ranks WHERE game_id=2 AND rank_name='Silver'),3,'19:00-22:00','VN','Cần 3 người chơi Unrated, luyện kỹ năng cơ bản.','OPEN','2026-12-07 23:59:59' UNION ALL
  SELECT 20,1,'[LOL-VN] Ranked Flex 5v5 đầy đủ',(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Gold'),(SELECT id FROM game_ranks WHERE game_id=1 AND rank_name='Emerald'),3,'20:00-23:00','VN','Cần Top, Jungle, Mid cho team ranked flex.','OPEN','2026-12-20 23:59:59'
) seed
WHERE NOT EXISTS (SELECT 1 FROM team_posts LIMIT 1);

-- ============================================================
-- 6. Seed team_post_roles (vai trò cần tuyển cho mỗi bài)
-- ============================================================
-- Seed cho bài 1 (Jungle + Support – LOL) và bài 4 (Duelist – VAL)
-- Chỉ chèn khi bảng đang rỗng
INSERT INTO team_post_roles (team_post_id, game_id, game_role_id)
SELECT tp_id, gm_id, gr_id FROM (
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1) tp_id, 1 gm_id, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='Jungle') gr_id UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 1, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='Support') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Cần Support%' LIMIT 1), 1, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='Support') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Team thiếu Mid%' LIMIT 1), 1, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='Mid') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Team thiếu Mid%' LIMIT 1), 1, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='ADC') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 2, (SELECT id FROM game_roles WHERE game_id=2 AND role_name='Duelist') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Cần Controller%' LIMIT 1), 2, (SELECT id FROM game_roles WHERE game_id=2 AND role_name='Controller') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Cần Controller%' LIMIT 1), 2, (SELECT id FROM game_roles WHERE game_id=2 AND role_name='Initiator') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Ranked Flex%' LIMIT 1), 1, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='Top') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Ranked Flex%' LIMIT 1), 1, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='Jungle') UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Ranked Flex%' LIMIT 1), 1, (SELECT id FROM game_roles WHERE game_id=1 AND role_name='Mid')
) r
WHERE NOT EXISTS (SELECT 1 FROM team_post_roles LIMIT 1)
  AND tp_id IS NOT NULL AND gr_id IS NOT NULL;

-- ============================================================
-- 7. Seed team_post_applications (8 đơn ứng tuyển mẫu)
-- ============================================================
INSERT INTO team_post_applications (team_post_id, user_id, message, status)
SELECT tp_id, u_id, msg, st FROM (
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1) tp_id, 10 u_id, 'Mình main Jungle, rank Plat II, mic on hàng ngày từ 20h.' msg, 'PENDING' st UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 11, 'Main Jungle Ex-Diamond, hiện Plat do smurfs. Mic on sẵn.', 'ACCEPTED' UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 12, 'Jungle Gold I, chơi flex cuối tuần được.', 'PENDING' UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 13, 'Pool: Lee Sin, Vi, Hecarim. Rank Plat III.', 'REJECTED' UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 14, 'Main Jungle Plat I, luôn ward đúng chỗ, không tilt.', 'CANCELLED' UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 15, 'Main Jett Gold I, entry sẵn sàng.', 'PENDING' UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 16, 'Main Neon, Silver III, đang leo lên Gold.', 'PENDING' UNION ALL
  SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 17, 'Duelist main Reyna + Phoenix, Gold II, không toxic.', 'ACCEPTED'
) a
WHERE NOT EXISTS (SELECT 1 FROM team_post_applications LIMIT 1)
  AND tp_id IS NOT NULL;
