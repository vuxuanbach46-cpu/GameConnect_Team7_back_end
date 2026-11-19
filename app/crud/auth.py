from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from sqlalchemy.orm import Session
from app.models.user import User, AuthProvider, UserRole, UserStatus
from fastapi import HTTPException, status
from app.core.security import (
    hash_password,
    create_access_token,
    verify_password,
    create_refresh_token,
)
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone
import secrets
import logging
from app.models.password_reset_token import PasswordResetToken

logger = logging.getLogger(__name__)


def create_register_service(info: UserRegisterRequest, db: Session):
    """Tạo tài khoản user"""
    username_val = (info.username or info.full_name or "").strip()
    if not username_val or len(username_val) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên người dùng phải có từ 2 ký tự trở lên",
        )

    duplicate_email = db.query(User).filter(User.email == info.email).first()
    if duplicate_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email này đã tồn tại"
        )

    duplicate_username = db.query(User).filter(User.username == username_val).first()
    if duplicate_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tên người dùng đã tồn tại"
        )

    hash_pass = hash_password(info.password)

    user_new = User(
        email=info.email,
        username=username_val,
        password_hash=hash_pass,
        auth_provider=AuthProvider.LOCAL,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )

    db.add(user_new)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email hoặc tên người dùng đã tồn tại",
        ) from error

    db.refresh(user_new)

    return user_new


def login_service(info: UserLoginRequest, db: Session):
    """Đăng nhập bằng Email hoặc Username"""
    identifier = (info.email or info.username or "").strip()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng nhập email hoặc tên đăng nhập",
        )

    user = (
        db.query(User)
        .filter((User.email == identifier) | (User.username == identifier))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại"
        )

    if not user.password_hash or not verify_password(info.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Mật khẩu sai"
        )

    user_status = user.status.value if hasattr(user.status, "value") else str(user.status)
    if user_status == UserStatus.LOCKED.value:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if user.locked_until is None or now < user.locked_until:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản bị vô hiệu hóa",
            )
        user.status = UserStatus.ACTIVE
        user.locked_until = None
        user.locked_reason = None
        try:
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise
        user_status = UserStatus.ACTIVE.value

    if user_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản bị vô hiệu hóa"
        )

    user_role = user.role.value if hasattr(user.role, "value") else str(user.role)

    # Tạo access token
    account_token = create_access_token(
        data={"email": user.email, "sub": str(user.id), "role": user_role}
    )

    # Tạo refresh token
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": account_token,
        "refresh_token": refresh_token,
        "role": user_role,
    }


def change_password_service(user: User, old_password: str, new_password: str, db: Session):
    if not user.password_hash or not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu cũ không chính xác")
    if old_password == new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu mới phải khác mật khẩu cũ")

    try:
        user.password_hash = hash_password(new_password)
        db.commit()
    except Exception:
        db.rollback()
        raise


def request_password_reset_service(email: str, db: Session, log_code: bool = False):
    """Issue a short lived reset code, without revealing whether the account exists."""
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user:
            now = datetime.utcnow()
            (db.query(PasswordResetToken)
             .filter(PasswordResetToken.user_id == user.id,
                     PasswordResetToken.used_at.is_(None),
                     PasswordResetToken.invalidated_at.is_(None))
             .update({PasswordResetToken.invalidated_at: now}, synchronize_session=False))
            code = f"{secrets.randbelow(1_000_000):06d}"
            db.add(PasswordResetToken(
                user_id=user.id,
                token_hash=hash_password(code),
                expires_at=now + timedelta(minutes=15),
            ))
            db.flush()
            if log_code:
                logger.info("Development password reset code for %s: %s", email, code)
        db.commit()
    except Exception:
        db.rollback()
        raise
