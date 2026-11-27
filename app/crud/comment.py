from sqlalchemy.orm import Session

from app.crud.notification import create_notification
from app.models.comment import Comment
from app.models.post import Post
from app.schemas.comment import CommentCreate, CommentUpdate


def get_comments(
    db: Session, post_id: int, skip: int = 0, limit: int = 20
) -> list[Comment]:
    return (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_comment(db: Session, comment_id: int) -> Comment | None:
    return db.query(Comment).filter(Comment.id == comment_id).first()


def create_comment(
    db: Session,
    post: Post,
    user_id: int,
    data: CommentCreate,
) -> Comment:
    if data.parent_comment_id is not None:
        parent = get_comment(db, data.parent_comment_id)
        if parent is None or parent.post_id != post.id:
            raise ValueError("Không tìm thấy bình luận cha trong bài viết")
        if parent.parent_comment_id is not None:
            raise ValueError("Chỉ hỗ trợ trả lời bình luận gốc")

    comment = Comment(
        post_id=post.id,
        user_id=user_id,
        content=data.content,
        parent_comment_id=data.parent_comment_id,
    )
    db.add(comment)
    if post.user_id != user_id:
        create_notification(
            db,
            recipient_id=post.user_id,
            type="POST_COMMENT",
            content=f"Có bình luận mới trên bài viết #{post.id}.",
            link=f"/posts/{post.id}",
        )
    # Thông báo cho chủ bình luận gốc khi có người trả lời
    if data.parent_comment_id is not None:
        parent = get_comment(db, data.parent_comment_id)
        if parent is not None and parent.user_id != user_id:
            create_notification(
                db,
                recipient_id=parent.user_id,
                type="POST_COMMENT",
                content=f"Có trả lời mới cho bình luận của bạn trên bài viết #{post.id}.",
                link=f"/posts/{post.id}",
            )
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(
    db: Session, comment: Comment, data: CommentUpdate
) -> Comment:
    comment.content = data.content
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.commit()
