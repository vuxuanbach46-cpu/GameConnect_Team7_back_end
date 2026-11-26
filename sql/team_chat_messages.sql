CREATE TABLE IF NOT EXISTS team_chat_messages (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    team_id BIGINT NOT NULL,
    sender_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_team_chat_messages_team_id (team_id),
    KEY ix_team_chat_messages_sender_id (sender_id),
    KEY ix_team_chat_team_id_id (team_id, id),
    CONSTRAINT fk_team_chat_messages_team
        FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT fk_team_chat_messages_sender
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
