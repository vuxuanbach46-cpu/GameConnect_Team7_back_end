"""Model bảng team_posts và team_post_applications.

team_posts          : Bài đăng tìm đội (người đăng, game, rank, vai trò, giờ chơi...)
team_post_applications : Đơn ứng tuyển của người chơi vào một bài đăng
"""
import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
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
    PENDING  = "PENDING"   # chờ duyệt
    ACCEPTED = "ACCEPTED"  # chấp nhận
    REJECTED = "REJECTED"  # từ chối


# ---------------------------------------------------------------------------
# TeamPost
# ---------------------------------------------------------------------------

class TeamPost(Base):
    """Bài đăng tìm đội / tìm thành viên."""

    __tablename__ = "team_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Người đăng (tạm dùng user_id: int; sau khi có bảng users thì đổi thành ForeignKey)
    poster_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="ID người đăng bài")

    # Thông tin game / rank
    game: Mapped[str] = mapped_column(String(100), nullable=False, comment="Tên game (vd: Liên Minh Huyền Thoại)")
    min_rank: Mapped[str | None] = mapped_column(String(50), nullable=True,  comment="Rank tối thiểu chấp nhận")
    max_rank: Mapped[str | None] = mapped_column(String(50), nullable=True,  comment="Rank tối đa chấp nhận")

    # Yêu cầu
    roles_needed: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="Vai trò cần tìm (vd: Jungle, Support)")
    slots_needed: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="Số chỗ trống cần tuyển")

    # Thói quen
    play_time: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="Khung giờ chơi (vd: 20:00-23:00)")
    region: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="Khu vực / server (vd: VN, SEA)")

    # Nội dung
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Mô tả chi tiết bài đăng")

    # Trạng thái & hạn hiển thị
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status"),
        nullable=False,
        default=PostStatus.OPEN,
        comment="Trạng thái bài đăng",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Thời điểm hết hạn hiển thị"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    applications: Mapped[list["TeamPostApplication"]] = relationship(
        "TeamPostApplication", back_populates="post", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# TeamPostApplication
# ---------------------------------------------------------------------------

class TeamPostApplication(Base):
    """Đơn ứng tuyển vào một bài đăng tìm đội."""

    __tablename__ = "team_post_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("team_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    applicant_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="ID người ứng tuyển"
    )

    message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Lời nhắn khi ứng tuyển")

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.PENDING,
        comment="Trạng thái đơn ứng tuyển",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    post: Mapped["TeamPost"] = relationship("TeamPost", back_populates="applications")
