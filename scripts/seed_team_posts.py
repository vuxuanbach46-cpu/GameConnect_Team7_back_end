"""Script seed 20 bài đăng tìm đội + 8 đơn ứng tuyển mẫu vào database.

Chạy từ thư mục gốc backend:
    python scripts/seed_team_posts.py

Yêu cầu: MySQL đang chạy và file .env đã cấu hình đúng.
Script dùng INSERT IGNORE nên chạy lại nhiều lần KHÔNG lỗi và KHÔNG thêm trùng.
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
)

# ---------------------------------------------------------------------------
# Dữ liệu seed
# ---------------------------------------------------------------------------

POSTS_DATA = [
    # (poster_id, game, min_rank, max_rank, roles_needed, slots_needed, play_time, region, description, status, expires_at)
    (1,  "Liên Minh Huyền Thoại", "Silver",   "Platinum", "Jungle",               2, "20:00-23:00",   "VN",  "Tìm Jungle biết gank sớm, mic on bắt buộc.",        PostStatus.OPEN,   datetime(2026, 11, 30, 23, 59, 59)),
    (2,  "Liên Minh Huyền Thoại", "Gold",     "Diamond",  "Support",              1, "21:00-24:00",   "VN",  "Cần Support chăm chỉ, biết roam đúng lúc.",         PostStatus.OPEN,   datetime(2026, 11, 25, 23, 59, 59)),
    (3,  "Liên Minh Huyền Thoại", "Platinum", "Master",   "Mid, ADC",             2, "Cuối tuần",     "VN",  "Team đang thiếu Mid và ADC cho ranked flex.",        PostStatus.OPEN,   datetime(2026, 11, 20, 23, 59, 59)),
    (4,  "VALORANT",               "Silver",   "Diamond",  "Duelist",              1, "19:00-22:00",   "SEA", "Tìm Duelist biết entry, không toxic.",               PostStatus.OPEN,   datetime(2026, 11, 28, 23, 59, 59)),
    (5,  "VALORANT",               "Gold",     "Immortal", "Controller, Initiator",2, "20:00-23:00",   "SEA", "Cần Controller + Initiator cho ranked.",             PostStatus.OPEN,   datetime(2026, 11, 22, 23, 59, 59)),
    (6,  "PUBG Mobile",            None,       None,       "Tất cả vị trí",        3, "Tối hàng ngày", "VN",  "Squad tìm thêm 3 người chơi vui, không cần giỏi.",   PostStatus.OPEN,   datetime(2026, 12,  1, 23, 59, 59)),
    (7,  "Free Fire",              "Bạch Kim", "Kim Cương","Xạ thủ, Hỗ trợ",      2, "18:00-21:00",   "VN",  "Cần 2 người cho clash squad cuối tuần.",             PostStatus.OPEN,   datetime(2026, 11, 29, 23, 59, 59)),
    (8,  "Liên Quân Mobile",       "Vàng",     "Tinh Anh", "Đỡ đòn",              1, "20:30-23:00",   "VN",  "Team thiếu Đỡ đòn, ưu tiên người dùng Thủ.",        PostStatus.OPEN,   datetime(2026, 11, 21, 23, 59, 59)),
    (9,  "Liên Quân Mobile",       "Bạc",      "Vàng",    "Đường trên",            1, "Cuối tuần",     "VN",  "Tìm đường trên farm tốt, chịu lắng nghe.",          PostStatus.OPEN,   datetime(2026, 11, 23, 23, 59, 59)),
    (10, "Genshin Impact",         None,       None,       "Tất cả",               3, "Linh hoạt",     "Asia","Tìm bạn clear Spiral Abyss Floor 12.",              PostStatus.OPEN,   datetime(2026, 12,  5, 23, 59, 59)),
    (11, "Liên Minh Huyền Thoại", "Bronze",   "Silver",   "ADC",                  1, "22:00-24:00",   "VN",  "Tìm ADC chịu khó luyện, cùng leo rank.",            PostStatus.FULL,   datetime(2026, 11, 15, 23, 59, 59)),
    (12, "VALORANT",               "Platinum", "Immortal", "Sentinel",             1, "21:00-23:00",   "SEA", "Cần Sentinel biết giữ site, calm dưới áp lực.",     PostStatus.OPEN,   datetime(2026, 11, 27, 23, 59, 59)),
    (13, "Liên Minh Huyền Thoại", "Diamond",  "Challenger","Top, Jungle",         2, "20:00-22:00",   "VN",  "Team Challenger tìm sub cho giải đấu nội bộ.",      PostStatus.OPEN,   datetime(2026, 11, 18, 23, 59, 59)),
    (14, "PUBG",                   None,       None,       "Tất cả",               3, "Cuối tuần",     "AS",  "Nhóm bạn 1 người, cần thêm 3 chơi TPP squad.",      PostStatus.OPEN,   datetime(2026, 11, 30, 23, 59, 59)),
    (15, "Apex Legends",           "Gold",     "Platinum", "Support (Lifeline)",   1, "20:00-23:00",   "SEA", "Cần Lifeline cho ranked, có Discord.",              PostStatus.OPEN,   datetime(2026, 11, 26, 23, 59, 59)),
    (16, "Apex Legends",           "Platinum", "Diamond",  "Recon (Bloodhound)",   1, "21:00-24:00",   "SEA", "Tìm Bloodhound biết đọc map, call shot tốt.",       PostStatus.CLOSED, datetime(2026, 11, 10, 23, 59, 59)),
    (17, "Liên Quân Mobile",       "Tinh Anh", "Vinh Dự", "Đường dưới",            1, "20:00-22:30",   "VN",  "Team Vinh Dự cần ADC biết phối hợp đội hình.",     PostStatus.OPEN,   datetime(2026, 11, 24, 23, 59, 59)),
    (18, "Free Fire",              "Bạch Kim", "Tinh Anh", "Tất cả vị trí",        3, "Tối hàng ngày", "VN",  "Tìm squad 4 người leo rank mùa mới.",              PostStatus.OPEN,   datetime(2026, 12, 10, 23, 59, 59)),
    (19, "Liên Minh Huyền Thoại", "Iron",     "Bronze",   "Tất cả vị trí",         4, "Linh hoạt",    "VN",  "Nhóm newbie tìm thêm thành viên học game cùng.",   PostStatus.OPEN,   datetime(2026, 12, 15, 23, 59, 59)),
    (20, "VALORANT",               "Iron",     "Silver",   "Tất cả vị trí",         3, "19:00-22:00",  "VN",  "Cần 3 người chơi Unrated học kỹ năng cùng nhau.", PostStatus.OPEN,   datetime(2026, 12,  7, 23, 59, 59)),
]

APPLICATIONS_DATA = [
    # (post_index_1based, applicant_id, message, status)
    (1, 10, "Mình main Jungle, rank Plat II, có thể chơi hàng ngày từ 20h.",  ApplicationStatus.PENDING),
    (1, 11, "Main Jungle Ex-Diamond, hiện tại Plat do smurfs. Mic on sẵn.",    ApplicationStatus.ACCEPTED),
    (1, 12, "Jungle Gold I, sẵn sàng chơi flex cuối tuần.",                    ApplicationStatus.PENDING),
    (1, 13, "Jungle Plat III, champion pool: Lee Sin, Vi, Hecarim.",            ApplicationStatus.REJECTED),
    (1, 14, "Main Jungle Plat I, luôn ward đúng chỗ, không tilt.",             ApplicationStatus.PENDING),
    (4, 20, "Duelist main Jett, Gold I VALORANT. Sẵn entry team.",             ApplicationStatus.PENDING),
    (4, 21, "Main Neon, Silver III, đang leo rank lên Gold.",                   ApplicationStatus.PENDING),
    (4, 22, "Duelist main Reyna + Phoenix, Gold II, không toxic.",              ApplicationStatus.ACCEPTED),
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
            (poster_id, game, min_rank, max_rank, roles_needed, slots_needed,
             play_time, region, description, status, expires_at) = row
            post = TeamPost(
                poster_id=poster_id,
                game=game,
                min_rank=min_rank,
                max_rank=max_rank,
                roles_needed=roles_needed,
                slots_needed=slots_needed,
                play_time=play_time,
                region=region,
                description=description,
                status=status,
                expires_at=expires_at,
            )
            db.add(post)
            posts.append(post)

        db.flush()  # flush để lấy id của posts

        for post_idx_1, applicant_id, message, app_status in APPLICATIONS_DATA:
            app = TeamPostApplication(
                post_id=posts[post_idx_1 - 1].id,
                applicant_id=applicant_id,
                message=message,
                status=app_status,
            )
            db.add(app)

        db.commit()
        print(f"[seed] ✅ Đã thêm {len(POSTS_DATA)} bài đăng và {len(APPLICATIONS_DATA)} đơn ứng tuyển mẫu.")
    except Exception as exc:
        db.rollback()
        print(f"[seed] ❌ Lỗi: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
