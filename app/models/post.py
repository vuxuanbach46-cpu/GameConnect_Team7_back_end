from datetime import datetime
import enum

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PostStatus(str, enum.Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint("status IN ('VISIBLE', 'HIDDEN')", name="ck_posts_status"),
        Index("ix_posts_user_created", "user_id", "created_at"),
        Index("ix_posts_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default=PostStatus.VISIBLE.value
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    likes: Mapped[list["PostLike"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )
    post_games: Mapped[list["PostGame"]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class PostGame(Base):
    __tablename__ = "post_games"

    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )

    post: Mapped[Post] = relationship(back_populates="post_games")


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_post_created", "post_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    post: Mapped[Post] = relationship(back_populates="comments")
    parent_comment: Mapped["Comment | None"] = relationship(
        remote_side="Comment.id", back_populates="replies"
    )
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent_comment",
        cascade="all, delete-orphan", single_parent=True
    )


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    post: Mapped[Post] = relationship(back_populates="likes")
