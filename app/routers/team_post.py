"""Router cho TeamPost và TeamPostApplication.

    GET    /api/team-posts                              Danh sách bài đăng
    GET    /api/team-posts/{post_id}                   Chi tiết + danh sách đơn ứng tuyển
    POST   /api/team-posts                              Tạo bài đăng (có validate đầy đủ)
    PUT    /api/team-posts/{post_id}                   Cập nhật bài đăng
    DELETE /api/team-posts/{post_id}                   Xoá bài đăng

    GET    /api/team-posts/{post_id}/applications      Danh sách đơn ứng tuyển
    POST   /api/team-posts/{post_id}/applications      Nộp đơn ứng tuyển
    PUT    /api/team-posts/{post_id}/applications/{id} Cập nhật trạng thái đơn
    DELETE /api/team-posts/{post_id}/applications/{id} Xoá / rút đơn
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import team_post as team_post_crud
from app.db.session import get_db
from app.models.team_post import PostStatus
from app.models.user import User
from app.schemas.team_post import (
    TeamPostApplicationCreate,
    TeamPostApplicationOut,
    TeamPostApplicationUpdate,
    TeamPostCreate,
    TeamPostDetailOut,
    TeamPostOut,
    TeamPostUpdate,
)

router = APIRouter(prefix="/team-posts", tags=["Team Posts"])

optional_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Lấy user hiện tại từ JWT token nếu có (không bắt buộc nếu truyền user_id)."""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None


def get_post_or_404(post_id: int, db: Session = Depends(get_db)):
    post = team_post_crud.get_team_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy bài đăng id={post_id}")
    return post


def get_application_or_404(post_id: int, application_id: int, db: Session = Depends(get_db)):
    app = team_post_crud.get_application(db, application_id)
    if app is None or app.team_post_id != post_id:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đơn ứng tuyển id={application_id}")
    return app


# ---------------------------------------------------------------------------
# TeamPost endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[TeamPostOut], summary="Danh sách bài đăng tìm đội")
def list_team_posts(
    game_id: int | None = Query(default=None, description="Lọc theo game ID"),
    region: str | None = Query(default=None, description="Lọc theo khu vực"),
    status_filter: PostStatus | None = Query(
        default=PostStatus.OPEN, alias="status", description="Lọc theo trạng thái bài đăng"
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return team_post_crud.get_team_posts(
        db, game_id=game_id, region=region, status_filter=status_filter, skip=skip, limit=limit
    )


@router.get("/{post_id}", response_model=TeamPostDetailOut, summary="Chi tiết bài đăng tìm đội")
def get_team_post(post=Depends(get_post_or_404)):
    return post


@router.post(
    "",
    response_model=TeamPostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bài đăng tìm đội mới",
)
def create_team_post(
    data: TeamPostCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """API Tạo bài đăng tìm đội.

    Quy tắc nghiệp vụ:
    - Validate game theo danh mục game (game_id tồn tại).
    - Validate rank tối thiểu/tối đa theo game (thuộc game đã chọn, min_rank <= max_rank).
    - Validate vai trò (role_ids) theo danh mục game.
    - Số người cần tuyển: từ 1 đến 9 người.
    - Hạn hiển thị: tối đa 7 ngày kể từ thời điểm hiện tại.
    - Giới hạn: mỗi user tối đa 3 bài đăng đang mở (OPEN).
    """
    user_id = current_user.id if current_user else data.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vui lòng đăng nhập hoặc cung cấp user_id để tạo bài đăng",
        )

    # Kiểm tra user hợp lệ trong hệ thống
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Người dùng id={user_id} không tồn tại trong hệ thống",
        )
    if getattr(user, "status", None) == "LOCKED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đã bị khóa, không thể tạo bài đăng",
        )

    return team_post_crud.create_team_post(db, data, user_id=user_id)


@router.put("/{post_id}", response_model=TeamPostOut, summary="Cập nhật bài đăng tìm đội")
def update_team_post(
    data: TeamPostUpdate,
    post=Depends(get_post_or_404),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user and post.user_id != current_user.id and getattr(current_user, "role", None) != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ bài đăng mới có quyền chỉnh sửa bài đăng này",
        )
    return team_post_crud.update_team_post(db, post, data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa bài đăng tìm đội")
def delete_team_post(
    post=Depends(get_post_or_404),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if current_user and post.user_id != current_user.id and getattr(current_user, "role", None) != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ bài đăng mới có quyền xóa bài đăng này",
        )
    team_post_crud.delete_team_post(db, post)


# ---------------------------------------------------------------------------
# TeamPostApplication endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{post_id}/applications",
    response_model=list[TeamPostApplicationOut],
    summary="Danh sách đơn ứng tuyển của bài đăng",
)
def list_applications(post_id: int, db: Session = Depends(get_db)):
    return team_post_crud.get_applications_by_post(db, post_id)


@router.post(
    "/{post_id}/applications",
    response_model=TeamPostApplicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Nộp đơn ứng tuyển vào bài đăng",
)
def create_application(
    post_id: int,
    data: TeamPostApplicationCreate,
    post=Depends(get_post_or_404),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    user_id = current_user.id if current_user else data.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vui lòng đăng nhập hoặc cung cấp user_id để ứng tuyển",
        )
    return team_post_crud.create_application(db, post_id, user_id=user_id, data=data)


@router.put(
    "/{post_id}/applications/{application_id}",
    response_model=TeamPostApplicationOut,
    summary="Cập nhật trạng thái đơn ứng tuyển",
)
def update_application(
    data: TeamPostApplicationUpdate,
    application=Depends(get_application_or_404),
    db: Session = Depends(get_db),
):
    return team_post_crud.update_application_status(db, application, data)


@router.delete(
    "/{post_id}/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa / rút đơn ứng tuyển",
)
def delete_application(
    application=Depends(get_application_or_404),
    db: Session = Depends(get_db),
):
    team_post_crud.delete_application(db, application)
