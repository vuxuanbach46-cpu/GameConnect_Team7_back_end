import logging
from urllib.parse import urljoin, urlsplit, urlunsplit

from authlib.integrations.base_client.errors import OAuthError
from fastapi import APIRouter, Depends, Request, status, Header
from fastapi.responses import RedirectResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
)
from app.db.session import get_db
from app.crud.auth import create_register_service, login_service
from app.schemas.api_response import api_repoint
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.security import (
    refresh_bearer_schema,
    refresh_access_token,
)
from app.core.limiter import limiter

from app.models.revoked_token import RevokedToken
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException
from app.core.config import settings
from datetime import datetime, timezone
from app.schemas.auth import LogoutRequest
from app.schemas.auth import ChangePasswordRequest, ForgotPasswordRequest
from app.core.security import get_current_user
from app.crud.auth import change_password_service, request_password_reset_service
from app.core.google_oauth import oauth
from app.core.security import oauth2_schema
from app.core.security import google_login_service , create_access_token, create_refresh_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["AUTH"])


@router.put("/change-password", summary="Đổi mật khẩu")
def change_password(
    request: Request,
    info: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        change_password_service(current_user, info.old_password, info.new_password, db)
        return api_repoint(
            req=request,
            status_code=status.HTTP_200_OK,
            message="Đổi mật khẩu thành công",
            data=None,
        )
    except HTTPException as error:
        db.rollback()
        return api_repoint(
            req=request,
            status_code=error.status_code,
            message="Đổi mật khẩu thất bại",
            error=error.detail,
        )
    except Exception:
        db.rollback()
        logger.exception("Password change failed")
        return api_repoint(
            req=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Đổi mật khẩu thất bại",
            error="Không thể cập nhật mật khẩu",
        )


@router.post("/forgot-password", summary="Yêu cầu đặt lại mật khẩu")
@limiter.limit("3/hour")
def forgot_password(
    request: Request,
    info: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    try:
        request_password_reset_service(
            info.email, db, log_code=settings.ENVIRONMENT.strip().lower() == "development"
        )
        return api_repoint(
            req=request,
            status_code=status.HTTP_200_OK,
            message="Nếu email tồn tại, hướng dẫn đặt lại mật khẩu sẽ được gửi.",
            data=None,
        )
    except Exception:
        db.rollback()
        logger.exception("Password reset request failed")
        return api_repoint(
            req=request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Không thể xử lý yêu cầu",
            error="Vui lòng thử lại sau",
        )


@router.post(
    "/register",
    summary="Đăng ký tài khoản",
    description="Người dùng nhập thông tin để đăng kí tài khoản",
)
def create_register(req: Request, info: UserRegisterRequest, db=Depends(get_db)):
    user_new = create_register_service(info=info, db=db)

    user_role = user_new.role.value if hasattr(user_new.role, "value") else str(user_new.role)
    user_status = user_new.status.value if hasattr(user_new.status, "value") else str(user_new.status)

    account_token = create_access_token(
        data={"email": user_new.email, "sub": str(user_new.id), "role": user_role}
    )
    refresh_token = create_refresh_token(data={"sub": str(user_new.id)})

    response_data = {
        "id": user_new.id,
        "email": user_new.email,
        "username": user_new.username,
        "role": user_role,
        "status": user_status,
        "access_token": account_token,
        "refresh_token": refresh_token,
    }
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Đăng ký tài khoản thành công",
        data=response_data,
    )


# Code Phong chạy đăng kí
# def create_register(req: Request, info: UserRegisterRequest, db=Depends(get_db)):
#     user_new = create_register_service(info=info, db=db)

#     user_response = UserRegisterResponse(
#         id=user_new.id,
#         email=user_new.email,
#         full_name=user_new.username,
#         role=user_new.role.value,
#         is_active=user_new.status.value == "ACTIVE"
#     )
#     return api_repoint(
#         req=req,
#         status_code=status.HTTP_201_CREATED,
#         message="Đăng kí tài khoản thành công",
#         data=user_response,
#     )

# Code Phong chạy đăng kí
# def create_register(req: Request, info: UserRegisterRequest, db=Depends(get_db)):
#     user_new = create_register_service(info=info, db=db)

#     user_response = UserRegisterResponse(
#         id=user_new.id,
#         email=user_new.email,
#         full_name=user_new.username,
#         role=user_new.role.value,
#         is_active=user_new.status.value == "ACTIVE"
#     )
#     return api_repoint(
#         req=req,
#         status_code=status.HTTP_201_CREATED,
#         message="Đăng kí tài khoản thành công",
#         data=user_response,
#     )


@router.post(
    "/login",
    summary="Đăng nhập tài khoản",
    description="Nhập thông tin đã đăng kí để đăng nhập dùng các api",
)
@limiter.limit("20/minute")
def login(request: Request, info: UserLoginRequest, db=Depends(get_db)):
    user_login = UserLoginResponse.model_validate(login_service(info=info, db=db))
    return api_repoint(
        req=request,
        status_code=status.HTTP_200_OK,
        message="Đăng nhập thành công",
        data=user_login,
    )


@router.post(
    "/refresh",
    summary="Xoay vòng Access Token và Refresh Token",
    description="Thu hồi cả hai token cũ và cấp cặp token mới",
)
def create_refresh_token(
    req: Request,
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_schema),
    refresh_token: str = Header(..., alias="X-Refresh-Token"),
    db: Session = Depends(get_db),
):
    try:
        new_tokens = refresh_access_token(
            access_token=credentials.credentials,
            refresh_token=refresh_token,
            db=db,
        )

        return api_repoint(
            req=req,
            status_code=status.HTTP_200_OK,
            message="Xoay vòng token thành công",
            data=new_tokens,
        )

    except HTTPException as e:
        return api_repoint(
            req=req,
            status_code=e.status_code,
            message="Xoay vòng token thất bại",
            error=e.detail,
        )


