"""Script tạo mới hoặc cập nhật tài khoản Admin cho GameConnect.

Cách sử dụng:
    # 1. Chạy với thông tin mặc định hoặc tự nhập:
    python scripts/create_admin.py

    # 2. Truyền tham số trực tiếp:
    python scripts/create_admin.py --username myadmin --email myadmin@example.com --password MyPassword@123
"""

import argparse
import os
import sys

# Đảm bảo đường dẫn gốc backend luôn có trong sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import AuthProvider, User, UserRole, UserStatus


def create_or_update_admin(username: str, email: str, password: str):
    db = SessionLocal()
    try:
        # Kiểm tra user theo username hoặc email
        user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        hashed = hash_password(password)

        if user:
            print(f"[*] Tìm thấy tài khoản ID={user.id} ({user.username} / {user.email}).")
            user.username = username
            user.email = email
            user.password_hash = hashed
            user.role = UserRole.ADMIN
            user.status = UserStatus.ACTIVE
            db.commit()
            print(f"[+] ĐÃ CẬP NHẬT TÀI KHOẢN ADMIN THÀNH CÔNG!")
            print(f"    - ID: {user.id}")
            print(f"    - Username: {user.username}")
            print(f"    - Email: {user.email}")
            print(f"    - Role: {user.role.value}")
            print(f"    - Password: {password}")
        else:
            new_admin = User(
                username=username,
                email=email,
                password_hash=hashed,
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                auth_provider=AuthProvider.LOCAL,
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print(f"[+] ĐÃ TẠO TÀI KHOẢN ADMIN MỚI THÀNH CÔNG!")
            print(f"    - ID: {new_admin.id}")
            print(f"    - Username: {new_admin.username}")
            print(f"    - Email: {new_admin.email}")
            print(f"    - Role: {new_admin.role.value}")
            print(f"    - Password: {password}")

    except Exception as e:
        db.rollback()
        print(f"[-] Lỗi khi tạo/cập nhật tài khoản Admin: {e}", file=sys.stderr)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tạo tài khoản Admin GameConnect")
    parser.add_argument("--username", default="admin", help="Tên đăng nhập admin (mặc định: admin)")
    parser.add_argument("--email", default="admin@example.com", help="Email admin (mặc định: admin@example.com)")
    parser.add_argument("--password", default="Admin@123", help="Mật khẩu admin (mặc định: Admin@123)")

    args = parser.parse_args()
    create_or_update_admin(args.username, args.email, args.password)
