-- Run once on databases that already have the posts table.
ALTER TABLE posts
    ADD COLUMN image_urls JSON NULL;

UPDATE posts
SET image_urls = JSON_ARRAY(image_url)
WHERE image_url IS NOT NULL AND image_url <> '';
