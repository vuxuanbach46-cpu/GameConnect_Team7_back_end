-- Thiết lập mã hóa và tối ưu thực thi
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Chạy file khởi tạo bảng và seed dữ liệu của users
SOURCE ./users.sql;

-- 2. Chạy tiếp các bảng game và profile
SOURCE ./games.sql;
SOURCE ./game_ranks.sql;
SOURCE ./game_roles.sql;
SOURCE ./gamer_profiles.sql;
SOURCE ./user_games.sql;

-- 3. Quan hệ bạn bè, thông báo, báo cáo
SOURCE ./db_friendships.sql;
SOURCE ./db_friend_requests.sql;
SOURCE ./db_blockUser.sql;
SOURCE ./notifications.sql;
SOURCE ./reports.sql;

-- 4. Module bài đăng tìm đội (Team Post)
SOURCE ./team_posts.sql;
SOURCE ./team_post_roles.sql;
SOURCE ./team_post_applications.sql;
SOURCE ./seed_team_posts.sql;

-- 5. Module quản lý đội nhóm (Team)
SOURCE ./teams.sql;
SOURCE ./team_members.sql;
SOURCE ./team_join_requests.sql;

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'Khởi tạo database và dữ liệu mẫu thành công!' AS message;
