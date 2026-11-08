
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

# Change this import if Base is declared in a different module in your project.
from app.db.session import Base


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (
        CheckConstraint("blocker_id <> blocked_id", name="chk_block_different_users"),
        UniqueConstraint("blocker_id", "blocked_id", name="uq_block_pair"),
        Index("idx_blocks_blocked", "blocked_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    blocker_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blocked_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    def __repr__(self) -> str:
        return f"<Block(id={self.id}, blocker_id={self.blocker_id}, blocked_id={self.blocked_id})>"
