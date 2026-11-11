import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TeamJoinMode(str, enum.Enum):
    PUBLIC = "PUBLIC"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    main_game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    captain_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    max_members: Mapped[int] = mapped_column(Integer, nullable=False)
    join_mode: Mapped[TeamJoinMode] = mapped_column(
        Enum(TeamJoinMode), nullable=False, default=TeamJoinMode.APPROVAL_REQUIRED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
