
from datetime import datetime
from sqlalchemy import (
    BigInteger, DateTime, Enum,
    ForeignKey, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    __table_args__ = (
        CheckConstraint("sender_id <> receiver_id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    sender_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    receiver_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum("PENDING", "ACCEPTED", "REJECTED", "CANCELLED"),
        default="PENDING",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )
