
import enum

from sqlalchemy import (
    Column,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
    func,
)

from app.db.session import Base


class TeamJoinRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class TeamJoinRequest(Base):
    __tablename__ = "team_join_requests"

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_team_join_requests_team_user",
        ),
        Index(
            "ix_team_join_requests_team_status",
            "team_id",
            "status",
        ),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    team_id = Column(
        BigInteger,
        ForeignKey(
            "teams.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )

    user_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=True,
    )

    status = Column(
        SQLEnum(TeamJoinRequestStatus),
        nullable=False,
        default=TeamJoinRequestStatus.PENDING,
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
