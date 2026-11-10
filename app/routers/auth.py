from fastapi import APIRouter, Depends, Request, status
from app.schemas.auth import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse,
)
from app.db.session import get_db
from app.crud.auth import create_register_service, login_service
from app.schemas.api_response import api_repoint
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.security import refresh_access_token
from app.core.limiter import limiter


router = APIRouter(prefix="/auth", tags=["AUTH"])

oauth2_schema = HTTPBearer()


@router.post("/register" , summary="Đăng ký tài khoản" , description="Người dùng nhập thông tin để đăng kí tài khoản")
def create_register(req: Request, info: UserRegisterRequest, db=Depends(get_db)):
    user_new = create_register_service(info=info, db=db)
    user_new = UserRegisterResponse.model_validate(user_new)
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Đăng kí tài khoản thành công",
        data=user_new,
    )


@router.post("/login" , summary="Đăng nhập tài khoản" , description="Nhập thông tin đã đăng kí để đăng nhập dùng các api")
@limiter.limit("5/minute")
def login(request: Request, info: UserLoginRequest, db=Depends(get_db)):
    user_login = UserLoginResponse.model_validate(login_service(info=info, db=db))
    return api_repoint(
        req=request,
        status_code=status.HTTP_200_OK,
        message="Đăng nhập thành công",
        data=user_login,
    )


@router.post("/refresh" , summary="Cập lại token" , description="Nếu token hết hạn , không phải đăng nhập lại ")
def create_refresh_token(
    req: Request,
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_schema),
    db: Session = Depends(get_db),
):
    new_access_token = refresh_access_token(credentials=credentials, db=db)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Cấp lại access token thành công",
        data=new_access_token,
    )
