from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.game import Game
from app.models.comment import Comment
from app.models.post import Post
from app.models.post_like import PostLike
from app.models.post_game import PostGame
from app.schemas.post import PostCreate, PostUpdate


def get_posts(db: Session, skip: int = 0, limit: int = 20) -> list[Post]:
    return (
        db.query(Post)
        .options(selectinload(Post.post_games))
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_visible_posts(db: Session, skip: int = 0, limit: int = 20) -> list[Post]:
    return (
        db.query(Post)
        .options(selectinload(Post.post_games))
        .filter(Post.status == "VISIBLE")
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_post(db: Session, post_id: int) -> Post | None:
    return (
        db.query(Post)
        .options(selectinload(Post.post_games))
        .filter(Post.id == post_id)
        .first()
    )


def _set_games(db: Session, post: Post, game_ids: list[int]) -> None:
    unique_ids = list(dict.fromkeys(game_ids))
    found_ids = {
        row[0] for row in db.query(Game.id).filter(Game.id.in_(unique_ids)).all()
    } if unique_ids else set()
    missing_ids = set(unique_ids) - found_ids
    if missing_ids:
        raise ValueError(f"Không tìm thấy game id: {', '.join(map(str, sorted(missing_ids)))}")
    post.post_games = [PostGame(game_id=game_id) for game_id in unique_ids]


def create_post(db: Session, data: PostCreate, user_id: int) -> Post:
    if data.image_urls and data.image_url:
        raise ValueError("Chỉ được truyền image_url hoặc image_urls")
    image_urls = data.image_urls or ([data.image_url] if data.image_url else [])
    post = Post(
        user_id=user_id,
        content=data.content,
        image_url=image_urls[0] if image_urls else None,
        image_urls=image_urls,
        status=data.status.value,
    )
    try:
        _set_games(db, post, data.game_ids)
    except ValueError:
        db.rollback()
        raise
    db.add(post)
    db.commit()
    db.refresh(post)
    created_post = get_post(db, post.id)
    if created_post is None:
        raise RuntimeError("Không thể tải bài viết vừa tạo")
    return created_post


def update_post(db: Session, post: Post, data: PostUpdate) -> Post:
    updates = data.model_dump(exclude_unset=True)
    game_ids = updates.pop("game_ids", None)
    image_urls = updates.pop("image_urls", None)
    image_url_was_set = "image_url" in updates
    image_url = updates.pop("image_url", None)

    if image_urls is not None and image_url_was_set:
        raise ValueError("Chỉ được truyền image_url hoặc image_urls")
    if image_urls is not None:
        updates["image_urls"] = image_urls
        updates["image_url"] = image_urls[0] if image_urls else None
    elif image_url_was_set:
        updates["image_urls"] = [image_url] if image_url else []
        updates["image_url"] = image_url

    if game_ids is not None:
        unique_ids = set(game_ids)
        found_ids = {
            row[0] for row in db.query(Game.id).filter(Game.id.in_(unique_ids)).all()
        } if unique_ids else set()
        missing_ids = unique_ids - found_ids
        if missing_ids:
            raise ValueError(
                f"Không tìm thấy game id: {', '.join(map(str, sorted(missing_ids)))}"
            )

    for field, value in updates.items():
        if field == "status" and value is not None:
            value = value.value
        if field == "content" and value is None:
            continue
        setattr(post, field, value)
    if game_ids is not None:
        post.post_games = [
            PostGame(game_id=game_id) for game_id in dict.fromkeys(game_ids)
        ]
    db.commit()
    db.refresh(post)
    updated_post = get_post(db, post.id)
    if updated_post is None:
        raise RuntimeError("Không thể tải bài viết vừa cập nhật")
    return updated_post


def delete_post(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()


def get_post_counts(db: Session, post_id: int) -> tuple[int, int]:
    like_count = db.query(PostLike.id).filter(PostLike.post_id == post_id).count()
    comment_count = db.query(Comment.id).filter(Comment.post_id == post_id).count()
    return like_count, comment_count


def get_post_counts_by_id(db: Session, post_ids: list[int]) -> dict[int, tuple[int, int]]:
    if not post_ids:
        return {}
    like_counts = dict(
        db.query(PostLike.post_id, func.count(PostLike.id))
        .filter(PostLike.post_id.in_(post_ids))
        .group_by(PostLike.post_id)
        .all()
    )
    comment_counts = dict(
        db.query(Comment.post_id, func.count(Comment.id))
        .filter(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
        .all()
    )
    return {
        post_id: (like_counts.get(post_id, 0), comment_counts.get(post_id, 0))
        for post_id in post_ids
    }
