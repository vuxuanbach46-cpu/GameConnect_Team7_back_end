SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- Bảng: team_post_roles (Vai trò cần tìm trong bài đăng)
-- ============================================================
CREATE TABLE IF NOT EXISTS team_post_roles (
    team_post_id BIGINT NOT NULL COMMENT 'ID bài đăng (FK → team_posts.id)',
    game_id      INT    NOT NULL COMMENT 'Game ID (FK → games.id)',
    game_role_id INT    NOT NULL COMMENT 'Vai trò cần tìm (FK → game_roles.id)',

    PRIMARY KEY (team_post_id, game_role_id),
    INDEX ix_tpr_game_role (game_role_id),

    CONSTRAINT fk_tpr_team_post FOREIGN KEY (team_post_id) REFERENCES team_posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_tpr_game      FOREIGN KEY (game_id)      REFERENCES games(id)      ON DELETE CASCADE,
    CONSTRAINT fk_tpr_role      FOREIGN KEY (game_role_id) REFERENCES game_roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
