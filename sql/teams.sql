CREATE TABLE
    IF NOT EXISTS teams (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        logo_url VARCHAR(500) NULL,
        main_game_id BIGINT UNSIGNED NOT NULL,
        description TEXT NULL,
        captain_id BIGINT UNSIGNED NOT NULL,
        max_members INT UNSIGNED NOT NULL DEFAULT 5,
        join_mode ENUM ('PUBLIC', 'APPROVAL_REQUIRED') NOT NULL DEFAULT 'PUBLIC',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      
        CONSTRAINT pk_teams PRIMARY KEY (id),
        CONSTRAINT uq_teams_name UNIQUE (name),
        CONSTRAINT chk_teams_max_members CHECK (max_members >= 1),
        CONSTRAINT fk_teams_main_game FOREIGN KEY (main_game_id) REFERENCES games (id) ON UPDATE CASCADE ON DELETE RESTRICT,
        CONSTRAINT fk_teams_captain FOREIGN KEY (captain_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE RESTRICT
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;