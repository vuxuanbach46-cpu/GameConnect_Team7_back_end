
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)

    name = Column(String(150), nullable=False, unique=True)
    image = Column(String(500), nullable=True)
    genre = Column(String(100), nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    ranks = relationship(
        "GameRank",
        back_populates="game",
        cascade="all, delete-orphan"
    )

    roles = relationship(
        "GameRole",
        back_populates="game",
        cascade="all, delete-orphan"
    )

    user_games = relationship(
        "UserGame",
        back_populates="game"
    )
