from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.session import Base


class PostGame(Base):
    __tablename__ = "post_games"

    post_id = Column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    post = relationship("Post", back_populates="post_games")
