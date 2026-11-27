

-- 2. FRIENDSHIPS: Danh sách bạn bè


CREATE TABLE friendships (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    user_a BIGINT NOT NULL,
    user_b BIGINT NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_friendship_user_a
        FOREIGN KEY (user_a) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_friendship_user_b
        FOREIGN KEY (user_b) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_friendship_user_order
        CHECK (user_a < user_b),

    UNIQUE KEY uq_friendship_pair (user_a, user_b)
) ENGINE=InnoDB;


    