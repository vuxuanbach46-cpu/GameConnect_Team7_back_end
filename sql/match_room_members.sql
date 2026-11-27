SET NAMES utf8mb4;
USE app_db;

-- Bảng: match_room_members (Danh sách thành viên trong phòng ghép)

CREATE TABLE IF NOT EXISTS match_room_members (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    room_id     BIGINT   NOT NULL ,
    user_id     BIGINT   NOT NULL,
    role_id     INT      NULL,
    is_host     BOOLEAN  NOT NULL DEFAULT FALSE,
    joined_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_match_room_member (room_id, user_id),
    INDEX ix_mrm_user (user_id),
    INDEX ix_mrm_room (room_id),

    CONSTRAINT fk_mrm_room FOREIGN KEY (room_id) REFERENCES match_rooms(id) ON DELETE CASCADE,
    CONSTRAINT fk_mrm_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_mrm_role FOREIGN KEY (role_id) REFERENCES game_roles(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
