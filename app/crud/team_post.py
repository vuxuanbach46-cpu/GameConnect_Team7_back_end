"""CRUD cho TeamPost và TeamPostApplication."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.team_post import ApplicationStatus, PostStatus, TeamPost, TeamPostApplication
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
    game: str | None = None,
    region: str | None = None,
    status: PostStatus | None = PostStatus.OPEN,
    skip: int = 0,
    limit: int = 50,
) -> list[TeamPost]:
    """Danh sách bài đăng, mặc định chỉ lấy OPEN. Lọc theo game/region tuỳ chọn."""
    query = select(TeamPost).order_by(TeamPost.created_at.desc())
    if game:
        query = query.where(TeamPost.game.contains(game))
    if region:
        query = query.where(TeamPost.region.contains(region))
    if status:
        query = query.where(TeamPost.status == status)
    query = query.offset(skip).limit(limit)
    return list(db.scalars(query))


def get_team_post(db: Session, post_id: int) -> TeamPost | None:
    return db.get(TeamPost, post_id)


def create_team_post(db: Session, data: TeamPostCreate) -> TeamPost:
    post = TeamPost(**data.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def update_team_post(db: Session, post: TeamPost, data: TeamPostUpdate) -> TeamPost:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
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
    query = select(TeamPostApplication).where(
        TeamPostApplication.post_id == post_id
    ).order_by(TeamPostApplication.created_at.asc())
    return list(db.scalars(query))


def get_application(db: Session, application_id: int) -> TeamPostApplication | None:
    return db.get(TeamPostApplication, application_id)


def create_application(
    db: Session, post_id: int, data: TeamPostApplicationCreate
) -> TeamPostApplication:
    app = TeamPostApplication(post_id=post_id, **data.model_dump())
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
