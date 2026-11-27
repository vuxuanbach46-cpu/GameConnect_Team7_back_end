
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RoomStatus(str, enum.Enum):
    WAITING   = "WAITING"    # Đang chờ người (chưa đủ)
    FULL      = "FULL"       # Đã đủ người -> Mở khóa hiện Code Game
    CANCELLED = "CANCELLED"  # Chủ phòng hủy


class QueueStatus(str, enum.Enum):
    SEARCHING = "SEARCHING"  # Đang trong hàng chờ tìm phòng
    MATCHED   = "MATCHED"    # Đã ghép vào phòng thành công
    CANCELLED = "CANCELLED"  # Người chơi tự hủy tìm trận


# ---------------------------------------------------------------------------
# MatchRoom – Bảng match_rooms
# ---------------------------------------------------------------------------

class MatchRoom(Base):
    """Phòng ghép đội (Chứa Code Game)."""

    __tablename__ = "match_rooms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    host_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="ID chủ phòng"
    )
    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, comment="ID Game"
    )
    room_name: Mapped[str] = mapped_column(
        String(150), nullable=False, comment="Tên phòng / Mục tiêu chơi"
    )
    game_code: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Mã phòng game thật để vào chơi (Code Game)"
    )
    max_players: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, comment="Số người tối đa để đủ đội"
    )
    current_players: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Số người hiện tại"
    )

    min_rank_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("game_ranks.id", ondelete="SET NULL"), nullable=True
    )
    max_rank_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("game_ranks.id", ondelete="SET NULL"), nullable=True
    )
    label: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Nhãn yêu cầu: Tryhard, Vui vẻ, Có Mic..."
    )

    status: Mapped[RoomStatus] = mapped_column(
        Enum(RoomStatus, name="room_status"),
        nullable=False,
        default=RoomStatus.WAITING,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_match_rooms_game_status", "game_id", "status"),
        Index("ix_match_rooms_host", "host_id"),
    )

    # Relationships
    members: Mapped[list["MatchRoomMember"]] = relationship(
        "MatchRoomMember", back_populates="room", cascade="all, delete-orphan"
    )
    host = relationship("User", foreign_keys=[host_id])
    game = relationship("Game", foreign_keys=[game_id])
    min_rank = relationship("GameRank", foreign_keys=[min_rank_id])
    max_rank = relationship("GameRank", foreign_keys=[max_rank_id])


# ---------------------------------------------------------------------------
# MatchRoomMember – Bảng match_room_members
# ---------------------------------------------------------------------------

class MatchRoomMember(Base):
    """Thành viên trong phòng ghép đội."""

    __tablename__ = "match_room_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    room_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("match_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("game_roles.id", ondelete="SET NULL"), nullable=True
    )
    is_host: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Có phải chủ phòng không"
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_match_room_member"),
    )

    # Relationships
    room: Mapped["MatchRoom"] = relationship("MatchRoom", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("GameRole", foreign_keys=[role_id])


# ---------------------------------------------------------------------------
# MatchQueue – Bảng match_queue
# ---------------------------------------------------------------------------

class MatchQueue(Base):
    """Hàng chờ Auto Match."""

    __tablename__ = "match_queue"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("game_roles.id", ondelete="SET NULL"), nullable=True
    )
    rank_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("game_ranks.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus, name="queue_status"),
        nullable=False,
        default=QueueStatus.SEARCHING,
    )
    matched_room_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("match_rooms.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_mq_game_status", "game_id", "status"),
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    game = relationship("Game", foreign_keys=[game_id])
    role = relationship("GameRole", foreign_keys=[role_id])
    rank = relationship("GameRank", foreign_keys=[rank_id])
    matched_room = relationship("MatchRoom", foreign_keys=[matched_room_id])
