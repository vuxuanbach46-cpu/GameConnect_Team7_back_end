from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.notification import create_notification
from app.models.post import Post
from app.models.post_like import PostLike


def create_post_like(
    db: Session, post: Post, user_id: int
) -> tuple[PostLike, bool]:
    existing = (
        db.query(PostLike)
        .filter(PostLike.post_id == post.id, PostLike.user_id == user_id)
        .first()
    )
    if existing is not None:
        return existing, False

    like = PostLike(post_id=post.id, user_id=user_id)
    db.add(like)
    if post.user_id != user_id:
        create_notification(
            db,
            recipient_id=post.user_id,
            type="POST_LIKE",
            content=f"Có lượt thích mới trên bài viết #{post.id}.",
            link=f"/posts/{post.id}",
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(PostLike)
            .filter(PostLike.post_id == post.id, PostLike.user_id == user_id)
            .first()
        )
        if existing is None:
            raise
        return existing, False

    db.refresh(like)
    return like, True


def delete_post_like(db: Session, post_id: int, user_id: int) -> bool:
    like = (
        db.query(PostLike)
        .filter(PostLike.post_id == post_id, PostLike.user_id == user_id)
        .first()
    )
    if like is None:
        return False
    db.delete(like)
    db.commit()
    return True
