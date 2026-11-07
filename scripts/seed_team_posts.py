"""Script seed 20 bài đăng tìm đội + roles + 8 đơn ứng tuyển mẫu vào database.
Khớp chuẩn schema DBML GameConnect (Task T3CCC1C).

Chạy từ thư mục gốc backend:
    python scripts/seed_team_posts.py

Yêu cầu: MySQL đang chạy và file .env đã cấu hình đúng.
"""
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import được app.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime

from app.db.session import Base, SessionLocal, engine
from app.models import team_post as _  # noqa: F401 – đảm bảo model được đăng ký
from app.models.team_post import (
    ApplicationStatus,
    PostStatus,
    TeamPost,
    TeamPostApplication,
    TeamPostRole,
)

# ---------------------------------------------------------------------------
# Dữ liệu seed bài đăng (20 bài)
# (user_id, game_id, title, min_rank_id, max_rank_id, needed_players, play_time, region, description, status, expires_at, role_ids)
# ---------------------------------------------------------------------------

POSTS_DATA = [
    (1,  1, "[LOL-VN] Tìm Jungle + Support leo Plat",  3,  5, 2, "20:00-23:00", "VN",  "Mic on bắt buộc, không toxic, leo rank flex.",        PostStatus.OPEN,   datetime(2026, 11, 30, 23, 59, 59), [2, 5]),
    (2,  1, "[LOL-VN] Cần Support chăm chỉ",           4,  7, 1, "21:00-24:00", "VN",  "Biết roam đúng lúc, main enchanter hoặc engage.",       PostStatus.OPEN,   datetime(2026, 11, 25, 23, 59, 59), [5]),
    (3,  1, "[LOL-VN] Team thiếu Mid và ADC",          5,  8, 2, "Cuối tuần",   "VN",  "Chơi ranked flex, cần người có kinh nghiệm.",          PostStatus.OPEN,   datetime(2026, 11, 20, 23, 59, 59), [3, 4]),
    (4,  2, "[VAL-SEA] Tìm Duelist biết entry",        3,  6, 1, "19:00-22:00", "SEA", "Không toxic, biết communicate rõ ràng.",              PostStatus.OPEN,   datetime(2026, 11, 28, 23, 59, 59), [1]),
    (5,  2, "[VAL-SEA] Cần Controller + Initiator",    4,  8, 2, "20:00-23:00", "SEA", "Team ranked đang thiếu 2 util players.",               PostStatus.OPEN,   datetime(2026, 11, 22, 23, 59, 59), [2, 3]),
    (6,  3, "[PUBG Mobile-VN] Squad tìm thêm 3 bạn",  None,None,3,"Tối hàng ngày","VN", "Chơi vui vẻ, không cần trình cao.",                    PostStatus.OPEN,   datetime(2026, 12,  1, 23, 59, 59), [1, 2, 3]),
    (7,  4, "[Free Fire-VN] Clash squad cuối tuần",    4,  5, 2, "18:00-21:00", "VN",  "Tìm Xạ Thủ và Hỗ Trợ cho clash squad.",                PostStatus.OPEN,   datetime(2026, 11, 29, 23, 59, 59), [1, 2]),
    (8,  5, "[LQM-VN] Team thiếu Đỡ Đòn",              3,  6, 1, "20:30-23:00", "VN",  "Ưu tiên người dùng Thủ hoặc Ryoma.",                   PostStatus.OPEN,   datetime(2026, 11, 21, 23, 59, 59), [5]),
    (9,  5, "[LQM-VN] Tìm Đường Trên farm tốt",        2,  3, 1, "Cuối tuần",   "VN",  "Chịu lắng nghe, cùng leo rank với bọn mình.",          PostStatus.OPEN,   datetime(2026, 11, 23, 23, 59, 59), [1]),
    (10, 1, "[LOL-VN] Tìm ADC newbie cùng leo",        2,  3, 1, "22:00-24:00", "VN",  "Tìm ADC chịu khó luyện, cùng học game.",               PostStatus.FULL,   datetime(2026, 11, 15, 23, 59, 59), [4]),
    (11, 2, "[VAL-SEA] Sentinel biết giữ site",        5,  8, 1, "21:00-23:00", "SEA", "Calm dưới áp lực, main Cypher hoặc Killjoy.",          PostStatus.OPEN,   datetime(2026, 11, 27, 23, 59, 59), [4]),
    (12, 1, "[LOL-VN] Team Challenger tìm sub",        7, 10, 2, "20:00-22:00", "VN",  "Tìm Top hoặc Jungle sub cho giải đấu nội bộ.",         PostStatus.OPEN,   datetime(2026, 11, 18, 23, 59, 59), [1, 2]),
    (13, 3, "[PUBG-AS] Squad TPP cuối tuần",          None,None,3,"Cuối tuần",  "AS",  "1 người cần thêm 3 chơi TPP squad.",                   PostStatus.OPEN,   datetime(2026, 11, 30, 23, 59, 59), [2, 3, 4]),
    (14, 2, "[VAL-SEA] Cần Initiator / Controller",    4,  5, 1, "20:00-23:00", "SEA", "Có Discord, không troll, ranked nghiêm túc.",          PostStatus.OPEN,   datetime(2026, 11, 26, 23, 59, 59), [2]),
    (15, 2, "[VAL-SEA] Tìm Initiator biết đọc map",    5,  6, 1, "21:00-24:00", "SEA", "Main Sova hoặc Fade, biết đọc map.",                   PostStatus.CLOSED, datetime(2026, 11, 10, 23, 59, 59), [2]),
    (16, 5, "[LQM-VN] ADC Vinh Dự biết phối hợp",      6,  7, 1, "20:00-22:30", "VN",  "Team Vinh Dự cần ADC cho ranked phối hợp.",            PostStatus.OPEN,   datetime(2026, 11, 24, 23, 59, 59), [4]),
    (17, 4, "[Free Fire-VN] Leo rank mùa mới",         4,  6, 3, "Tối hàng ngày","VN", "Tìm squad 4 người leo rank từ Bạch Kim.",               PostStatus.OPEN,   datetime(2026, 12, 10, 23, 59, 59), [1, 3, 4]),
    (18, 1, "[LOL-VN] Nhóm newbie học game",           1,  2, 4, "Linh hoạt",   "VN",  "Nhóm mới bắt đầu, tìm thêm thành viên học cùng.",      PostStatus.OPEN,   datetime(2026, 12, 15, 23, 59, 59), [1, 2, 3, 5]),
    (19, 2, "[VAL-VN] Học kỹ năng Unrated",            1,  3, 3, "19:00-22:00", "VN",  "Cần 3 người chơi Unrated, luyện kỹ năng cơ bản.",      PostStatus.OPEN,   datetime(2026, 12,  7, 23, 59, 59), [1, 2, 3]),
    (20, 1, "[LOL-VN] Ranked Flex 5v5 đầy đủ",         4,  6, 3, "20:00-23:00", "VN",  "Cần Top, Jungle, Mid cho team ranked flex.",           PostStatus.OPEN,   datetime(2026, 12, 20, 23, 59, 59), [1, 2, 3]),
]

