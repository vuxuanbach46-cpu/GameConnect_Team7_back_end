
SET NAMES utf8mb4; 

CREATE DATABASE IF NOT EXISTS app_db
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE app_db;

CREATE TABLE IF NOT EXISTS items (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(255) NOT NULL,
  description TEXT NULL,
  price       DECIMAL(12, 2) NOT NULL DEFAULT 0,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO items (name, description, price) VALUES
  ('Cơm rang dưa bò', 'Món mẫu để kiểm tra API', 45000),
  ('Trà đá', 'Dữ liệu mẫu số 2', 5000);


USE app_db;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('USER', 'ADMIN') NOT NULL DEFAULT 'USER',
    status ENUM('ACTIVE', 'LOCKED') NOT NULL DEFAULT 'ACTIVE',
    locked_until DATETIME,
    last_seen DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO users
(id, email, username, password_hash, role)
VALUES
(1, 'user1@example.com', 'user1', 'sample_hash_1', 'USER'),
(2, 'user2@example.com', 'user2', 'sample_hash_2', 'USER'),
(3, 'user3@example.com', 'user3', 'sample_hash_3', 'USER'),
(4, 'user4@example.com', 'user4', 'sample_hash_4', 'USER'),
(5, 'admin@example.com', 'admin', 'sample_hash_admin', 'ADMIN');

CREATE TABLE IF NOT EXISTS notifications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    recipient_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    content VARCHAR(500) NOT NULL,
    link VARCHAR(500),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notifications_recipient_read_created
    (recipient_id, is_read, created_at),
    FOREIGN KEY (recipient_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    reporter_id BIGINT NOT NULL,
    target_type ENUM('USER', 'POST', 'COMMENT', 'TEAM_POST') NOT NULL,
    target_id BIGINT NOT NULL,
    reason VARCHAR(150) NOT NULL,
    description TEXT,
    status ENUM('PENDING', 'RESOLVED', 'REJECTED')
    NOT NULL DEFAULT 'PENDING',
    handler_id BIGINT,
    result TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    handled_at DATETIME,
    INDEX idx_reports_status_created (status, created_at),
    INDEX idx_reports_target (target_type, target_id),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (handler_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO notifications
(recipient_id, type, content, link, is_read)
VALUES
(1, 'FRIEND_REQUEST', 'Bạn có một lời mời kết bạn mới.', '/friends/requests', FALSE),
(1, 'TEAM_JOIN_REQUEST', 'Có người muốn tham gia đội của bạn.', '/teams/1/requests', FALSE),
(2, 'POST_LIKE', 'Bài viết của bạn vừa được thích.', '/posts/1', TRUE),
(2, 'POST_COMMENT', 'Có người vừa bình luận bài viết của bạn.', '/posts/2', FALSE),
(3, 'FRIEND_ACCEPTED', 'Lời mời kết bạn của bạn đã được chấp nhận.', '/friends', TRUE),
(4, 'TEAM_JOIN_ACCEPTED', 'Yêu cầu tham gia đội của bạn đã được chấp nhận.', '/teams/2', FALSE),
(5, 'POST_COMMENT', 'Có bình luận mới trên bài viết của bạn.', '/posts/3', FALSE);

INSERT INTO reports
(reporter_id, target_type, target_id, reason, description, status, handler_id, result, handled_at)
VALUES
(1, 'USER', 2, 'Quấy rối người dùng', 'Người dùng có hành vi xúc phạm người khác.', 'PENDING', NULL, NULL, NULL),
(2, 'POST', 1, 'Nội dung không phù hợp', 'Bài viết chứa nội dung không phù hợp với cộng đồng.', 'RESOLVED', 5, 'Đã kiểm tra và xử lý bài viết.', NOW()),
(3, 'COMMENT', 4, 'Spam', 'Bình luận quảng cáo lặp lại nhiều lần.', 'REJECTED', 5, 'Nội dung chưa đủ căn cứ để xác định vi phạm.', NOW()),
(4, 'TEAM_POST', 2, 'Thông tin sai lệch', 'Bài đăng tuyển thành viên có thông tin không chính xác.', 'PENDING', NULL, NULL, NULL),
(5, 'USER', 3, 'Giả mạo tài khoản', 'Tài khoản có dấu hiệu giả mạo người khác.', 'RESOLVED', 5, 'Đã xác minh và xử lý tài khoản.', NOW());

SELECT * FROM users;
SELECT * FROM notifications;
SELECT * FROM reports;users
