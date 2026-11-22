CREATE TABLE IF NOT EXISTS team_invitations (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    team_id BIGINT NOT NULL,
    inviter_id BIGINT NOT NULL,
    invitee_id BIGINT NOT NULL,
    status ENUM('PENDING', 'ACCEPTED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_team_invitations_team_invitee UNIQUE (team_id, invitee_id),
    CONSTRAINT fk_team_invitation_team FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CONSTRAINT fk_team_invitation_inviter FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_team_invitation_invitee FOREIGN KEY (invitee_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX ix_team_invitations_invitee_status (invitee_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