# (post_idx_1based, user_id, message, status)
APPLICATIONS_DATA = [
    (1, 10, "Mình main Jungle, rank Plat II, mic on hàng ngày từ 20h.", ApplicationStatus.PENDING),
    (1, 11, "Main Jungle Ex-Diamond, hiện Plat do smurfs. Mic on sẵn.",   ApplicationStatus.ACCEPTED),
    (1, 12, "Jungle Gold I, chơi flex cuối tuần được.",                   ApplicationStatus.PENDING),
    (1, 13, "Pool: Lee Sin, Vi, Hecarim. Rank Plat III.",                 ApplicationStatus.REJECTED),
    (1, 14, "Main Jungle Plat I, luôn ward đúng chỗ, không tilt.",        ApplicationStatus.CANCELLED),
    (4, 15, "Main Jett Gold I, entry sẵn sàng.",                          ApplicationStatus.PENDING),
    (4, 16, "Main Neon, Silver III, đang leo lên Gold.",                  ApplicationStatus.PENDING),
    (4, 17, "Duelist main Reyna + Phoenix, Gold II, không toxic.",        ApplicationStatus.ACCEPTED),
]


def main() -> None:
    # Tạo bảng nếu chưa có
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Chỉ seed nếu bảng đang rỗng
        existing_count = db.query(TeamPost).count()
        if existing_count > 0:
            print(f"[seed] Đã có {existing_count} bài đăng trong DB – bỏ qua seed.")
            return

        posts: list[TeamPost] = []
        for row in POSTS_DATA:
            (user_id, game_id, title, min_rank_id, max_rank_id, needed_players,
             play_time, region, description, status, expires_at, role_ids) = row
            post = TeamPost(
                user_id=user_id,
                game_id=game_id,
                title=title,
                min_rank_id=min_rank_id,
                max_rank_id=max_rank_id,
                needed_players=needed_players,
                play_time=play_time,
                region=region,
                description=description,
                status=status,
                expires_at=expires_at,
            )
            db.add(post)
            db.flush()
            posts.append(post)

            # Thêm roles
            for r_id in role_ids:
                db.add(TeamPostRole(team_post_id=post.id, game_id=game_id, game_role_id=r_id))

        # Thêm applications
        for post_idx_1, user_id, message, app_status in APPLICATIONS_DATA:
            app = TeamPostApplication(
                team_post_id=posts[post_idx_1 - 1].id,
                user_id=user_id,
                message=message,
                status=app_status,
            )
            db.add(app)

        db.commit()
        print(f"[seed] ✅ Đã thêm {len(POSTS_DATA)} bài đăng, các vai trò (roles), và {len(APPLICATIONS_DATA)} đơn ứng tuyển mẫu.")
    except Exception as exc:
        db.rollback()
        print(f"[seed] ❌ Lỗi: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
