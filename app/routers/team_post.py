"""Router cho TeamPost và TeamPostApplication.

    GET    /api/team-posts                              Danh sách bài đăng
    GET    /api/team-posts/{post_id}                   Chi tiết + danh sách đơn ứng tuyển
    POST   /api/team-posts                              Tạo bài đăng (có validate đầy đủ)
    PUT    /api/team-posts/{post_id}                   Cập nhật bài đăng
    PATCH  /api/team-posts/{post_id}/close             Đóng bài đăng sớm
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
from app.models.team_post import PostStatus, TeamPost
from app.models.user import User
from app.schemas.team_post import (
    TeamPostApplicationCreate,
    TeamPostApplicationOut,
    TeamPostApplicationUpdate,
    TeamPostCreate,
    TeamPostDetailOut,
    TeamPostOut,
    TeamPostPaginationOut,
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


def verify_post_owner(
    post: TeamPost,
    current_user: User | None,
    acting_user_id: int | None = None,
    action: str = "chỉnh sửa",
) -> None:
    """Kiểm tra quyền sở hữu bài đăng (BR07).

    Chỉ chủ bài đăng (post.user_id) hoặc quản trị viên (ADMIN) mới có quyền thao tác.
    """
    if current_user and getattr(current_user, "role", None) == "ADMIN":
        return

    effective_id = current_user.id if current_user else acting_user_id
    if not effective_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Vui lòng đăng nhập hoặc cung cấp user_id để {action} bài đăng",
        )
    if post.user_id != effective_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Chỉ chủ bài đăng mới có quyền {action} bài đăng này",
        )


# ---------------------------------------------------------------------------
# TeamPost endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=TeamPostPaginationOut, summary="Tìm kiếm và phân trang bài đăng tìm đội")
def list_team_posts(
    game_id: int | None = Query(default=None, description="Lọc theo game ID"),
    rank_id: int | None = Query(
        default=None,
        description="Lọc theo rank người chơi (phù hợp khoảng min_rank - max_rank của bài)",
    ),
    min_rank_id: int | None = Query(default=None, description="Lọc theo min_rank_id cụ thể"),
    max_rank_id: int | None = Query(default=None, description="Lọc theo max_rank_id cụ thể"),
    role_id: int | None = Query(
        default=None, description="Lọc theo vai trò cần tuyển (game_role_id)"
    ),
    play_time: str | None = Query(default=None, description="Lọc theo khung giờ chơi (vd: 20:00)"),
    region: str | None = Query(default=None, description="Lọc theo khu vực / máy chủ (vd: VN)"),
    q: str | None = Query(default=None, description="Tìm kiếm từ khóa theo tiêu đề hoặc mô tả"),
    status_filter: PostStatus | None = Query(
        default=PostStatus.OPEN,
        alias="status",
        description="Lọc theo trạng thái bài đăng (mặc định chỉ OPEN)",
    ),
    include_expired: bool = Query(
        default=False,
        description="Bao gồm cả bài đăng đã hết hạn (mặc định False: chỉ lấy bài còn hạn)",
    ),
    page: int = Query(default=1, ge=1, description="Số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số bài mỗi trang"),
    skip: int | None = Query(default=None, ge=0, description="Hỗ trợ tương thích skip (tùy chọn)"),
    limit: int | None = Query(default=None, ge=1, le=200, description="Hỗ trợ tương thích limit (tùy chọn)"),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """API Tìm kiếm và lọc bài đăng tìm đồng đội.

    Đặc điểm:
    - Tìm kiếm theo game, rank, vai trò, giờ chơi, khu vực, từ khóa.
    - Mặc định chỉ lấy bài OPEN và còn hạn (expires_at > hiện tại).
    - Sắp xếp mới nhất (created_at DESC).
    - Phân trang đầy đủ (total, page, page_size, total_pages, items).
    """
    eff_page_size = limit if limit is not None else page_size
    eff_page = (skip // eff_page_size) + 1 if skip is not None else page

    items, total = team_post_crud.get_team_posts(
        db,
        game_id=game_id,
        rank_id=rank_id,
        min_rank_id=min_rank_id,
        max_rank_id=max_rank_id,
        role_id=role_id,
        play_time=play_time,
        region=region,
        q=q,
        status_filter=status_filter,
        include_expired=include_expired,
        page=eff_page,
        page_size=eff_page_size,
    )

    total_pages = (total + eff_page_size - 1) // eff_page_size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": eff_page,
        "page_size": eff_page_size,
        "total_pages": total_pages,
    }


@router.get("/{post_id}", response_model=TeamPostDetailOut, summary="Chi tiết bài đăng tìm đội")
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


@router.post(
    "",
    response_model=TeamPostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo bài đăng tìm đội mới",
)
def create_team_post(
    data: TeamPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """API Tạo bài đăng tìm đội.

    Quy tắc nghiệp vụ:
    - Validate game theo danh mục game (game_id tồn tại).
    - Validate rank tối thiểu/tối đa theo game (thuộc game đã chọn, min_rank <= max_rank).
    - Validate vai trò (role_ids) theo danh mục game.
    - Số người cần tuyển: từ 1 đến 50 người.
    - Hạn hiển thị: tối đa 7 ngày kể từ thời điểm hiện tại.
    - Giới hạn: mỗi user tối đa 3 bài đăng đang mở (OPEN).
    """
    return team_post_crud.create_team_post(
        db, data.model_copy(update={"user_id": current_user.id})
    )


@router.put("/{post_id}", response_model=TeamPostOut, summary="Cập nhật bài đăng tìm đội (chỉ chủ bài)")
def update_team_post(
    data: TeamPostUpdate,
    post=Depends(get_post_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật bài đăng tìm đội. Chỉ chủ bài đăng (poster) hoặc ADMIN mới có quyền."""
    verify_post_owner(post, current_user, action="chỉnh sửa")
    return team_post_crud.update_team_post(db, post, data)


@router.patch("/{post_id}/close", response_model=TeamPostOut, summary="Đóng bài đăng sớm (chỉ chủ bài)")
@router.post("/{post_id}/close", response_model=TeamPostOut, summary="Đóng bài đăng sớm (chỉ chủ bài)", include_in_schema=False)
def close_team_post(
    post_id: int,
    post: TeamPost = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Đóng bài đăng tìm đội sớm (chuyển status thành CLOSED). Chỉ chủ bài đăng hoặc ADMIN mới có quyền."""
    verify_post_owner(post, current_user, action="đóng")
    return team_post_crud.close_team_post(db, post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xóa bài đăng tìm đội (chỉ chủ bài)")
def delete_team_post(
    post=Depends(get_post_owner_or_admin),
    db: Session = Depends(get_db),
):
    """Xóa bài đăng tìm đội. Chỉ chủ bài đăng hoặc ADMIN mới có quyền."""
    team_post_crud.delete_team_post(db, post)


# ---------------------------------------------------------------------------
# TeamPostApplication endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{post_id}/applications",
    response_model=list[TeamPostApplicationOut],
    summary="Danh sách đơn ứng tuyển của bài đăng",
)
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
    summary="Nộp đơn ứng tuyển vào bài đăng",
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
            detail="Bài đăng đã đóng hoặc hết hạn, không thể ứng tuyển",
        )
    return team_post_crud.create_application(
        db, post_id, data.model_copy(update={"user_id": current_user.id})
    )


@router.put(
    "/{post_id}/applications/{application_id}",
    response_model=TeamPostApplicationOut,
    summary="Cập nhật trạng thái đơn ứng tuyển",
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
    summary="Xóa / rút đơn ứng tuyển",
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
