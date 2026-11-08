"""SQLAlchemy model for friend requests."""
import enum
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

# Change this import if Base is declared in a different module in your project.
from app.db.session import Base


class FriendRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class FriendRequest(Base):
    __tablename__ = "friend_requests"
    __table_args__ = (
        CheckConstraint("sender_id <> receiver_id", name="chk_friend_request_different_users"),
        Index("idx_friend_requests_receiver", "receiver_id"),
        Index("idx_friend_requests_receiver_status", "receiver_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[FriendRequestStatus] = mapped_column(
        Enum(FriendRequestStatus, name="friend_request_status",
             values_callable=lambda cls: [item.value for item in cls]),
        nullable=False,
        default=FriendRequestStatus.PENDING,
        server_default=FriendRequestStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<FriendRequest(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id}, status={self.status})>"
