"""Model: team_posts, team_post_roles, team_post_applications.

Khớp chuẩn schema GameConnect cho task tìm đội / tuyển thành viên.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PostStatus(str, enum.Enum):
    OPEN   = "OPEN"    # đang tuyển
    FULL   = "FULL"    # đủ người
    CLOSED = "CLOSED"  # người đăng đóng sớm


class ApplicationStatus(str, enum.Enum):
    PENDING   = "PENDING"    # chờ duyệt
    ACCEPTED  = "ACCEPTED"   # chấp nhận
    REJECTED  = "REJECTED"   # từ chối
    CANCELLED = "CANCELLED"  # người ứng tuyển tự rút


# ---------------------------------------------------------------------------
# TeamPost  –  bảng team_posts
# ---------------------------------------------------------------------------

class TeamPost(Base):
    """Bài đăng tìm đội / tìm thành viên."""

    __tablename__ = "team_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # FK → users.id (BigInteger)
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True, comment="ID người đăng bài (FK → users.id)"
    )

    # FK → games.id (Integer)
    game_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="FK → games.id"
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False, comment="Tiêu đề bài đăng")

    # FK → game_ranks.id (Integer)
    min_rank_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Rank tối thiểu chấp nhận (FK → game_ranks.id)"
    )
    max_rank_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Rank tối đa chấp nhận (FK → game_ranks.id)"
    )

    needed_players: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Số người cần tuyển thêm (1-9)"
    )
    play_time: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Khung giờ chơi (vd: 20:00-23:00)"
    )
    region: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Khu vực / server (vd: VN, SEA)"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Mô tả chi tiết")

    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status"),
        nullable=False,
        default=PostStatus.OPEN,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Hạn hiển thị bài đăng (tối đa 7 ngày)"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_team_posts_game_status", "game_id", "status"),
        Index("ix_team_posts_user_id", "user_id"),
    )

    # Relationships nội bộ module
    post_roles: Mapped[list["TeamPostRole"]] = relationship(
        "TeamPostRole",
        primaryjoin="TeamPost.id == foreign(TeamPostRole.team_post_id)",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    applications: Mapped[list["TeamPostApplication"]] = relationship(
        "TeamPostApplication", back_populates="post", cascade="all, delete-orphan"
    )

    @property
    def role_ids(self) -> list[int]:
        return [r.game_role_id for r in self.post_roles] if self.post_roles else []


# ---------------------------------------------------------------------------
# TeamPostRole  –  bảng team_post_roles  (vai trò cần tuyển)
# ---------------------------------------------------------------------------

class TeamPostRole(Base):
    """Vai trò cần tuyển cho một bài đăng (1 bài có thể cần nhiều vai trò)."""

    __tablename__ = "team_post_roles"

    team_post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("team_posts.id", ondelete="CASCADE"), nullable=False
    )
    game_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="FK → games.id"
    )
    game_role_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="FK → game_roles.id"
    )

    __table_args__ = (
        PrimaryKeyConstraint("team_post_id", "game_role_id", name="pk_team_post_roles"),
    )


# ---------------------------------------------------------------------------
# TeamPostApplication  –  bảng team_post_applications
# ---------------------------------------------------------------------------

class TeamPostApplication(Base):
    """Đơn ứng tuyển của người chơi vào một bài đăng tìm đội."""

    __tablename__ = "team_post_applications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    team_post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("team_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True, comment="ID người ứng tuyển (FK → users.id)"
    )

    message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Lời nhắn khi ứng tuyển")

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("team_post_id", "user_id", name="uq_team_post_apps_post_user"),
        Index("ix_team_post_apps_user_status", "user_id", "status"),
    )

    post: Mapped["TeamPost"] = relationship("TeamPost", back_populates="applications")
