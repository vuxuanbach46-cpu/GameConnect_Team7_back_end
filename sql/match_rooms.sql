SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- Bảng: match_rooms (Phòng tìm đội / Ghép đội tự động)
-- ============================================================
CREATE TABLE IF NOT EXISTS match_rooms (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    host_id         BIGINT       NOT NULL, 
    game_id         INT          NOT NULL, 
    room_name       VARCHAR(150) NOT NULL ,
    game_code       VARCHAR(100) NOT NULL ,
    max_players     INT          NOT NULL DEFAULT 5,
    current_players INT          NOT NULL DEFAULT 1 ,
    min_rank_id     INT          NULL,
    max_rank_id     INT          NULL,
    label           VARCHAR(100) NULL COMMENT 'Nhãn yêu cầu / Phong cách chơi (Tryhard, Vui vẻ, Có Mic...)',
    status          ENUM('WAITING', 'FULL', 'CANCELLED') NOT NULL DEFAULT 'WAITING',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX ix_match_rooms_game_status (game_id, status),
    INDEX ix_match_rooms_host (host_id),

    CONSTRAINT fk_match_rooms_host FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_match_rooms_game FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    CONSTRAINT fk_match_rooms_min_rank FOREIGN KEY (min_rank_id) REFERENCES game_ranks(id) ON DELETE SET NULL,
    CONSTRAINT fk_match_rooms_max_rank FOREIGN KEY (max_rank_id) REFERENCES game_ranks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
