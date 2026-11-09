USE app_db;
CREATE TABLE IF NOT EXISTS reports (
    id BIGINT NOT NULL AUTO_INCREMENT,
    reporter_id BIGINT NOT NULL,
    target_type ENUM('USER', 'POST', 'COMMENT', 'TEAM_POST') NOT NULL,
    target_id BIGINT NOT NULL,
    reason VARCHAR(150) NOT NULL,
    description TEXT NULL,
    status ENUM('PENDING', 'RESOLVED', 'REJECTED')
        NOT NULL DEFAULT 'PENDING',
    handler_id BIGINT NULL,
    result TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    handled_at DATETIME NULL,
    PRIMARY KEY (id),
    INDEX idx_reports_status_created (status, created_at),
    INDEX idx_reports_target (target_type, target_id),
    CONSTRAINT fk_reports_reporter
        FOREIGN KEY (reporter_id) REFERENCES users(id),
    CONSTRAINT fk_reports_handler
        FOREIGN KEY (handler_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
