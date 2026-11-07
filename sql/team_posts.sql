-- T3CCC1C: Tạo bảng team_posts + team_post_applications + 20 bài đăng mẫu.
-- Chạy trong MySQL Workbench: File > Open SQL Script... > chọn file này > Execute (tia sét).
-- Chạy lại nhiều lần KHÔNG lỗi (đã có thì bỏ qua). Dữ liệu mẫu chỉ thêm nếu bảng đang rỗng.

SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- 1. Bảng team_posts
-- ============================================================
CREATE TABLE IF NOT EXISTS team_posts (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  poster_id    INT NOT NULL                           COMMENT 'ID người đăng bài',
  game         VARCHAR(100) NOT NULL                  COMMENT 'Tên game',
  min_rank     VARCHAR(50)  NULL                      COMMENT 'Rank tối thiểu',
  max_rank     VARCHAR(50)  NULL                      COMMENT 'Rank tối đa',
  roles_needed VARCHAR(255) NULL                      COMMENT 'Vai trò cần tìm',
  slots_needed SMALLINT NOT NULL DEFAULT 1            COMMENT 'Số chỗ trống',
  play_time    VARCHAR(100) NULL                      COMMENT 'Khung giờ chơi',
  region       VARCHAR(100) NULL                      COMMENT 'Khu vực / server',
  description  TEXT NULL                              COMMENT 'Mô tả chi tiết',
  status       ENUM('OPEN','FULL','CLOSED') NOT NULL DEFAULT 'OPEN' COMMENT 'Trạng thái',
  expires_at   DATETIME NULL                          COMMENT 'Hạn hiển thị',
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_poster  (poster_id),
  INDEX idx_game    (game),
  INDEX idx_status  (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. Bảng team_post_applications
-- ============================================================
CREATE TABLE IF NOT EXISTS team_post_applications (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  post_id      INT NOT NULL,
  applicant_id INT NOT NULL                           COMMENT 'ID người ứng tuyển',
  message      TEXT NULL                              COMMENT 'Lời nhắn',
  status       ENUM('PENDING','ACCEPTED','REJECTED') NOT NULL DEFAULT 'PENDING' COMMENT 'Trạng thái đơn',
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_app_post FOREIGN KEY (post_id)
    REFERENCES team_posts(id) ON DELETE CASCADE ON UPDATE CASCADE,
  INDEX idx_post_id      (post_id),
  INDEX idx_applicant_id (applicant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. Seed 20 bài đăng mẫu (chỉ chèn khi bảng đang rỗng)
-- ============================================================
INSERT INTO team_posts
  (poster_id, game, min_rank, max_rank, roles_needed, slots_needed, play_time, region, description, status, expires_at)
SELECT * FROM (SELECT
  1,  'Liên Minh Huyền Thoại', 'Silver',   'Platinum', 'Jungle',              2, '20:00-23:00', 'VN',  'Tìm Jungle biết gank sớm, mic on bắt buộc.', 'OPEN',   '2026-11-30 23:59:59' UNION ALL SELECT
  2,  'Liên Minh Huyền Thoại', 'Gold',     'Diamond',  'Support',             1, '21:00-24:00', 'VN',  'Cần Support chăm chỉ, biết roam đúng lúc.',  'OPEN',   '2026-11-25 23:59:59' UNION ALL SELECT
  3,  'Liên Minh Huyền Thoại', 'Platinum', 'Master',   'Mid, ADC',            2, 'Cuối tuần',   'VN',  'Team đang thiếu Mid và ADC cho ranked flex.', 'OPEN',   '2026-11-20 23:59:59' UNION ALL SELECT
  4,  'VALORANT',               'Silver',   'Diamond',  'Duelist',             1, '19:00-22:00', 'SEA', 'Tìm Duelist biết entry, không toxic.',        'OPEN',   '2026-11-28 23:59:59' UNION ALL SELECT
  5,  'VALORANT',               'Gold',     'Immortal', 'Controller, Initiator', 2, '20:00-23:00', 'SEA', 'Cần Controller + Initiator cho ranked.',    'OPEN',   '2026-11-22 23:59:59' UNION ALL SELECT
  6,  'PUBG Mobile',            NULL,       NULL,       'Tất cả vị trí',       3, 'Tối hàng ngày', 'VN', 'Squad tìm thêm 3 người chơi vui, không cần giỏi.', 'OPEN', '2026-12-01 23:59:59' UNION ALL SELECT
  7,  'Free Fire',              'Bạch Kim', 'Kim Cương','Xạ thủ, Hỗ trợ',     2, '18:00-21:00', 'VN',  'Cần 2 người cho clash squad cuối tuần.',      'OPEN',   '2026-11-29 23:59:59' UNION ALL SELECT
  8,  'Liên Quân Mobile',       'Vàng',     'Tinh Anh', 'Đỡ đòn',             1, '20:30-23:00', 'VN',  'Team thiếu Đỡ đòn, ưu tiên người dùng Thủ.', 'OPEN',   '2026-11-21 23:59:59' UNION ALL SELECT
  9,  'Liên Quân Mobile',       'Bạc',      'Vàng',    'Đường trên',          1, 'Cuối tuần',   'VN',  'Tìm đường trên farm tốt, chịu lắng nghe.',    'OPEN',   '2026-11-23 23:59:59' UNION ALL SELECT
  10, 'Genshin Impact',         NULL,       NULL,       'Tất cả',              3, 'Linh hoạt',   'Asia','Tìm bạn clear Spiral Abyss Floor 12.',        'OPEN',   '2026-12-05 23:59:59' UNION ALL SELECT
  11, 'Liên Minh Huyền Thoại', 'Bronze',   'Silver',   'ADC',                 1, '22:00-24:00', 'VN',  'Tìm ADC chịu khó luyện, cùng leo rank.',      'FULL',   '2026-11-15 23:59:59' UNION ALL SELECT
  12, 'VALORANT',               'Platinum', 'Immortal', 'Sentinel',            1, '21:00-23:00', 'SEA', 'Cần Sentinel biết giữ site, calm dưới áp lực.','OPEN',  '2026-11-27 23:59:59' UNION ALL SELECT
  13, 'Liên Minh Huyền Thoại', 'Diamond',  'Challenger','Top, Jungle',        2, '20:00-22:00', 'VN',  'Team Challenger tìm sub cho giải đấu nội bộ.','OPEN',   '2026-11-18 23:59:59' UNION ALL SELECT
  14, 'PUBG',                   NULL,       NULL,       'Tất cả',              3, 'Cuối tuần',   'AS',  'Nhóm bạn 1 người, cần thêm 3 chơi TPP squad.','OPEN',   '2026-11-30 23:59:59' UNION ALL SELECT
  15, 'Apex Legends',           'Gold',     'Platinum', 'Support (Lifeline)',  1, '20:00-23:00', 'SEA', 'Cần Lifeline cho ranked, có Discord.',        'OPEN',   '2026-11-26 23:59:59' UNION ALL SELECT
  16, 'Apex Legends',           'Platinum', 'Diamond',  'Recon (Bloodhound)',  1, '21:00-24:00', 'SEA', 'Tìm Bloodhound biết đọc map, call shot tốt.', 'CLOSED', '2026-11-10 23:59:59' UNION ALL SELECT
  17, 'Liên Quân Mobile',       'Tinh Anh', 'Vinh Dự', 'Đường dưới',          1, '20:00-22:30', 'VN',  'Team Vinh Dự cần ADC biết phối hợp đội hình.','OPEN',   '2026-11-24 23:59:59' UNION ALL SELECT
  18, 'Free Fire',              'Bạch Kim', 'Tinh Anh', 'Tất cả vị trí',      3, 'Tối hàng ngày','VN', 'Tìm squad 4 người leo rank mùa mới.',         'OPEN',   '2026-12-10 23:59:59' UNION ALL SELECT
  19, 'Liên Minh Huyền Thoại', 'Iron',     'Bronze',   'Tất cả vị trí',       4, 'Linh hoạt',   'VN',  'Nhóm newbie tìm thêm thành viên học game cùng.','OPEN',  '2026-12-15 23:59:59' UNION ALL SELECT
  20, 'VALORANT',               'Iron',     'Silver',   'Tất cả vị trí',       3, '19:00-22:00', 'VN',  'Cần 3 người chơi Unrated học kỹ năng cùng nhau.','OPEN', '2026-12-07 23:59:59'
) AS seed
WHERE NOT EXISTS (SELECT 1 FROM team_posts LIMIT 1);

-- ============================================================
-- 4. Seed đơn ứng tuyển mẫu (5 đơn cho bài 1, 3 đơn cho bài 4)
-- ============================================================
INSERT INTO team_post_applications (post_id, applicant_id, message, status)
SELECT * FROM (SELECT
  1, 10, 'Mình main Jungle, rank Plat II, có thể chơi hàng ngày từ 20h.', 'PENDING'   UNION ALL SELECT
  1, 11, 'Main Jungle Ex-Diamond, hiện tại Plat do smurfs. Mic on sẵn.',   'ACCEPTED'  UNION ALL SELECT
  1, 12, 'Jungle Gold I, sẵn sàng chơi flex cuối tuần.',                   'PENDING'   UNION ALL SELECT
  1, 13, 'Jungle Plat III, champion pool: Lee Sin, Vi, Hecarim.',           'REJECTED'  UNION ALL SELECT
  1, 14, 'Main Jungle Plat I, luôn ward đúng chỗ, không tilt.',            'PENDING'   UNION ALL SELECT
  4, 20, 'Duelist main Jett, Gold I VALORANT. Sẵn entry team.',            'PENDING'   UNION ALL SELECT
  4, 21, 'Main Neon, Silver III, đang leo rank lên Gold.',                  'PENDING'   UNION ALL SELECT
  4, 22, 'Duelist main Reyna + Phoenix, Gold II, không toxic.',             'ACCEPTED'
) AS seed2
WHERE NOT EXISTS (SELECT 1 FROM team_post_applications LIMIT 1);
