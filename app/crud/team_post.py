"""CRUD cho TeamPost, TeamPostRole, TeamPostApplication."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

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
    status: PostStatus | None = PostStatus.OPEN,
    skip: int = 0,
    limit: int = 50,
) -> list[TeamPost]:
    """Danh sách bài đăng. Mặc định chỉ lấy OPEN."""
    query = select(TeamPost).order_by(TeamPost.created_at.desc())
    if game_id:
        query = query.where(TeamPost.game_id == game_id)
    if region:
        query = query.where(TeamPost.region.contains(region))
    if status:
        query = query.where(TeamPost.status == status)
    return list(db.scalars(query.offset(skip).limit(limit)))


def get_team_post(db: Session, post_id: int) -> TeamPost | None:
    return db.get(TeamPost, post_id)


def create_team_post(db: Session, data: TeamPostCreate) -> TeamPost:
    role_ids = data.role_ids
    post_data = data.model_dump(exclude={"role_ids"})
    post = TeamPost(**post_data)
    db.add(post)
    db.flush()  # lấy post.id trước khi thêm roles

    for role_id in role_ids:
        role = TeamPostRole(
            team_post_id=post.id,
            game_id=post.game_id,
            game_role_id=role_id,
        )
        db.add(role)

    db.commit()
    db.refresh(post)
    return post


def update_team_post(db: Session, post: TeamPost, data: TeamPostUpdate) -> TeamPost:
    update_data = data.model_dump(exclude_unset=True, exclude={"role_ids"})
    for field, value in update_data.items():
        setattr(post, field, value)

    # Nếu gửi role_ids → ghi đè toàn bộ danh sách vai trò
    if data.role_ids is not None:
        db.execute(delete(TeamPostRole).where(TeamPostRole.team_post_id == post.id))
        for role_id in data.role_ids:
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
    db: Session, team_post_id: int, data: TeamPostApplicationCreate
) -> TeamPostApplication:
    app = TeamPostApplication(team_post_id=team_post_id, **data.model_dump())
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
