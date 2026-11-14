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

    # 8. Test tạo bài đăng thành công – dùng user sạch chưa có bài
    print("\n[Test 8] Tạo bài đăng hợp lệ...")
    valid_expiry = (datetime.now() + timedelta(days=3)).isoformat()

    # Tìm user chưa có bài OPEN nào (thử user_id 10..21 cho đến khi có)
    test_user_id = None
    for uid in range(10, 22):
        check = client.get(f"/api/team-posts?status=OPEN&page=1&page_size=5")
        # Lọc thủ công trên tất cả page để tìm user chưa đủ 3 bài
        # Cách đơn giản: thử tạo bài – nếu 400 với "tối đa 3" thì bỏ qua, thử uid tiếp theo
        probe = client.post("/api/team-posts", json={
            "user_id": uid, "game_id": 1, "title": f"Probe user {uid}", "needed_players": 1
        })
        if probe.status_code == 201:
            test_user_id = uid
            post_id = probe.json().get("id")
            # Xóa bài probe vừa tạo
            client.delete(f"/api/team-posts/{post_id}?user_id={uid}")
            break
        if "bị khóa" in (probe.json().get("detail") or ""):
            continue

    assert test_user_id is not None, "Không tìm được user nào còn chỗ để tạo bài đăng test"

    res = client.post("/api/team-posts", json={
        "user_id": test_user_id,
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
    print(f" -> Status: {res.status_code} (test_user_id={test_user_id})")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
    created_post = res.json()
    post_id = created_post.get("id")
    print(f" -> Created post ID={post_id}, roles={created_post.get('role_ids')}")
    print(" -> PASS ✅")

    # 9. Test giới hạn tối đa 3 bài đang mở
    print("\n[Test 9] Validate giới hạn tối đa 3 bài đang mở...")
    # Lấy số bài hiện tại của test_user_id và tạo thêm cho đủ 3
    page_resp = client.get(f"/api/team-posts?status=OPEN&page=1&page_size=100")
    user_open_posts = [p for p in page_resp.json()["items"] if p["user_id"] == test_user_id]
    for fill_i in range(3 - len(user_open_posts)):
        client.post("/api/team-posts", json={"user_id": test_user_id, "game_id": 1, "title": f"Fill {fill_i}", "needed_players": 1})
    # Bài thứ 4 phải bị từ chối
    res_4th = client.post("/api/team-posts", json={"user_id": test_user_id, "game_id": 1, "title": "Bài 4 (bị chặn)", "needed_players": 1})
    print(f" -> Bài 4 status: {res_4th.status_code}, detail: {res_4th.json().get('detail')}")
    assert res_4th.status_code == 400
    print(" -> PASS ✅")

    print("\n=== BẮT ĐẦU KIỂM THỬ TÌM KIẾM, LỌC, PHÂN TRANG VÀ QUYỀN SỞ HỮU (SỬA/ĐÓNG/XOÁ) ===")

    # 10. Test tìm kiếm cơ bản và phân trang
    print("\n[Test 10] Phân trang danh sách bài đăng (page, page_size)...")
    res = client.get("/api/team-posts?page=1&page_size=5")
    assert res.status_code == 200
    page_data = res.json()
    assert "items" in page_data
    assert "total" in page_data
    assert "page" in page_data
    assert "page_size" in page_data
    assert "total_pages" in page_data
    assert page_data["page"] == 1
    assert page_data["page_size"] == 5
    assert len(page_data["items"]) <= 5
    print(f" -> Total posts: {page_data['total']}, total_pages: {page_data['total_pages']}, items on page 1: {len(page_data['items'])}")
    print(" -> PASS ✅")

    # 11. Test sắp xếp mới nhất
    print("\n[Test 11] Kiểm tra sắp xếp bài đăng mới nhất (created_at DESC)...")
    items = page_data["items"]
    if len(items) >= 2:
        for i in range(len(items) - 1):
            assert items[i]["created_at"] >= items[i + 1]["created_at"]
    print(" -> PASS ✅")

    # 12. Test lọc theo game_id
    print("\n[Test 12] Lọc theo game_id=1 (LOL)...")
    res = client.get("/api/team-posts?game_id=1")
    assert res.status_code == 200
    lol_posts = res.json()["items"]
    assert all(p["game_id"] == 1 for p in lol_posts)
    print(f" -> Found {len(lol_posts)} posts for game_id=1")
    print(" -> PASS ✅")

    # 13. Test lọc theo rank_id (người chơi rank_id=4)
    print("\n[Test 13] Lọc theo rank_id...")
    res = client.get("/api/team-posts?game_id=1&rank_id=4")
    assert res.status_code == 200
    rank_posts = res.json()["items"]
    print(f" -> Found {len(rank_posts)} posts compatible with rank_id=4")
    print(" -> PASS ✅")

    # 14. Test lọc theo role_id
    print("\n[Test 14] Lọc theo role_id=2 (Jungle)...")
    res = client.get("/api/team-posts?role_id=2")
    assert res.status_code == 200
    role_posts = res.json()["items"]
    assert all(2 in p["role_ids"] for p in role_posts)
    print(f" -> Found {len(role_posts)} posts needing role_id=2")
    print(" -> PASS ✅")

    # 15. Test lọc theo giờ chơi (play_time) và khu vực (region)
    print("\n[Test 15] Lọc theo play_time='20:00' và region='VN'...")
    res = client.get("/api/team-posts?play_time=20:00&region=VN")
    assert res.status_code == 200
    time_posts = res.json()["items"]
    assert all("20:00" in (p["play_time"] or "") and "VN" in (p["region"] or "") for p in time_posts)
    print(f" -> Found {len(time_posts)} posts matching play_time and region")
    print(" -> PASS ✅")

    # 16. Test tìm kiếm từ khóa (q)
    print("\n[Test 16] Tìm kiếm từ khóa q='Leo rank'...")
    res = client.get("/api/team-posts?q=Leo rank")
    assert res.status_code == 200
    q_posts = res.json()["items"]
    assert any("Leo rank" in p["title"] for p in q_posts)
    print(f" -> Found {len(q_posts)} posts matching keyword 'Leo rank'")
    print(" -> PASS ✅")

    # 17. Test sửa bài (Chủ bài vs Người khác)
    print("\n[Test 17] Sửa bài: Người lạ sửa -> 403 Forbidden...")
    res = client.put(f"/api/team-posts/{post_id}", json={
        "user_id": 99,  # Không phải chủ bài
        "title": "Hacker cố sửa bài"
    })
    assert res.status_code == 403
    print(f" -> Detail: {res.json().get('detail')}")
    print(" -> PASS ✅")

    print("\n[Test 18] Sửa bài: Chủ bài sửa thành công -> 200 OK...")
    res = client.put(f"/api/team-posts/{post_id}", json={
        "user_id": test_user_id,
        "title": "[Updated] Leo rank Thách Đấu cùng team",
        "needed_players": 1,
        "role_ids": [3]
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    updated_post = res.json()
    assert updated_post["title"] == "[Updated] Leo rank Thách Đấu cùng team"
    assert updated_post["needed_players"] == 1
    assert updated_post["role_ids"] == [3]
    print(f" -> Updated title: {updated_post['title']}, role_ids: {updated_post['role_ids']}")
    print(" -> PASS ✅")

    # 19. Test đóng bài (Chủ bài vs Người khác)
    print("\n[Test 19] Đóng bài: Người lạ đóng -> 403 Forbidden...")
    res = client.patch(f"/api/team-posts/{post_id}/close?user_id=99")
    assert res.status_code == 403
    print(" -> PASS ✅")

    print("\n[Test 20] Đóng bài: Chủ bài đóng -> 200 OK, status=CLOSED...")
    res = client.patch(f"/api/team-posts/{post_id}/close?user_id={test_user_id}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    closed_post = res.json()
    assert closed_post["status"] == "CLOSED"
    print(f" -> Closed post status: {closed_post['status']}")
    print(" -> PASS ✅")

    print("\n[Test 21] Kiểm tra bài đã đóng không xuất hiện trong danh sách tìm kiếm mặc định...")
    res = client.get("/api/team-posts?page=1&page_size=100")
    items = res.json()["items"]
    assert not any(p["id"] == post_id for p in items)
    # Nhưng tìm với status=CLOSED thì thấy
    res_closed = client.get("/api/team-posts?status=CLOSED&page=1&page_size=100")
    items_closed = res_closed.json()["items"]
    assert any(p["id"] == post_id for p in items_closed)
    print(" -> PASS ✅")

    # 22. Test xóa bài (Chủ bài vs Người khác)
    print("\n[Test 22] Xóa bài: Người lạ xóa -> 403 Forbidden...")
    res = client.delete(f"/api/team-posts/{post_id}?user_id=99")
    assert res.status_code == 403
    print(" -> PASS ✅")

    print("\n[Test 23] Xóa bài: Chủ bài xóa -> 204 No Content...")
    res = client.delete(f"/api/team-posts/{post_id}?user_id={test_user_id}")
    assert res.status_code == 204
    print(" -> Deleted post successfully")

    res_check = client.get(f"/api/team-posts/{post_id}")
    assert res_check.status_code == 404
    print(" -> Verified post is gone (404)")
    print(" -> PASS ✅")

    print("\n=============================================================")
    print("=== TẤT CẢ 23/23 TEST CASES VALIDATION VÀ CHỨC NĂNG ĐẠT 100%! ===")
    print("=============================================================")


if __name__ == "__main__":
    test_validation()
