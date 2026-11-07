"""Model: team_posts, team_post_roles, team_post_applications.

Các bảng liên quan (users, games, game_ranks, game_roles) thuộc task khác.
FK đến các bảng đó được khai báo đúng kiểu dữ liệu và tên cột ở đây;
constraint SQL thực sự nằm trong sql/team_posts.sql để chạy trên MySQL Workbench.
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
    """Bài đăng tìm đội / tìm thành viên theo đúng schema GameConnect."""

    __tablename__ = "team_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # FK → users.id  (model users do task khác implement)
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True, comment="ID người đăng bài (FK → users.id)"
    )

    # FK → games.id  (model games do task khác implement)
    game_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="FK → games.id"
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False, comment="Tiêu đề bài đăng")

    # FK → game_ranks.id  (composite: game_id, min_rank_id → game_ranks.game_id, id)
    min_rank_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="Rank tối thiểu chấp nhận (FK → game_ranks.id)"
    )
    # FK → game_ranks.id  (composite: game_id, max_rank_id → game_ranks.game_id, id)
    max_rank_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="Rank tối đa chấp nhận (FK → game_ranks.id)"
    )

    needed_players: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Số người cần tuyển thêm"
    )
    play_time: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Khung giờ chơi (vd: 20:00-23:00)"
    )
    region: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Khu vực / server (vd: VN, SEA)"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status"),
        nullable=False,
        default=PostStatus.OPEN,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Hạn hiển thị bài đăng"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # Schema requires unique (game_id, id) for composite FK from team_post_roles
        UniqueConstraint("game_id", "id", name="uq_team_posts_game_id"),
        Index("ix_team_posts_game_status", "game_id", "status"),
        Index("ix_team_posts_user_id", "user_id"),
    )

    # Relationships (nội bộ task này)
    post_roles: Mapped[list["TeamPostRole"]] = relationship(
        "TeamPostRole",
        primaryjoin="TeamPost.id == foreign(TeamPostRole.team_post_id)",
        cascade="all, delete-orphan",
        overlaps="",
    )
    applications: Mapped[list["TeamPostApplication"]] = relationship(
        "TeamPostApplication", back_populates="post", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# TeamPostRole  –  bảng team_post_roles  (junction: vai trò cần tuyển)
# ---------------------------------------------------------------------------

class TeamPostRole(Base):
    """Vai trò cần tuyển cho một bài đăng (1 bài có thể cần nhiều vai trò).

    Composite FK:
        (game_id, team_post_id) → team_posts(game_id, id)
        (game_id, game_role_id) → game_roles(game_id, id)
    """

    __tablename__ = "team_post_roles"

    team_post_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    game_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="Phải trùng game_id của team_post và game_role"
    )
    game_role_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="FK → game_roles.id"
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
    # FK → users.id  (model users do task khác implement)
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
