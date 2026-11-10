
from datetime import datetime
from sqlalchemy import (
    BigInteger, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Block(Base):
    __tablename__ = "blocks"

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id"),
        CheckConstraint("blocker_id <> blocked_id"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    blocker_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    blocked_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
