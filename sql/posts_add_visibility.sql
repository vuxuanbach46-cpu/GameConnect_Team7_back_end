-- Run once on databases that already have the posts table.
ALTER TABLE posts
    ADD COLUMN visibility VARCHAR(10) NOT NULL DEFAULT 'PUBLIC';
