from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.crud.admin_user import list_users, lock_user, unlock_user
from app.db.session import get_db
from app.models.user import User, UserStatus
from app.schemas.admin_user import AdminUserItem, AdminUserPage, LockUserRequest
from app.schemas.api_response import api_repoint


router = APIRouter(
    prefix="/api/admin/users",
    tags=["Admin - Users"],
    dependencies=[Depends(get_current_user), Depends(require_admin)],
)


@router.get("", summary="Danh sách người dùng")
def get_users(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    user_status: UserStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    users, total, total_pages = list_users(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status_filter=user_status,
    )
    data = AdminUserPage(
        items=[AdminUserItem.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
    return api_repoint(
        req=request,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách người dùng thành công",
        data=data.model_dump(mode="json"),
    )


@router.patch("/{user_id}/lock", summary="Khóa tài khoản người dùng")
def lock_user_account(
    user_id: int,
    info: LockUserRequest,
    request: Request,
    admin: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = lock_user(
        db=db,
        user_id=user_id,
        duration_days=info.duration_days,
        reason=info.reason,
        admin_id=admin.id,
    )
    return api_repoint(
        req=request,
        status_code=status.HTTP_200_OK,
        message="Khóa tài khoản thành công",
        data=AdminUserItem.model_validate(user).model_dump(mode="json"),
    )


@router.patch("/{user_id}/unlock", summary="Mở khóa tài khoản người dùng")
def unlock_user_account(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = unlock_user(db=db, user_id=user_id)
    return api_repoint(
        req=request,
        status_code=status.HTTP_200_OK,
        message="Mở khóa tài khoản thành công",
        data=AdminUserItem.model_validate(user).model_dump(mode="json"),
    )
