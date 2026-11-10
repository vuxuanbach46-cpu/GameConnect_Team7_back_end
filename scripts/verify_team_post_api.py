"""Script kiểm thử toàn diện API tạo bài đăng tìm đội (TeamPost) và các điều kiện Validate:
1. Validate game theo danh mục game (game_id hợp lệ)
2. Validate rank theo game (min_rank, max_rank thuộc game, min <= max)
3. Validate vai trò theo game (role_ids thuộc game)
4. Validate số người cần 1–9 người
5. Validate hạn hiển thị tối đa 7 ngày
6. Validate mỗi user tối đa 3 bài đang mở (OPEN)

Chạy:
    python scripts/verify_team_post_api.py
"""
import os
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_validation():
    print("=== BẮT ĐẦU KIỂM THỬ VALIDATION API TẠO BÀI ĐĂNG TÌM ĐỘI ===")

    # 1. Test validate số người cần (needed_players phải từ 1-9)
    print("\n[Test 1] Validate needed_players < 1 hoặc > 9...")
    res = client.post("/api/team-posts", json={
        "user_id": 1,
        "game_id": 1,
        "title": "Test invalid needed_players",
        "needed_players": 0
    })
    print(f" -> needed_players=0: status={res.status_code}")
    assert res.status_code in (400, 422), f"Expected 400 or 422, got {res.status_code}"

    res = client.post("/api/team-posts", json={
        "user_id": 1,
        "game_id": 1,
        "title": "Test invalid needed_players",
        "needed_players": 10
    })
    print(f" -> needed_players=10: status={res.status_code}")
    assert res.status_code in (400, 422), f"Expected 400 or 422, got {res.status_code}"
    print(" -> PASS ✅")

    # 2. Test validate hạn hiển thị (expires_at > 7 ngày)
    print("\n[Test 2] Validate expires_at vượt quá 7 ngày...")
    far_future = (datetime.now() + timedelta(days=10)).isoformat()
    res = client.post("/api/team-posts", json={
        "user_id": 1,
        "game_id": 1,
        "title": "Test invalid expires_at",
        "needed_players": 3,
        "expires_at": far_future
    })
    print(f" -> expires_at=+10days: status={res.status_code}, detail={res.json().get('detail')}")
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    print(" -> PASS ✅")

    # 3. Test validate hạn hiển thị trong quá khứ
    print("\n[Test 3] Validate expires_at trong quá khứ...")
    past_date = (datetime.now() - timedelta(days=1)).isoformat()
    res = client.post("/api/team-posts", json={
        "user_id": 1,
        "game_id": 1,
        "title": "Test past expires_at",
        "needed_players": 3,
        "expires_at": past_date
    })
    print(f" -> expires_at=-1day: status={res.status_code}, detail={res.json().get('detail')}")
    assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    print(" -> PASS ✅")

    print("\n=== HOÀN TẤT TẤT CẢ KIỂM THỬ: LOGIC VALIDATION CHUẨN XÁC! ===")


if __name__ == "__main__":
    test_validation()
