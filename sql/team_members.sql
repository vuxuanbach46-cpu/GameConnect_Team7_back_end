CREATE TABLE
    IF NOT EXISTS team_members (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        team_id BIGINT UNSIGNED NOT NULL,
        user_id BIGINT UNSIGNED NOT NULL,
        role ENUM ('CAPTAIN', 'MEMBER') NOT NULL DEFAULT 'MEMBER',
        joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT pk_team_members PRIMARY KEY (id),
        CONSTRAINT uq_team_members_team_user UNIQUE (team_id, user_id),
        CONSTRAINT fk_team_members_team FOREIGN KEY (team_id) REFERENCES teams (id) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT fk_team_members_user FOREIGN KEY (user_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE CASCADE,
        INDEX idx_team_members_user_id (user_id)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;