# Api đăng xuất chỉ chấp nhận refresh token
@router.post(
    "/logout",
    summary="Đăng xuất tài khoản",
    description="Thu hồi cả Access Token và Refresh Token",
)
def logout(
    req: Request,
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_schema),
    refresh_token: str = Header(..., alias="X-Refresh-Token"),
    db: Session = Depends(get_db),
):
    tokens = [(credentials.credentials, "access"), (refresh_token, "refresh")]

    try:
        for token, expected_type in tokens:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},
            )

            if payload.get("type") != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token không phải {expected_type} token",
                )

            token_jti = payload.get("jti")
            token_exp = payload.get("exp")

            if not token_jti or not token_exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token không hợp lệ",
                )

            existing_token = (
                db.query(RevokedToken)
                .filter(RevokedToken.token_jti == token_jti)
                .first()
            )

            if not existing_token:
                db.add(
                    RevokedToken(
                        token_jti=token_jti,
                        expires_at=datetime.fromtimestamp(
                            int(token_exp), tz=timezone.utc
                        ).replace(tzinfo=None),
                    )
                )

        db.commit()

    except ExpiredSignatureError:
        db.rollback()
        return api_repoint(
            req=req,
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Failed",
            error="Token đã hết hạn",
        )

    except JWTError:
        db.rollback()
        return api_repoint(
            req=req,
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Failed",
            error="Token không hợp lệ",
        )

    except HTTPException as e:
        db.rollback()
        return api_repoint(
            req=req, status_code=e.status_code, message="Failed", error=e.detail
        )

    except Exception:
        db.rollback()
        return api_repoint(
            req=req,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed",
            error="Không thể thực hiện đăng xuất",
        )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Đăng xuất thành công",
        data=None,
    )


@router.get("/google/login")
async def google_login(
    request: Request,
    redirect_to: str | None = None,
):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    callback_url = urlsplit(redirect_uri)
    if not callback_url.scheme or not callback_url.netloc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_REDIRECT_URI không hợp lệ",
        )

    if (
        request.url.scheme != callback_url.scheme
        or request.url.netloc != callback_url.netloc
    ):
        canonical_login_url = urlunsplit(
            (callback_url.scheme, callback_url.netloc, request.url.path, request.url.query, "")
        )
        return RedirectResponse(url=canonical_login_url)

    # Xác định đúng URL trang home.html của Frontend từ redirect_to hoặc Referer header
    target_home = None
    if redirect_to and redirect_to.startswith(("http://", "https://")):
        target_home = redirect_to
    else:
        referer = request.headers.get("referer")
        if referer and referer.startswith(("http://", "https://")):
            target_home = urljoin(referer, "home.html")

    request.session["frontend_redirect_to"] = target_home or settings.FRONTEND_HOME_URL

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        prompt="select_account",
    )


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    stage = "authorization code exchange"
    try:
        token = await oauth.google.authorize_access_token(request)

        stage = "Google user profile retrieval"
        user_info = token.get("userinfo")

        if not user_info:
            user_info = await oauth.google.userinfo(token=token)

        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google không trả về thông tin người dùng",
            )

        stage = "user account provisioning"
        result = google_login_service(user_info=dict(user_info), db=db)

        stage = "API response creation"

        # Trích xuất access_token, refresh_token từ kết quả trả về của service
        access_token = (
            result.get("access_token")
            if isinstance(result, dict)
            else result.access_token
        )
        refresh_token = (
            result.get("refresh_token")
            if isinstance(result, dict)
            else getattr(result, "refresh_token", "")
        )

        # Tạo URL chuyển hướng thẳng về trang chủ Frontend (home.html) kèm token trên query string
        target_home = request.session.pop("frontend_redirect_to", None) or settings.FRONTEND_HOME_URL
        separator = "&" if "?" in target_home else "?"
        frontend_url = (
            f"{target_home}{separator}"
            f"access_token={access_token}&refresh_token={refresh_token}"
        )

        return RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)

    except OAuthError as error:
        db.rollback()
        if error.error == "mismatching_state":
            state = request.query_params.get("state")
            state_exists_in_session = bool(
                state and request.session.get(f"_state_google_{state}")
            )
            session_cookie_present = bool(request.cookies.get("session"))
            logger.warning(
                "Google OAuth state mismatch (session_cookie_present=%s, "
                "state_exists_in_session=%s, callback_host=%s)",
                session_cookie_present,
                state_exists_in_session,
                request.url.netloc,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Phiên đăng nhập Google không khớp hoặc đã hết hạn. "
                    "Hãy mở lại /auth/google/login trong cùng trình duyệt, "
                    "không gọi callback trực tiếp và không đổi giữa localhost "
                    "và 127.0.0.1."
                ),
            ) from error

        logger.warning(
            "Google OAuth failed during %s (provider error: %s)",
            stage,
            error.error or "unknown",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                f"Đăng nhập Google thất bại tại bước {stage}: "
                f"{error.error or 'OAuth error'}"
            ),
        ) from error

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Google callback failed during %s", stage)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Đăng nhập Google thất bại tại bước {stage}",
        )
