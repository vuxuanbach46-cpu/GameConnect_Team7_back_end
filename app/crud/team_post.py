"""CRUD cho TeamPost, TeamPostRole, TeamPostApplication.

Bao gồm đầy đủ các quy tắc nghiệp vụ (Business Rules) và validation:
- Validate game theo danh mục game
- Validate rank tối thiểu / tối đa theo game
- Validate vai trò theo game
- Validate số người cần 1–9 người
- Validate hạn hiển thị tối đa 7 ngày
- Mỗi user tối đa 3 bài đăng đang mở (OPEN)
"""
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.team_post import (
    ApplicationStatus,
    PostStatus,
    TeamPost,
    TeamPostApplication,
    TeamPostRole,
)
from app.schemas.team_post import (
    TeamPostApplicationCreate,
    TeamPostApplicationUpdate,
    TeamPostCreate,
    TeamPostUpdate,
)


# ---------------------------------------------------------------------------
# TeamPost CRUD
# ---------------------------------------------------------------------------

def get_team_posts(
    db: Session,
    game_id: int | None = None,
    region: str | None = None,
    status_filter: PostStatus | None = PostStatus.OPEN,
    skip: int = 0,
    limit: int = 50,
) -> list[TeamPost]:
    """Danh sách bài đăng. Mặc định chỉ lấy OPEN."""
    query = select(TeamPost).order_by(TeamPost.created_at.desc())
    if game_id:
        query = query.where(TeamPost.game_id == game_id)
    if region:
        query = query.where(TeamPost.region.contains(region))
    if status_filter:
        query = query.where(TeamPost.status == status_filter)
    return list(db.scalars(query.offset(skip).limit(limit)))


def get_team_post(db: Session, post_id: int) -> TeamPost | None:
    return db.get(TeamPost, post_id)


def create_team_post(
    db: Session,
    data: TeamPostCreate,
    user_id: int,
) -> TeamPost:
    """Tạo bài đăng tìm đội kèm đầy đủ business validation."""
    # 1. Kiểm tra giới hạn: Mỗi user tối đa 3 bài đang mở (PostStatus.OPEN)
    open_posts_count = (
        db.query(TeamPost)
        .filter(TeamPost.user_id == user_id, TeamPost.status == PostStatus.OPEN)
        .count()
    )
    if open_posts_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mỗi người dùng chỉ được có tối đa 3 bài đăng tìm đội đang mở (OPEN)",
        )

    # 2. Validate game theo danh mục game
    game = db.get(Game, data.game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trò chơi (game_id={data.game_id}) không tồn tại trong hệ thống",
        )

    # 3. Validate rank theo danh mục game
    min_rank = None
    max_rank = None
    if data.min_rank_id is not None:
        min_rank = db.get(GameRank, data.min_rank_id)
        if not min_rank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối thiểu (id={data.min_rank_id}) không tồn tại",
            )
        if min_rank.game_id != data.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối thiểu '{min_rank.rank_name}' không thuộc game '{game.name}'",
            )

    if data.max_rank_id is not None:
        max_rank = db.get(GameRank, data.max_rank_id)
        if not max_rank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối đa (id={data.max_rank_id}) không tồn tại",
            )
        if max_rank.game_id != data.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rank tối đa '{max_rank.rank_name}' không thuộc game '{game.name}'",
            )

    if min_rank and max_rank and min_rank.rank_order > max_rank.rank_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rank tối thiểu ({min_rank.rank_name}) không được cao hơn rank tối đa ({max_rank.rank_name})",
        )

    # 4. Validate vai trò (role_ids) theo danh mục game
    unique_role_ids = list(dict.fromkeys(data.role_ids))
    for r_id in unique_role_ids:
        role = db.get(GameRole, r_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vai trò (id={r_id}) không tồn tại",
            )
        if role.game_id != data.game_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vai trò '{role.role_name}' không thuộc game '{game.name}'",
            )

    # 5. Validate số người cần 1–9 người
    if data.needed_players < 1 or data.needed_players > 9:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số lượng thành viên cần tuyển phải từ 1 đến 9 người",
        )

    # 6. Validate hạn hiển thị tối đa 7 ngày
    now = datetime.now()
    max_expiry = now + timedelta(days=7)

    if data.expires_at is None:
        expires_at = max_expiry
    else:
        user_expiry = (
            data.expires_at.replace(tzinfo=None)
            if data.expires_at.tzinfo
            else data.expires_at
        )
        if user_expiry <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng phải lớn hơn thời điểm hiện tại",
            )
        if user_expiry > max_expiry + timedelta(minutes=5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng tối đa không được vượt quá 7 ngày kể từ hiện tại",
            )
        expires_at = user_expiry

    # 7. Lưu bài đăng
    post = TeamPost(
        user_id=user_id,
        game_id=data.game_id,
        title=data.title,
        min_rank_id=data.min_rank_id,
        max_rank_id=data.max_rank_id,
        needed_players=data.needed_players,
        play_time=data.play_time,
        region=data.region,
        description=data.description,
        status=PostStatus.OPEN,
        expires_at=expires_at,
    )
    db.add(post)
    db.flush()

    for r_id in unique_role_ids:
        role = TeamPostRole(
            team_post_id=post.id,
            game_id=post.game_id,
            game_role_id=r_id,
        )
        db.add(role)

    db.commit()
    db.refresh(post)
    return post


