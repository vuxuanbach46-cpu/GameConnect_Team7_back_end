SET NAMES utf8mb4;
USE app_db;

-- ============================================================
-- Seed 20 bài đăng tìm đội (team_posts)
-- Chỉ chèn khi bảng team_posts đang rỗng
-- ============================================================
INSERT INTO team_posts (user_id, game_id, title, min_rank_id, max_rank_id, needed_players, play_time, region, description, status, expires_at)
SELECT u, g, t, mnr, mxr, np, pt, rg, dsc, st, ea FROM (
    SELECT 1 u, 1 g, '[LOL-VN] Tìm Jungle + Support leo Plat' t, 3 mnr, 5 mxr, 2 np, '20:00-23:00' pt, 'VN' rg, 'Mic on bắt buộc, không toxic, leo rank flex.' dsc, 'OPEN' st, '2026-11-30 23:59:59' ea UNION ALL
    SELECT 2, 1, '[LOL-VN] Cần Support chăm chỉ', 4, 7, 1, '21:00-24:00', 'VN', 'Biết roam đúng lúc, main enchanter hoặc engage.', 'OPEN', '2026-11-25 23:59:59' UNION ALL
    SELECT 3, 1, '[LOL-VN] Team thiếu Mid và ADC', 5, 8, 2, 'Cuối tuần', 'VN', 'Chơi ranked flex, cần người có kinh nghiệm.', 'OPEN', '2026-11-20 23:59:59' UNION ALL
    SELECT 4, 2, '[VAL-SEA] Tìm Duelist biết entry', 3, 6, 1, '19:00-22:00', 'SEA', 'Không toxic, biết communicate bằng tiếng Anh hoặc tiếng Việt.', 'OPEN', '2026-11-28 23:59:59' UNION ALL
    SELECT 5, 2, '[VAL-SEA] Cần Controller + Initiator', 4, 8, 2, '20:00-23:00', 'SEA', 'Team ranked đang thiếu 2 util players.', 'OPEN', '2026-11-22 23:59:59' UNION ALL
    SELECT 6, 3, '[PUBG Mobile-VN] Squad tìm thêm 3 thành viên', NULL, NULL, 3, 'Tối hàng ngày', 'VN', 'Chơi vui vẻ, không cần trình cao.', 'OPEN', '2026-12-01 23:59:59' UNION ALL
    SELECT 7, 4, '[Free Fire-VN] Clash squad cuối tuần', 4, 5, 2, '18:00-21:00', 'VN', 'Tìm Xạ Thủ và Hỗ Trợ cho clash squad.', 'OPEN', '2026-11-29 23:59:59' UNION ALL
    SELECT 8, 5, '[LQM-VN] Team thiếu Đỡ Đòn', 3, 6, 1, '20:30-23:00', 'VN', 'Ưu tiên người dùng Thủ hoặc Ryoma.', 'OPEN', '2026-11-21 23:59:59' UNION ALL
    SELECT 9, 5, '[LQM-VN] Tìm Đường Trên farm tốt', 2, 3, 1, 'Cuối tuần', 'VN', 'Chịu lắng nghe, không rủi ro lên rank với bọn mình.', 'OPEN', '2026-11-23 23:59:59' UNION ALL
    SELECT 10, 1, '[LOL-VN] Tìm ADC newbie cùng leo', 2, 3, 1, '22:00-24:00', 'VN', 'Tìm ADC chịu khó luyện, cùng học game.', 'FULL', '2026-11-15 23:59:59' UNION ALL
    SELECT 11, 2, '[VAL-SEA] Sentinel biết giữ site', 5, 8, 1, '21:00-23:00', 'SEA', 'Calm dưới áp lực, main Cypher hoặc Killjoy.', 'OPEN', '2026-11-27 23:59:59' UNION ALL
    SELECT 12, 1, '[LOL-VN] Team Challenger tìm sub', 7, 10, 2, '20:00-22:00', 'VN', 'Tìm Top hoặc Jungle sub cho giải đấu nội bộ.', 'OPEN', '2026-11-18 23:59:59' UNION ALL
    SELECT 13, 3, '[PUBG-AS] Squad TPP cuối tuần', NULL, NULL, 3, 'Cuối tuần', 'AS', '1 người cần thêm 3 chơi TPP squad.', 'OPEN', '2026-11-30 23:59:59' UNION ALL
    SELECT 14, 2, '[VAL-SEA] Cần Lifeline / Support', 4, 5, 1, '20:00-23:00', 'SEA', 'Có Discord, không troll, ranked seriously.', 'OPEN', '2026-11-26 23:59:59' UNION ALL
    SELECT 15, 2, '[VAL-SEA] Tìm Recon / Initiator', 5, 6, 1, '21:00-24:00', 'SEA', 'Main Bloodhound hoặc Sova, biết đọc map.', 'CLOSED', '2026-11-10 23:59:59' UNION ALL
    SELECT 16, 5, '[LQM-VN] ADC Vinh Dự biết phối hợp', 6, 7, 1, '20:00-22:30', 'VN', 'Team Vinh Dự cần ADC cho ranked solo/duo.', 'OPEN', '2026-11-24 23:59:59' UNION ALL
    SELECT 17, 4, '[Free Fire-VN] Leo rank mùa mới', 4, 6, 3, 'Tối hàng ngày', 'VN', 'Tìm squad 4 người leo rank từ Bạch Kim trở lên.', 'OPEN', '2026-12-10 23:59:59' UNION ALL
    SELECT 18, 1, '[LOL-VN] Nhóm newbie học game', 1, 2, 4, 'Linh hoạt', 'VN', 'Nhóm mới bắt đầu, tìm thêm thành viên học cùng.', 'OPEN', '2026-12-15 23:59:59' UNION ALL
    SELECT 19, 2, '[VAL-VN] Học kỹ năng Unrated', 1, 3, 3, '19:00-22:00', 'VN', 'Cần 3 người chơi Unrated, luyện kỹ năng cơ bản.', 'OPEN', '2026-12-07 23:59:59' UNION ALL
    SELECT 20, 1, '[LOL-VN] Ranked Flex 5v5 đầy đủ', 4, 6, 3, '20:00-23:00', 'VN', 'Cần Top, Jungle, Mid cho team ranked flex.', 'OPEN', '2026-12-20 23:59:59'
) seed
WHERE NOT EXISTS (SELECT 1 FROM team_posts LIMIT 1);

