import enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    image_urls = Column(JSON, nullable=True)
    status = Column(String(10), nullable=False, default=PostStatus.VISIBLE.value)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    post_games = relationship(
        "PostGame", back_populates="post", cascade="all, delete-orphan"
    )
