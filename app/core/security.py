import bcrypt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
from app.db.session import get_db
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError, jwt
from app.models.user import User
from fastapi import Request

oauth2_schema = HTTPBearer(scheme_name="BearerAuth")
optional_bearer_schema = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
)


# Bắm mật khẩu
def hash_password(pass_word: str) -> str:
    return bcrypt.hashpw(pass_word.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# check mật khẩu
def verify_password(password: str, hash_password: str):
    return bcrypt.checkpw(password.encode("utf-8"), hash_password.encode("utf-8"))


# Tạo token
def create_access_token(
    data: dict, expire: int = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
):
    payload = data.copy()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=expire)
    payload.update({"exp": expiration, "type": "access"})

    return jwt.encode(payload, settings.SECRET_KEY, settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expiration = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload.update({"exp": expiration, "type": "refresh"})
    return jwt.encode(payload, settings.SECRET_KEY, settings.JWT_ALGORITHM)

# Giải mã access token và lấy user_id
def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    if payload.get("type") != "access":
        raise JWTError("Token không phải access token")

    user_id = int(payload["sub"])

    return user_id


# Lấy user hiện tại từ request state
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_schema),
    db: Session = Depends(get_db)
):
    user_id = getattr(request.state, "user_id", None)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bạn cần đăng nhập"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại"
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    return user

# Lấy user hiện tại từ request state, nhưng không bắt buộc phải có user
def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_schema),
    db: Session = Depends(get_db)
):
    user_id = getattr(request.state, "user_id", None)

    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại"
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa"
        )

    return user

# Phân quyền admin
def get_admin_user(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập chức năng này"
        )

    return current_user

# Cấp lại access token từ refresh token
def refresh_access_token(
    credentials: HTTPAuthorizationCredentials,
    db: Session,
) -> dict[str, str]:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không phải refresh token",
            )
        user_id = int(payload["sub"])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token hết hạn",
        )
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ: thiếu user ID",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại",
        )
    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa",
        )

    access_token = create_access_token(
        data={"email": user.email, "sub": str(user.id), "role": user.role}
    )
    return {"access_token": access_token}


# # Phân quyền admin
def require_admin(current_user: Session = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền truy cập chức năng này",
        )

    return current_user
