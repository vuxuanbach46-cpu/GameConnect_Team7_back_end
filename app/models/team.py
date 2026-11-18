import enum

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    func,
)

from app.db.session import Base


class TeamJoinMode(str, enum.Enum):
    PUBLIC = "PUBLIC"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class Team(Base):
    __tablename__ = "teams"

    __table_args__ = (
        Index("ix_teams_main_game_id", "main_game_id"),
        Index("ix_teams_captain_id", "captain_id"),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
        autoincrement=True,
    )
    name = Column(
        String(100),
        unique=True,
        nullable=False,
    )
    logo_url = Column(
        String(500),
        nullable=True,
    )
    main_game_id = Column(
        Integer,
        ForeignKey(
            "games.id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    description = Column(
        Text,
        nullable=True,
    )
    captain_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
    )
    max_members = Column(
        Integer,
        nullable=False,
        default=5,
    )
    join_mode = Column(
        SQLEnum(TeamJoinMode),
        nullable=False,
        default=TeamJoinMode.PUBLIC,
    )
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
