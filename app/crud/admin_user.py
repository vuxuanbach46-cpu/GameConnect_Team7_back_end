from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStatus


def list_users(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
    status_filter: UserStatus | None = None,
):
    query = db.query(User)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(User.username.ilike(pattern), User.email.ilike(pattern))
        )
    if status_filter is not None:
        query = query.filter(User.status == status_filter)

    total = query.count()
    items = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size
    return items, total, total_pages


def lock_user(
    db: Session,
    user_id: int,
    duration_days: int | None,
    reason: str,
    admin_id: int,
) -> User:
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")
    if user.id == admin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể khóa tài khoản của chính mình")
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể khóa tài khoản quản trị viên")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user.status = UserStatus.LOCKED
    user.locked_until = now + timedelta(days=duration_days) if duration_days is not None else None
    user.locked_reason = reason.strip()
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def unlock_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")

    user.status = UserStatus.ACTIVE
    user.locked_until = None
    user.locked_reason = None
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
