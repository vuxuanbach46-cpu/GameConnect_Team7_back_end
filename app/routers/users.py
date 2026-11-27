from fastapi import APIRouter, status, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.api_response import api_repoint
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import UserProfileResponse

router = APIRouter(prefix="/user", tags=["Users"])


@router.get("/me" , summary="Thông tin chi tiết tài khoản" , description="Lấy thông tin chi tiết của tài khoản")
def get_curent_user(req: Request, current_user: User = Depends(get_current_user)):
    user_data = UserProfileResponse.model_validate(current_user)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Thông tin tài khoản hiện tại",
        data=user_data.model_dump(),
    )