
from datetime import datetime
from sqlalchemy import (
    BigInteger, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Friendship(Base):
    __tablename__ = "friendships"

    __table_args__ = (
        UniqueConstraint("user_a", "user_b"),
        CheckConstraint("user_a < user_b"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    user_a: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    user_b: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
