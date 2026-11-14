"""Router cho TeamPost và TeamPostApplication.

    GET    /api/team-posts                              Danh sách bài đăng
    GET    /api/team-posts/{post_id}                   Chi tiết + danh sách đơn ứng tuyển
    POST   /api/team-posts                              Tạo bài đăng
    PUT    /api/team-posts/{post_id}                   Cập nhật bài đăng
    DELETE /api/team-posts/{post_id}                   Xoá bài đăng

    GET    /api/team-posts/{post_id}/applications      Danh sách đơn ứng tuyển
    POST   /api/team-posts/{post_id}/applications      Nộp đơn ứng tuyển
    PUT    /api/team-posts/{post_id}/applications/{id} Cập nhật trạng thái đơn
    DELETE /api/team-posts/{post_id}/applications/{id} Xoá / rút đơn
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_admin_user, get_current_user, get_optional_user
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


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def get_post_or_404(post_id: int, db: Session = Depends(get_db)):
    post = team_post_crud.get_team_post(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy bài đăng id={post_id}")
    return post


def require_post_owner(post, current_user: User) -> None:
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ chủ bài đăng mới được thực hiện thao tác này",
        )


def get_post_owner_or_admin(
    post=Depends(get_post_or_404),
    current_user: User = Depends(get_current_user),
):
    if post.user_id != current_user.id:
        get_admin_user(current_user)
    return post


def get_application_or_404(post_id: int, application_id: int, db: Session = Depends(get_db)):
    app = team_post_crud.get_application(db, application_id)
    if app is None or app.team_post_id != post_id:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đơn ứng tuyển id={application_id}")
    return app


# ---------------------------------------------------------------------------
# TeamPost endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[TeamPostOut])
def list_team_posts(
    game_id: int | None = Query(default=None, description="Lọc theo game ID"),
    region: str | None = Query(default=None, description="Lọc theo khu vực"),
    status: PostStatus | None = Query(default=PostStatus.OPEN, description="Lọc theo trạng thái"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    return team_post_crud.get_team_posts(
        db, game_id=game_id, region=region, status=status, skip=skip, limit=limit
    )


@router.get("/{post_id}", response_model=TeamPostDetailOut)
def get_team_post(
    post=Depends(get_post_or_404),
    current_user: User | None = Depends(get_optional_user),
):
    result = TeamPostDetailOut.model_validate(post)
    if current_user is None or (
        post.user_id != current_user.id and current_user.role != "ADMIN"
    ):
        return result.model_copy(update={"applications": []})
    return result


@router.post("", response_model=TeamPostOut, status_code=status.HTTP_201_CREATED)
def create_team_post(
    data: TeamPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return team_post_crud.create_team_post(
        db, data.model_copy(update={"user_id": current_user.id})
    )


@router.put("/{post_id}", response_model=TeamPostOut)
def update_team_post(
    data: TeamPostUpdate,
    post=Depends(get_post_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_post_owner(post, current_user)
    return team_post_crud.update_team_post(db, post, data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team_post(
    post=Depends(get_post_owner_or_admin),
    db: Session = Depends(get_db),
):
    team_post_crud.delete_team_post(db, post)


# ---------------------------------------------------------------------------
# TeamPostApplication endpoints
# ---------------------------------------------------------------------------

@router.get("/{post_id}/applications", response_model=list[TeamPostApplicationOut])
def list_applications(
    post_id: int,
    post=Depends(get_post_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_post_owner(post, current_user)
    return team_post_crud.get_applications_by_post(db, post_id)


@router.post(
    "/{post_id}/applications",
    response_model=TeamPostApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    post_id: int,
    data: TeamPostApplicationCreate,
    post=Depends(get_post_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if post.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bạn không thể ứng tuyển vào bài đăng của chính mình",
        )
    if post.status != PostStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bài đăng này không còn nhận đơn ứng tuyển.",
        )
    return team_post_crud.create_application(
        db, post_id, data.model_copy(update={"user_id": current_user.id})
    )


@router.put(
    "/{post_id}/applications/{application_id}",
    response_model=TeamPostApplicationOut,
)
def update_application(
    data: TeamPostApplicationUpdate,
    application=Depends(get_application_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người gửi đơn mới được cập nhật đơn ứng tuyển",
        )
    if data.status.value != "CANCELLED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Người ứng tuyển chỉ được phép rút đơn; chủ bài đăng xử lý trạng thái duyệt",
        )
    return team_post_crud.update_application_status(db, application, data)


@router.delete(
    "/{post_id}/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_application(
    application=Depends(get_application_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if application.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người gửi đơn mới được hủy đơn ứng tuyển",
        )
    team_post_crud.delete_application(db, application)
