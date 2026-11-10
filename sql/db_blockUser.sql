
-- 3. BLOCKS: Chặn người dùng


CREATE TABLE blocks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    blocker_id BIGINT NOT NULL,
    blocked_id BIGINT NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_block_blocker
        FOREIGN KEY (blocker_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_block_blocked
        FOREIGN KEY (blocked_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_block_different_users
        CHECK (blocker_id <> blocked_id),

    UNIQUE KEY uq_block_pair (blocker_id, blocked_id),

    INDEX idx_blocks_blocked (blocked_id)
) ENGINE=InnoDB;
