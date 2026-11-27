

-- 1. FRIEND REQUESTS: Yêu cầu kết bạn

CREATE TABLE friend_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    sender_id BIGINT NOT NULL,
    receiver_id BIGINT NOT NULL,

    status ENUM(
        'PENDING',
        'ACCEPTED',
        'REJECTED',
        'CANCELLED'
    ) NOT NULL DEFAULT 'PENDING',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_friend_request_sender
        FOREIGN KEY (sender_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_friend_request_receiver
        FOREIGN KEY (receiver_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_friend_request_different_users
        CHECK (sender_id <> receiver_id),

    INDEX idx_friend_requests_receiver (receiver_id),
    INDEX idx_friend_requests_receiver_status (receiver_id, status)
) ENGINE=InnoDB;

