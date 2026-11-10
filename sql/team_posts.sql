SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- Bảng: team_posts (Bài đăng tìm đội / thành viên)
-- ============================================================
CREATE TABLE IF NOT EXISTS team_posts (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id        BIGINT       NOT NULL                 COMMENT 'ID người đăng bài (FK → users.id)',
    game_id        INT          NOT NULL                 COMMENT 'Game của bài đăng (FK → games.id)',
    title          VARCHAR(150) NOT NULL                 COMMENT 'Tiêu đề bài đăng',
    min_rank_id    INT          NULL                     COMMENT 'Rank tối thiểu chấp nhận (FK → game_ranks.id)',
    max_rank_id    INT          NULL                     COMMENT 'Rank tối đa chấp nhận (FK → game_ranks.id)',
    needed_players INT          NOT NULL DEFAULT 1       COMMENT 'Số người cần tuyển thêm',
    play_time      VARCHAR(100) NULL                     COMMENT 'Khung giờ chơi (vd: 20:00-23:00)',
    region         VARCHAR(100) NULL                     COMMENT 'Khu vực / server (vd: VN, SEA)',
    description    TEXT         NULL                     COMMENT 'Mô tả chi tiết bài đăng',
    status         ENUM('OPEN', 'FULL', 'CLOSED') NOT NULL DEFAULT 'OPEN' COMMENT 'Trạng thái bài đăng',
    expires_at     DATETIME     NULL                     COMMENT 'Hạn hiển thị bài đăng',
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX ix_team_posts_user_id (user_id),
    INDEX ix_team_posts_game_status (game_id, status),

    CONSTRAINT fk_team_posts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_team_posts_game FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    CONSTRAINT fk_team_posts_min_rank FOREIGN KEY (min_rank_id) REFERENCES game_ranks(id) ON DELETE SET NULL,
    CONSTRAINT fk_team_posts_max_rank FOREIGN KEY (max_rank_id) REFERENCES game_ranks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
