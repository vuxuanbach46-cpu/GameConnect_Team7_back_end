
from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import mapped_column

from app.db.session import Base


class Report(Base):
    __tablename__ = "reports"

    id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reporter_id = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    target_type = mapped_column(
        Enum("USER", "POST", "COMMENT", "TEAM_POST"),
        nullable=False,
    )
    target_id = mapped_column(BigInteger, nullable=False)
    reason = mapped_column(String(150), nullable=False)
    description = mapped_column(Text, nullable=True)
    status = mapped_column(
        Enum("PENDING", "RESOLVED", "REJECTED"),
        nullable=False,
        server_default=text("'PENDING'"),
    )
    handler_id = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    result = mapped_column(Text, nullable=True)
    created_at = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    handled_at = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_reports_status_created", "status", "created_at"),
        Index("idx_reports_target", "target_type", "target_id"),
    )