def update_team_post(db: Session, post: TeamPost, data: TeamPostUpdate) -> TeamPost:
    """Cập nhật bài đăng tìm đội."""
    if data.needed_players is not None and (data.needed_players < 1 or data.needed_players > 9):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Số lượng thành viên cần tuyển phải từ 1 đến 9 người",
        )

    if data.expires_at is not None:
        now = datetime.now()
        max_expiry = now + timedelta(days=7)
        user_expiry = (
            data.expires_at.replace(tzinfo=None)
            if data.expires_at.tzinfo
            else data.expires_at
        )
        if user_expiry <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng phải lớn hơn thời điểm hiện tại",
            )
        if user_expiry > max_expiry + timedelta(minutes=5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hạn hiển thị bài đăng tối đa không được vượt quá 7 ngày kể từ hiện tại",
            )

    update_data = data.model_dump(exclude_unset=True, exclude={"role_ids"})
    for field, value in update_data.items():
        setattr(post, field, value)

    # Nếu gửi role_ids → ghi đè toàn bộ danh sách vai trò
    if data.role_ids is not None:
        unique_role_ids = list(dict.fromkeys(data.role_ids))
        for r_id in unique_role_ids:
            role = db.get(GameRole, r_id)
            if not role or role.game_id != post.game_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Vai trò (id={r_id}) không thuộc trò chơi của bài đăng này",
                )
        db.execute(delete(TeamPostRole).where(TeamPostRole.team_post_id == post.id))
        for role_id in unique_role_ids:
            role = TeamPostRole(
                team_post_id=post.id,
                game_id=post.game_id,
                game_role_id=role_id,
            )
            db.add(role)

    db.commit()
    db.refresh(post)
    return post


def delete_team_post(db: Session, post: TeamPost) -> None:
    db.delete(post)
    db.commit()


# ---------------------------------------------------------------------------
# TeamPostApplication CRUD
# ---------------------------------------------------------------------------

def get_applications_by_post(db: Session, post_id: int) -> list[TeamPostApplication]:
    query = (
        select(TeamPostApplication)
        .where(TeamPostApplication.team_post_id == post_id)
        .order_by(TeamPostApplication.created_at.asc())
    )
    return list(db.scalars(query))


def get_application(db: Session, application_id: int) -> TeamPostApplication | None:
    return db.get(TeamPostApplication, application_id)


def create_application(
    db: Session, team_post_id: int, user_id: int, data: TeamPostApplicationCreate
) -> TeamPostApplication:
    # Kiểm tra bài đăng có đang OPEN không
    post = db.get(TeamPost, team_post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Bài đăng không tồn tại")
    if post.status != PostStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bài đăng không còn mở nhận ứng tuyển",
        )
    if post.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể tự ứng tuyển vào bài đăng của chính mình",
        )

    # Kiểm tra đã ứng tuyển trước đó chưa
    existing_app = (
        db.query(TeamPostApplication)
        .filter(
            TeamPostApplication.team_post_id == team_post_id,
            TeamPostApplication.user_id == user_id,
        )
        .first()
    )
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đã gửi đơn ứng tuyển vào bài đăng này rồi",
        )

    app = TeamPostApplication(
        team_post_id=team_post_id,
        user_id=user_id,
        message=data.message,
        status=ApplicationStatus.PENDING,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_application_status(
    db: Session, application: TeamPostApplication, data: TeamPostApplicationUpdate
) -> TeamPostApplication:
    application.status = data.status
    db.commit()
    db.refresh(application)
    return application


def delete_application(db: Session, application: TeamPostApplication) -> None:
    db.delete(application)
    db.commit()
