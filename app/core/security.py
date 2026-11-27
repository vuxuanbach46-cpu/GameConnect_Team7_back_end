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
import uuid
from app.models.revoked_token import RevokedToken
from sqlalchemy.exc import IntegrityError
import re
from app.models.user import User, AuthProvider, UserRole, UserStatus
import secrets

# Dùng cho Access Token
oauth2_schema = HTTPBearer(scheme_name="AccessToken", description="Nhập Access Token")

# Dùng cho Refresh Token
refresh_bearer_schema = HTTPBearer(
    scheme_name="RefreshToken", description="Nhập Refresh Token"
)

optional_bearer_schema = HTTPBearer(
    auto_error=False,
    scheme_name="AccessToken",
)


# Băm mật khẩu
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
    payload.update({"exp": expiration, "type": "access", "jti": str(uuid.uuid4())})

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(data: dict) -> str:
    payload = data.copy()

    expiration = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload.update({"exp": expiration, "type": "refresh", "jti": str(uuid.uuid4())})

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# Giải mã access token và lấy user_id
def decode_access_token(token: str) -> int:
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )

    if payload.get("type") != "access":
        raise JWTError("Token không phải access token")

    user_id = int(payload["sub"])

    return user_id


# Lấy user hiện tại từ request state
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_schema),
    db: Session = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    if user_id is None and credentials and credentials.credentials:
        try:
            user_id = decode_access_token(credentials.credentials)
        except Exception:
            user_id = None

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Bạn cần đăng nhập"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại"
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị vô hiệu hóa"
        )

    try:
        user.last_seen = datetime.now()
        db.commit()
    except Exception:
        db.rollback()

    return user


# Lấy user hiện tại từ request state, nhưng không bắt buộc phải có user
def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_schema),
    db: Session = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)

    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại"
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị vô hiệu hóa"
        )

    try:
        user.last_seen = datetime.now()
        db.commit()
    except Exception:
        db.rollback()

    return user


# Phân quyền admin
def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập chức năng này",
        )

    return current_user

    return current_user


# Cấp lại access token từ refresh token
def refresh_access_token(
    access_token: str,
    refresh_token: str,
    db: Session,
):
    try:
        # Giải mã Access Token cũ
        access_payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )

        # Giải mã Refresh Token cũ
        refresh_payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Kiểm tra đúng loại token
        if access_payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Access Token không hợp lệ",
            )

        if refresh_payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Refresh Token không hợp lệ",
            )

        # Lấy thông tin định danh
        access_jti = access_payload.get("jti")
        refresh_jti = refresh_payload.get("jti")
        user_id = refresh_payload.get("sub")

        if (
            not access_jti
            or not refresh_jti
            or not user_id
            or access_payload.get("sub") != user_id
        ):
            raise HTTPException(
                status_code=401,
                detail="Cặp token không hợp lệ",
            )

        # Kiểm tra cả hai token đã bị thu hồi chưa
        revoked_jtis = (
            db.query(RevokedToken.token_jti)
            .filter(RevokedToken.token_jti.in_([access_jti, refresh_jti]))
            .all()
        )

        if revoked_jtis:
            raise HTTPException(
                status_code=401,
                detail="Token đã bị thu hồi",
            )

        # Kiểm tra tài khoản
        user = db.query(User).filter(User.id == int(user_id)).first()

        if not user or user.status != "ACTIVE":
            raise HTTPException(
                status_code=403,
                detail="Tài khoản không tồn tại hoặc đã bị khóa",
            )

        # Lấy thời gian hết hạn của hai token cũ
        access_exp = access_payload.get("exp")
        refresh_exp = refresh_payload.get("exp")

        if not access_exp or not refresh_exp:
            raise HTTPException(
                status_code=401,
                detail="Token thiếu thông tin hết hạn",
            )

        # Thu hồi Access Token và Refresh Token cũ
        db.add_all(
            [
                RevokedToken(
                    token_jti=access_jti,
                    expires_at=datetime.fromtimestamp(
                        int(access_exp),
                        tz=timezone.utc,
                    ).replace(tzinfo=None),
                ),
                RevokedToken(
                    token_jti=refresh_jti,
                    expires_at=datetime.fromtimestamp(
                        int(refresh_exp),
                        tz=timezone.utc,
                    ).replace(tzinfo=None),
                ),
            ]
        )

        # Tạo cặp token mới
        new_access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
            }
        )

        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Lưu việc thu hồi token cũ
        db.commit()

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Token đã được sử dụng hoặc bị thu hồi",
        )

    except JWTError:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Access Token hoặc Refresh Token không hợp lệ hoặc đã hết hạn",
        )

    except Exception:
        db.rollback()
        raise


# # Phân quyền admin
def require_admin(current_user: Session = Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền truy cập chức năng này",
        )

    return current_user


def generate_google_username(email: str, db: Session):
    base_username = email.split("@")[0].lower()
    base_username = re.sub(r"[^a-z0-9_]", "", base_username)

    if not base_username:
        base_username = "google_user"

    username = base_username

    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}_{secrets.token_hex(3)}"

    return username


def google_login_service(user_info: dict, db: Session):

    # 1. Lấy thông tin Google
    google_id = user_info.get("sub")
    email = user_info.get("email")
    email_verified = user_info.get("email_verified")

    if not google_id or not email or email_verified is not True:
        raise HTTPException(
            status_code=400, detail="Thông tin tài khoản Google không hợp lệ"
        )

    email = email.strip().lower()

    try:
        # 2. Tìm user bằng Google ID
        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:

            # 3. Kiểm tra email đã tồn tại chưa
            user = db.query(User).filter(User.email == email).first()

            if user:
                # Không tự động liên kết nếu email đã thuộc tài khoản LOCAL
                if user.auth_provider == AuthProvider.LOCAL:
                    raise HTTPException(
                        status_code=409,
                        detail="Email đã được đăng ký. Vui lòng đăng nhập bằng tài khoản hiện tại.",
                    )

                user.google_id = google_id

            else:
                # 4. Tạo user mới
                user = User(
                    email=email,
                    username=generate_google_username(email, db),
                    google_id=google_id,
                    password_hash=None,
                    auth_provider=AuthProvider.GOOGLE,
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE,
                )

                db.add(user)
                db.flush()

        # 5. Kiểm tra trạng thái tài khoản
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")

        # 6. Cập nhật lần đăng nhập cuối
        user.last_seen = datetime.now()

        db.commit()
        db.refresh(user)

        # 7. Tạo Access Token đúng cơ chế security.py
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
            }
        )

        # 8. Tạo Refresh Token
        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
            }
        )

        # 9. Trả kết quả
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value,
                "status": user.status.value,
                "auth_provider": user.auth_provider.value,
            },
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
