from datetime import datetime, timedelta

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Query, Session, selectinload

from app.models.block import Block
from app.models.game import Game
from app.models.comment import Comment
from app.models.friendships import Friendship
from app.models.post import Post
from app.models.post_like import PostLike
from app.models.post_game import PostGame
from app.schemas.post import PostCreate, PostUpdate


GAME_HASHTAG_ALIASES = {
    "counter-strike 2": ["counter-strike 2", "counter strike 2", "cs2"],
    "league of legends": ["league of legends", "liên minh huyền thoại", "lol"],
}


def _normalize_hashtag(value: str) -> str:
    return " ".join(value.strip().lstrip("#").casefold().split())


def _game_names_for_hashtag(hashtag: str) -> list[str]:
    normalized = _normalize_hashtag(hashtag)
    aliases = GAME_HASHTAG_ALIASES.get(normalized)
    if aliases:
        return aliases
    return [normalized]


def _visible_posts_query(
    db: Session,
    current_user_id: int | None = None,
    include_friends_posts: bool = False,
) -> Query[Post]:
    query = (
        db.query(Post)
        .options(selectinload(Post.post_games))
        .filter(Post.status == "VISIBLE")
    )
    if current_user_id is not None:
        query = query.filter(
            ~exists(
                select(Block.id).where(
                    or_(
                        and_(
                            Block.blocker_id == current_user_id,
                            Block.blocked_id == Post.user_id,
                        ),
                        and_(
                            Block.blocked_id == current_user_id,
                            Block.blocker_id == Post.user_id,
                        ),
                    )
                )
            )
        )
        if include_friends_posts:
            # Người xem được thấy bài PUBLIC của mọi người + bài FRIENDS của bạn bè
            # và bài FRIENDS/PRIVATE của chính mình
            query = query.filter(
                or_(
                    Post.visibility == "PUBLIC",
                    Post.user_id == current_user_id,
                    and_(
                        Post.visibility == "FRIENDS",
                        exists(
                            select(Friendship.id).where(
                                or_(
                                    and_(
                                        Friendship.user_a == current_user_id,
                                        Friendship.user_b == Post.user_id,
                                    ),
                                    and_(
                                        Friendship.user_b == current_user_id,
                                        Friendship.user_a == Post.user_id,
                                    )
                                )
                            )
                        ),
                    ),
                )
            )
    elif include_friends_posts:
        # Người xem chưa đăng nhập: chỉ thấy bài PUBLIC
        query = query.filter(Post.visibility == "PUBLIC")
    if current_user_id is not None and not include_friends_posts:
        # Với các nguồn khác (featured, search, ...): bài PRIVATE chỉ hiện với tác giả,
        # bài FRIENDS hiện với tác giả và bạn bè
        query = query.filter(
            or_(
                Post.visibility == "PUBLIC",
                Post.user_id == current_user_id,
                and_(
                    Post.visibility == "FRIENDS",
                    exists(
                        select(Friendship.id).where(
                            or_(
                                and_(
                                    Friendship.user_a == current_user_id,
                                    Friendship.user_b == Post.user_id,
                                ),
                                and_(
                                    Friendship.user_b == current_user_id,
                                    Friendship.user_a == Post.user_id,
                                )
                            )
                        )
                    ),
                ),
            )
        )
    elif current_user_id is None and not include_friends_posts:
        query = query.filter(Post.visibility == "PUBLIC")
    return query


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _hashtag_matches(content: str, hashtag: str) -> bool:
    normalized_content = content.casefold()
    normalized_hashtag = hashtag.strip().lstrip("#").casefold()
    if not normalized_hashtag:
        return False

    marker = f"#{normalized_hashtag}"
    start = 0
    while True:
        position = normalized_content.find(marker, start)
        if position < 0:
            return False

        before = normalized_content[position - 1] if position > 0 else ""
        end = position + len(marker)
        after = normalized_content[end] if end < len(normalized_content) else ""
        before_is_word = before.isalnum() or before == "_"
        after_is_word = after.isalnum() or after == "_"
        if not before_is_word and not after_is_word:
            return True
        start = position + 1


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


