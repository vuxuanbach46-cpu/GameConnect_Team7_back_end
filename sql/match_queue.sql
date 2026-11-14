SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- Bảng: match_queue (Hàng chờ tự động ghép đội - Quick Match Queue)
-- ============================================================
CREATE TABLE IF NOT EXISTS match_queue (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT   NOT NULL UNIQUE,
    game_id         INT      NOT NULL ,
    role_id         INT      NULL ,
    rank_id         INT      NULL,
    status          ENUM('SEARCHING', 'MATCHED', 'CANCELLED') NOT NULL DEFAULT 'SEARCHING' ,
    matched_room_id BIGINT   NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX ix_mq_game_status (game_id, status),
    INDEX ix_mq_user (user_id),

    CONSTRAINT fk_mq_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_mq_game FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    CONSTRAINT fk_mq_role FOREIGN KEY (role_id) REFERENCES game_roles(id) ON DELETE SET NULL,
    CONSTRAINT fk_mq_rank FOREIGN KEY (rank_id) REFERENCES game_ranks(id) ON DELETE SET NULL,
    CONSTRAINT fk_mq_room FOREIGN KEY (matched_room_id) REFERENCES match_rooms(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
