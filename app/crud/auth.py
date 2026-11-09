from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import HTTPException, status
from app.core.security import (
    hash_password,
    create_access_token,
    verify_password,
    create_refresh_token,
)


def create_register_service(info: UserRegisterRequest, db: Session):
    """Tạo tài khoản user"""
    duplicate_email = db.query(User).filter(User.email == info.email).first()

    if duplicate_email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Email đã tồn tại"
        )

    hash_pass = hash_password(info.password)

    user_new = User(
        email=info.email,
        username=info.full_name,
        password_hash=hash_pass,
    )

    db.add(user_new)
    db.commit()
    db.refresh(user_new)

    return user_new


def login_service(info: UserLoginRequest, db: Session):
    """Đăng nhập"""
    user = db.query(User).filter(User.email == info.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email k tồn tại"
        )

    if not verify_password(info.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Mật khẩu sai"
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản bị vô hiệu hóa "
        )

    # Tạo access token
    account_token = create_access_token(
        data={"email": user.email, "sub": str(user.id), "role": user.role}
    )

    # Tạo refresh token
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {"access_token": account_token, "refresh_token": refresh_token}
