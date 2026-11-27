
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class GameRank(Base):
    __tablename__ = "game_ranks"

    id = Column(Integer, primary_key=True, autoincrement=True)

    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False
    )

    rank_name = Column(String(100), nullable=False)
    rank_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "rank_name",
            name="unique_game_rank"
        ),
    )

    game = relationship("Game", back_populates="ranks")

    user_games = relationship(
        "UserGame",
        back_populates="rank",
        passive_deletes=True,
    )
