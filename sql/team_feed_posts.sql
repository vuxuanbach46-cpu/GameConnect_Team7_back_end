CREATE TABLE IF NOT EXISTS team_feed_posts (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  team_id BIGINT NOT NULL,
  author_id BIGINT NOT NULL,
  type VARCHAR(20) NOT NULL,
  title VARCHAR(120) NOT NULL,
  content TEXT NOT NULL,
  play_date VARCHAR(10) NULL,
  play_time VARCHAR(5) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX ix_team_feed_posts_team_created (team_id, created_at),
  FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
  FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
