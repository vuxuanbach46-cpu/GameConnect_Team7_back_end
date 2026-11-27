"""
Script kiểm tra kết nối Database và kiểm thử CRUD endpoints.
Chạy: python scripts/verify_api.py
"""
import os
import sys

# Đảm bảo đường dẫn gốc của project có trong sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine
from sqlalchemy import text

def main():
    print("[1/3] Kiểm tra kết nối MySQL...")
    try:
        with engine.connect() as conn:
            val = conn.execute(text("SELECT 1")).scalar()
            print(f" -> Kết nối thành công! (SELECT 1 = {val})")
    except Exception as e:
        print(f" -> Lỗi kết nối DB: {e}")
        sys.exit(1)

    print("[2/3] Kiểm tra Health Check endpoint...")
    client = TestClient(app)
    resp = client.get("/api/health")
    print(f" -> GET /api/health: status={resp.status_code}, data={resp.json()}")

    print("[3/3] Kiểm tra CRUD Items...")
    # List items
    res_list = client.get("/api/items")
    print(f" -> GET /api/items: {len(res_list.json())} items hiện có")

    # Create item
    res_post = client.post("/api/items", json={
        "name": "Món kiểm thử tự động",
        "description": "Tạo bởi script kiểm thử",
        "price": 25000
    })
    print(f" -> POST /api/items: status={res_post.status_code}, id={res_post.json().get('id')}")
    item_id = res_post.json().get("id")

    # Update item
    if item_id:
        res_put = client.put(f"/api/items/{item_id}", json={"price": 30000})
        print(f" -> PUT /api/items/{item_id}: status={res_put.status_code}, new_price={res_put.json().get('price')}")

        # Delete item to clean up
        res_del = client.delete(f"/api/items/{item_id}")
        print(f" -> DELETE /api/items/{item_id}: status={res_del.status_code}")

    print("=== Hoàn tất kiểm thử CRUD: TẤT CẢ ĐỀU HOẠT ĐỘNG TỐT ===")

if __name__ == "__main__":
    main()
