
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class GameRole(Base):
    __tablename__ = "game_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    game_id = Column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False
    )

    role_name = Column(String(100), nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "role_name",
            name="unique_game_role"
        ),
    )

    game = relationship("Game", back_populates="roles")

    user_games = relationship(
        "UserGame",
        back_populates="role"
    )
