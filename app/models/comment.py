from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, Text, func

from app.db.session import Base


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_post_created", "post_id", "created_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_comment_id = Column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
