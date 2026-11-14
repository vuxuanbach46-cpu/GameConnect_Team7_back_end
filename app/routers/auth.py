from fastapi import APIRouter, Depends, Request, status, Header
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
from app.core.security import oauth2_schema

router = APIRouter(prefix="/auth", tags=["AUTH"])


@router.post(
    "/register",
    summary="Đăng ký tài khoản",
    description="Người dùng nhập thông tin để đăng kí tài khoản",
)
def create_register(req: Request, info: UserRegisterRequest, db=Depends(get_db)):
    user_new = create_register_service(info=info, db=db)
    user_new = UserRegisterResponse.model_validate(user_new)
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Đăng kí tài khoản thành công",
        data=user_new,
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


@router.post(
    "/login",
    summary="Đăng nhập tài khoản",
    description="Nhập thông tin đã đăng kí để đăng nhập dùng các api",
)
@limiter.limit("5/minute")
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