def get_feed_posts(
    db: Session,
    current_user_id: int | None,
    game_id: int | None = None,
    user_id: int | None = None,
    friends_only: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> list[Post]:
    query = _visible_posts_query(db, current_user_id)
    if game_id is not None:
        query = query.filter(Post.post_games.any(PostGame.game_id == game_id))
    if user_id is not None:
        query = query.filter(Post.user_id == user_id)
    if friends_only:
        query = query.filter(
            exists(
                select(Friendship.id).where(
                    or_(
                        and_(
                            Friendship.user_a == current_user_id,
                            Friendship.user_b == Post.user_id,
                        ),
                        and_(
                            Friendship.user_b == current_user_id,
                            Friendship.user_a == Post.user_id,
                        ),
                    )
                )
            )
        )

    return (
        query.order_by(Post.created_at.desc(), Post.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_featured_posts(
    db: Session,
    current_user_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Post]:
    since = datetime.now() - timedelta(days=7)
    recent_likes = (
        db.query(
            PostLike.post_id.label("post_id"),
            func.count(PostLike.id).label("interaction_count"),
        )
        .filter(PostLike.created_at >= since)
        .group_by(PostLike.post_id)
        .subquery()
    )
    recent_comments = (
        db.query(
            Comment.post_id.label("post_id"),
            func.count(Comment.id).label("interaction_count"),
        )
        .filter(Comment.created_at >= since)
        .group_by(Comment.post_id)
        .subquery()
    )
    like_count = func.coalesce(recent_likes.c.interaction_count, 0)
    comment_count = func.coalesce(recent_comments.c.interaction_count, 0)
    interaction_count = like_count + comment_count

    return (
        _visible_posts_query(db, current_user_id)
        .outerjoin(recent_likes, Post.id == recent_likes.c.post_id)
        .outerjoin(recent_comments, Post.id == recent_comments.c.post_id)
        .filter(interaction_count > 0)
        .order_by(interaction_count.desc(), Post.created_at.desc(), Post.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def search_posts(
    db: Session,
    keyword: str | None = None,
    hashtag: str | None = None,
    current_user_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Post]:
    query = _visible_posts_query(db, current_user_id)
    if keyword:
        content_match = Post.content.ilike(
            f"%{_escape_like(keyword.lstrip('#'))}%",
            escape="\\",
        )
        game_aliases = _game_names_for_hashtag(keyword)
        game_alias_conditions = [
            func.lower(Game.name).ilike(
                f"%{_escape_like(alias).lower()}%",
                escape="\\",
            )
            for alias in game_aliases
        ]
        game_match = exists(
            select(PostGame.post_id).join(
                Game,
                Game.id == PostGame.game_id,
            ).where(
                PostGame.post_id == Post.id,
                or_(*game_alias_conditions),
            )
        )
        query = query.filter(or_(content_match, game_match))
    if hashtag:
        normalized_hashtag = hashtag.strip().lstrip("#")
        game_aliases = _game_names_for_hashtag(normalized_hashtag)
        game_alias_conditions = [
            func.lower(Game.name).ilike(
                f"%{_escape_like(alias).lower()}%",
                escape="\\",
            )
            for alias in game_aliases
        ]
        game_match = (
            exists(
                select(PostGame.post_id).join(
                    Game,
                    Game.id == PostGame.game_id,
                ).where(
                    PostGame.post_id == Post.id,
                    or_(*game_alias_conditions),
                )
            )
        )
        content_match = Post.content.ilike(
            f"%#{_escape_like(normalized_hashtag)}%",
            escape="\\",
        )
        query = query.filter(or_(content_match, game_match))
        posts = (
            query.order_by(Post.created_at.desc(), Post.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return posts

    return (
        query.order_by(Post.created_at.desc(), Post.id.desc())
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
    image_urls = data.image_urls or ([data.image_url] if data.image_url else [])
    post = Post(
        user_id=user_id,
        content=data.content,
        image_url=image_urls[0] if image_urls else None,
        image_urls=image_urls,
        status=data.status.value,
        visibility=data.visibility.value,
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

    if image_urls is not None:
        if image_url and image_url not in image_urls:
            image_urls = [image_url, *image_urls]
        if len(image_urls) > 4:
            raise ValueError("Chỉ được đính kèm tối đa 4 ảnh")
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
        if field == "visibility" and value is not None:
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
