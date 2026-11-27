SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- Bảng: team_post_applications (Đơn ứng tuyển bài đăng)
-- ============================================================
CREATE TABLE IF NOT EXISTS team_post_applications (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    team_post_id BIGINT   NOT NULL COMMENT 'ID bài đăng (FK → team_posts.id)',
    user_id      BIGINT   NOT NULL COMMENT 'ID người ứng tuyển (FK → users.id)',
    message      TEXT     NULL     COMMENT 'Lời nhắn khi ứng tuyển',
    status       ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED') NOT NULL DEFAULT 'PENDING' COMMENT 'Trạng thái ứng tuyển',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_team_post_apps_post_user (team_post_id, user_id),
    INDEX ix_team_post_apps_user_status (user_id, status),

    CONSTRAINT fk_tpa_post FOREIGN KEY (team_post_id) REFERENCES team_posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_tpa_user FOREIGN KEY (user_id)      REFERENCES users(id)      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
