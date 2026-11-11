"""Script kiểm thử toàn diện API tạo bài đăng tìm đội (TeamPost) và các điều kiện Validate:
1. Validate needed_players (1-9)
2. Validate expires_at (tối đa 7 ngày, không ở quá khứ)
3. Validate game_id (game phải tồn tại)
4. Validate rank_id (phải thuộc game đã chọn, min_rank <= max_rank)
5. Validate role_ids (phải thuộc game đã chọn)
6. Validate mỗi user tối đa 3 bài đang mở (OPEN)
7. Tạo bài đăng thành công (Status 201)

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
    print("=== BẮT ĐẦU KIỂM THỬ TOÀN DIỆN VALIDATION API TẠO BÀI ĐĂNG TÌM ĐỘI ===")

    # 1. Test validate số người cần (needed_players phải từ 1-9)
    print("\n[Test 1] Validate needed_players < 1 hoặc > 9...")
    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 1, "title": "Test invalid needed_players", "needed_players": 0
    })
    assert res.status_code in (400, 422)

    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 1, "title": "Test invalid needed_players", "needed_players": 10
    })
    assert res.status_code in (400, 422)
    print(" -> PASS ✅")

    # 2. Test validate hạn hiển thị (expires_at > 7 ngày và trong quá khứ)
    print("\n[Test 2] Validate expires_at vượt quá 7 ngày...")
    far_future = (datetime.now() + timedelta(days=10)).isoformat()
    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 1, "title": "Test expires_at > 7d", "needed_players": 3, "expires_at": far_future
    })
    assert res.status_code == 400
    print(f" -> Detail: {res.json().get('detail')}")
    print(" -> PASS ✅")

    print("\n[Test 3] Validate expires_at trong quá khứ...")
    past_date = (datetime.now() - timedelta(days=1)).isoformat()
    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 1, "title": "Test past expires_at", "needed_players": 3, "expires_at": past_date
    })
    assert res.status_code == 400
    print(f" -> Detail: {res.json().get('detail')}")
    print(" -> PASS ✅")

    # 4. Test validate game_id không tồn tại
    print("\n[Test 4] Validate game_id không tồn tại...")
    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 99999, "title": "Test invalid game", "needed_players": 2
    })
    assert res.status_code == 400
    print(f" -> Detail: {res.json().get('detail')}")
    print(" -> PASS ✅")

    # 5. Test validate rank không thuộc game
    print("\n[Test 5] Validate rank không thuộc game...")
    # game_id=1 (LOL) nhưng rank_id=15 (thuộc game 2 - VALORANT)
    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 1, "title": "Test mismatch rank", "min_rank_id": 15, "needed_players": 2
    })
    assert res.status_code == 400
    print(f" -> Detail: {res.json().get('detail')}")
    print(" -> PASS ✅")

    # 6. Test validate min_rank > max_rank
    print("\n[Test 6] Validate min_rank cao hơn max_rank...")
    # LOL: rank 7 (Diamond) > rank 3 (Silver)
    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 1, "title": "Test min > max rank", "min_rank_id": 7, "max_rank_id": 3, "needed_players": 2
    })
    assert res.status_code == 400
    print(f" -> Detail: {res.json().get('detail')}")
    print(" -> PASS ✅")

    # 7. Test validate role không thuộc game
    print("\n[Test 7] Validate vai trò không thuộc game...")
    # game_id=1 (LOL) nhưng role_id=6 (Duelist thuộc VALORANT)
    res = client.post("/api/team-posts", json={
        "user_id": 2, "game_id": 1, "title": "Test mismatch role", "role_ids": [6], "needed_players": 2
    })
    assert res.status_code == 400
    print(f" -> Detail: {res.json().get('detail')}")
    print(" -> PASS ✅")

    # 8. Test tạo bài đăng thành công
    print("\n[Test 8] Tạo bài đăng hợp lệ...")
    valid_expiry = (datetime.now() + timedelta(days=3)).isoformat()
    # Dùng user_id=9 (chưa có bài nào mở)
    res = client.post("/api/team-posts", json={
        "user_id": 9,
        "game_id": 1,
        "title": "Leo rank Cao Thủ cùng team",
        "min_rank_id": 3,
        "max_rank_id": 6,
        "needed_players": 2,
        "play_time": "20:00-23:00",
        "region": "VN",
        "description": "Cần tuyển người giao tiếp tốt",
        "role_ids": [1, 2],
        "expires_at": valid_expiry
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    created_post = res.json()
    post_id = created_post.get("id")
    print(f" -> Created post ID={post_id}, roles={created_post.get('role_ids')}")
    print(" -> PASS ✅")

    # 9. Test giới hạn tối đa 3 bài đang mở
    print("\n[Test 9] Validate giới hạn tối đa 3 bài đang mở...")
    # user 9 đã có 1 bài, tạo thêm bài 2 và 3
    client.post("/api/team-posts", json={"user_id": 9, "game_id": 1, "title": "Bài 2", "needed_players": 1})
    client.post("/api/team-posts", json={"user_id": 9, "game_id": 1, "title": "Bài 3", "needed_players": 1})
    # Bài thứ 4 phải bị từ chối
    res_4th = client.post("/api/team-posts", json={"user_id": 9, "game_id": 1, "title": "Bài 4 (bị chặn)", "needed_players": 1})
    print(f" -> Bài 4 status: {res_4th.status_code}, detail: {res_4th.json().get('detail')}")
    assert res_4th.status_code == 400
    print(" -> PASS ✅")

    print("\n=============================================================")
    print("=== TẤT CẢ 9/9 TEST CASES VALIDATION ĐỀU ĐẠT CHUẨN XÁC! ===")
    print("=============================================================")


if __name__ == "__main__":
    test_validation()