-- ============================================================
-- Seed vai trò cần tìm (team_post_roles)
-- ============================================================
INSERT INTO team_post_roles (team_post_id, game_id, game_role_id)
SELECT tp_id, gm_id, gr_id FROM (
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1) tp_id, 1 gm_id, 2 gr_id UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 1, 5 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Cần Support%' LIMIT 1), 1, 5 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Team thiếu Mid%' LIMIT 1), 1, 3 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Team thiếu Mid%' LIMIT 1), 1, 4 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 2, 1 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Cần Controller%' LIMIT 1), 2, 2 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Cần Controller%' LIMIT 1), 2, 3 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Ranked Flex%' LIMIT 1), 1, 1 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Ranked Flex%' LIMIT 1), 1, 2 UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Ranked Flex%' LIMIT 1), 1, 3
) r
WHERE NOT EXISTS (SELECT 1 FROM team_post_roles LIMIT 1)
  AND tp_id IS NOT NULL;

-- ============================================================
-- Seed đơn ứng tuyển mẫu (team_post_applications)
-- ============================================================
INSERT INTO team_post_applications (team_post_id, user_id, message, status)
SELECT tp_id, u_id, msg, st FROM (
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1) tp_id, 10 u_id, 'Mình main Jungle, rank Plat II, mic on hàng ngày từ 20h.' msg, 'PENDING' st UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 11, 'Main Jungle Ex-Diamond, hiện Plat do smurfs. Mic on sẵn.', 'ACCEPTED' UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 12, 'Jungle Gold I, chơi flex cuối tuần được.', 'PENDING' UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 13, 'Pool: Lee Sin, Vi, Hecarim. Rank Plat III.', 'REJECTED' UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[LOL-VN] Tìm Jungle%' LIMIT 1), 14, 'Main Jungle Plat I, luôn ward đúng chỗ, không tilt.', 'CANCELLED' UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 15, 'Main Jett Gold I, entry sẵn sàng.', 'PENDING' UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 16, 'Main Neon, Silver III, đang leo lên Gold.', 'PENDING' UNION ALL
    SELECT (SELECT id FROM team_posts WHERE title LIKE '[VAL-SEA] Tìm Duelist%' LIMIT 1), 17, 'Duelist main Reyna + Phoenix, Gold II, không toxic.', 'ACCEPTED'
) a
WHERE NOT EXISTS (SELECT 1 FROM team_post_applications LIMIT 1)
  AND tp_id IS NOT NULL;
