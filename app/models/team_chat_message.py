from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

TEAM_CHAT_ID_TYPE = BigInteger().with_variant(BIGINT(unsigned=True), "mysql").with_variant(Integer, "sqlite")


class TeamChatMessage(Base):
    """Persistent message in a private team/club room."""

    __tablename__ = "team_chat_messages"
    __table_args__ = (
        Index("ix_team_chat_team_id_id", "team_id", "id"),
    )

    id: Mapped[int] = mapped_column(TEAM_CHAT_ID_TYPE, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
