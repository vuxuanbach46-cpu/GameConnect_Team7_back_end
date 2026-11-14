
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    BigInteger
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserGame(Base):
    __tablename__ = "user_games"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False
    )

    rank_id = Column(
        Integer,
        ForeignKey("game_ranks.id", ondelete="SET NULL"),
        nullable=True
    )

    role_id = Column(
        Integer,
        ForeignKey("game_roles.id", ondelete="SET NULL"),
        nullable=True
    )

    in_game_id = Column(String(150), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "game_id",
            name="unique_user_game"
        ),
        Index("idx_user_games_user", "user_id"),
        Index("idx_user_games_game", "game_id"),
    )

    user = relationship("User")

    game = relationship(
        "Game",
        back_populates="user_games"
    )

    rank = relationship(
        "GameRank",
        back_populates="user_games"
    )

    role = relationship(
        "GameRole",
        back_populates="user_games"
    )
