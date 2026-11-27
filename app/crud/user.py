from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User


def lock_user_account(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Tài khoản không tồn tại")

    if user.role == "ADMIN":
        raise HTTPException(status_code=400, detail="Không thể khóa tài khoản Admin")

    user.status = "LOCKED"
    user.locked_until = None
    user.locked_reason = "Bị khóa bởi quản trị viên"
    db.flush()
    return user
