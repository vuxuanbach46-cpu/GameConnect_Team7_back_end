"""Script nạp dữ liệu mẫu ban đầu cho toàn bộ hệ thống GameConnect:
1. Users (20 users + 1 admin)
2. Games (5 games phổ biến)
3. Game Ranks (Ranks chuẩn của từng game)
4. Game Roles (Roles chuẩn của từng game)
5. Team Posts (20 bài đăng tìm đội kèm vai trò và đơn ứng tuyển)
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from datetime import datetime
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.user import User
from app.core.security import hash_password
from scripts.seed_team_posts import main as seed_team_posts


def seed_all():
    db = SessionLocal()
    try:
        # 1. Seed Users nếu chưa có
        user_count = db.query(User).count()
        if user_count == 0:
            print("[1/4] Nạp dữ liệu Users mẫu...")
            users_to_add = [
                User(email="admin@gameconnect.vn", username="admin_boss", password_hash=hash_password("123456"), role="ADMIN", status="ACTIVE"),
                User(email="gammer01@example.com", username="vuxuanbach", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer02@example.com", username="huyptg", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer03@example.com", username="pro_gamer99", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer04@example.com", username="thanh_an", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer05@example.com", username="minh_duc", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer06@example.com", username="quoc_trung", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer07@example.com", username="gia_huy", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer08@example.com", username="tuan_anh", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer09@example.com", username="hoang_trung", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
                User(email="gammer10@example.com", username="nhat_anh", password_hash=hash_password("123456"), role="USER", status="ACTIVE"),
            ]
            for i in range(11, 21):
                users_to_add.append(
                    User(email=f"gammer{i}@example.com", username=f"player_{i}", password_hash=hash_password("123456"), role="USER", status="ACTIVE")
                )
            db.add_all(users_to_add)
            db.commit()
            print(f" -> Đã tạo {len(users_to_add)} users (mật khẩu mặc định: 123456)")
        else:
            print(f"[1/4] Đã có {user_count} users trong DB.")

        # 2. Seed Games nếu chưa có
        game_count = db.query(Game).count()
        if game_count == 0:
            print("[2/4] Nạp dữ liệu Games...")
            games_data = [
                Game(id=1, name="Liên Minh Huyền Thoại", genre="MOBA"),
                Game(id=2, name="VALORANT", genre="FPS"),
                Game(id=3, name="PUBG Mobile", genre="Battle Royale"),
                Game(id=4, name="Free Fire", genre="Battle Royale"),
                Game(id=5, name="Liên Quân Mobile", genre="MOBA"),
            ]
            db.add_all(games_data)
            db.commit()
            print(" -> Đã tạo 5 games mẫu.")
        else:
            print(f"[2/4] Đã có {game_count} games trong DB.")

        # 3. Seed Ranks & Roles
        rank_count = db.query(GameRank).count()
        if rank_count == 0:
            print("[3/4] Nạp Ranks & Roles...")
            # LOL ranks
            lol_ranks = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond", "Master", "Grandmaster", "Challenger"]
            for idx, rname in enumerate(lol_ranks, start=1):
                db.add(GameRank(game_id=1, rank_name=rname, rank_order=idx))
            # VALORANT ranks
            val_ranks = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]
            for idx, rname in enumerate(val_ranks, start=1):
                db.add(GameRank(game_id=2, rank_name=rname, rank_order=idx))
            # PUBG ranks
            pubg_ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Crown", "Ace", "Conqueror"]
            for idx, rname in enumerate(pubg_ranks, start=1):
                db.add(GameRank(game_id=3, rank_name=rname, rank_order=idx))
            # Free Fire ranks
            ff_ranks = ["Đồng", "Bạc", "Vàng", "Bạch Kim", "Kim Cương", "Tinh Anh", "Huyền Thoại"]
            for idx, rname in enumerate(ff_ranks, start=1):
                db.add(GameRank(game_id=4, rank_name=rname, rank_order=idx))
            # Lien Quan ranks
            lqm_ranks = ["Đồng", "Bạc", "Vàng", "Bạch Kim", "Kim Cương", "Tinh Anh", "Vinh Dự", "Thách Đấu"]
            for idx, rname in enumerate(lqm_ranks, start=1):
                db.add(GameRank(game_id=5, rank_name=rname, rank_order=idx))

            # Roles
            lol_roles = ["Top", "Jungle", "Mid", "ADC", "Support"]
            for rname in lol_roles:
                db.add(GameRole(game_id=1, role_name=rname))
            val_roles = ["Duelist", "Initiator", "Controller", "Sentinel"]
            for rname in val_roles:
                db.add(GameRole(game_id=2, role_name=rname))
            pubg_roles = ["IGL", "Fragger", "Support", "Sniper"]
            for rname in pubg_roles:
                db.add(GameRole(game_id=3, role_name=rname))
            ff_roles = ["Xạ Thủ", "Hỗ Trợ", "Trinh Sát", "Xe"]
            for rname in ff_roles:
                db.add(GameRole(game_id=4, role_name=rname))
            lqm_roles = ["Đường Trên", "Rừng", "Đường Giữa", "Đường Dưới", "Đỡ Đòn"]
            for rname in lqm_roles:
                db.add(GameRole(game_id=5, role_name=rname))

            db.commit()
            print(" -> Đã tạo Ranks & Roles cho tất cả games.")
        else:
            print(f"[3/4] Đã có {rank_count} ranks trong DB.")

        # 4. Seed Team Posts
        print("[4/4] Nạp 20 bài đăng tìm đội...")
        seed_team_posts()
        print("\n=== TẤT CẢ DỮ LIỆU BAN ĐẦU ĐÃ ĐƯỢC NẠP THÀNH CÔNG! ===")
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
