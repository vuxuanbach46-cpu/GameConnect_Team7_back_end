CREATE TABLE
    IF NOT EXISTS team_join_requests (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        team_id BIGINT UNSIGNED NOT NULL,
        user_id BIGINT UNSIGNED NOT NULL,
        message TEXT NULL,
        status ENUM ('PENDING', 'ACCEPTED', 'REJECTED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT pk_team_join_requests PRIMARY KEY (id),
        CONSTRAINT uq_team_join_requests_team_user UNIQUE (team_id, user_id),
        CONSTRAINT fk_team_join_requests_team FOREIGN KEY (team_id) REFERENCES teams (id) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_team_join_requests_user FOREIGN KEY (user_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE CASCADE,
        INDEX idx_team_join_requests_user_id (user_id),
        INDEX idx_team_join_requests_team_status (team_id, status)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;