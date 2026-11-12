
import enum

from sqlalchemy import (
    Column,
    BigInteger,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
    func,
)

from app.db.session import Base


class TeamMemberRole(str, enum.Enum):
    CAPTAIN = "CAPTAIN"
    MEMBER = "MEMBER"


class TeamMember(Base):
    __tablename__ = "team_members"

    __table_args__ = (
        UniqueConstraint(
            "team_id",
            "user_id",
            name="uq_team_members_team_user",
        ),
        Index(
            "ix_team_members_user_id",
            "user_id",
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

    role = Column(
        SQLEnum(TeamMemberRole),
        nullable=False,
        default=TeamMemberRole.MEMBER,
    )

    joined_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )
