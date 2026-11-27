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
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
import secrets
from app.models.password_reset_token import PasswordResetToken


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


def request_password_reset_service(email: str, db: Session):
    """Issue a short lived reset code; return it only to the calling route for email delivery."""
    reset_code = None
    try:
        normalized_email = email.strip().lower()
        user = (
            db.query(User)
            .filter(
                func.lower(User.email) == normalized_email,
                User.auth_provider == AuthProvider.LOCAL,
                User.password_hash.isnot(None),
            )
            .first()
        )
        if user:
            now = datetime.utcnow()
            (db.query(PasswordResetToken)
             .filter(PasswordResetToken.user_id == user.id,
                     PasswordResetToken.used_at.is_(None),
                     PasswordResetToken.invalidated_at.is_(None))
             .update({PasswordResetToken.invalidated_at: now}, synchronize_session=False))
            code = f"{secrets.randbelow(1_000_000):06d}"
            reset_code = code
            db.add(PasswordResetToken(
                user_id=user.id,
                token_hash=hash_password(code),
                expires_at=now + timedelta(minutes=15),
            ))
            db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise
    return reset_code


def reset_password_service(email: str, code: str, new_password: str, db: Session):
    """Validate a one-time email code and replace the local account password."""
    now = datetime.utcnow()
    try:
        user = (
            db.query(User)
            .filter(
                func.lower(User.email) == email.strip().lower(),
                User.auth_provider == AuthProvider.LOCAL,
                User.password_hash.isnot(None),
            )
            .with_for_update()
            .first()
        )
        if not user:
            raise HTTPException(status_code=400, detail="Mã xác nhận không hợp lệ hoặc đã hết hạn")

        reset_token = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.invalidated_at.is_(None),
            )
            .order_by(PasswordResetToken.created_at.desc(), PasswordResetToken.id.desc())
            .with_for_update()
            .first()
        )
        if (
            not reset_token
            or reset_token.expires_at <= now
            or not verify_password(code, reset_token.token_hash)
        ):
            raise HTTPException(status_code=400, detail="Mã xác nhận không hợp lệ hoặc đã hết hạn")

        if verify_password(new_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại")

        user.password_hash = hash_password(new_password)
        reset_token.used_at = now
        (db.query(PasswordResetToken)
         .filter(
             PasswordResetToken.user_id == user.id,
             PasswordResetToken.id != reset_token.id,
             PasswordResetToken.used_at.is_(None),
             PasswordResetToken.invalidated_at.is_(None),
         )
         .update({PasswordResetToken.invalidated_at: now}, synchronize_session=False))
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
