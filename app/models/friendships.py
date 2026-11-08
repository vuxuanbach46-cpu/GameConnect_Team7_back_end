"""SQLAlchemy model for established friendships."""
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

# Change this import if Base is declared in a different module in your project.
from app.db.session import Base


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (
        CheckConstraint("user_a < user_b", name="chk_friendship_user_order"),
        UniqueConstraint("user_a", "user_b", name="uq_friendship_pair"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # Always store the smaller user ID in user_a and the larger one in user_b.
    user_a: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_b: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    def __repr__(self) -> str:
        return f"<Friendship(id={self.id}, user_a={self.user_a}, user_b={self.user_b})>"
