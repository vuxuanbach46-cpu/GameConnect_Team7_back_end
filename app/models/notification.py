
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import mapped_column

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    recipient_id = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    type = mapped_column(String(50), nullable=False)
    content = mapped_column(String(500), nullable=False)
    link = mapped_column(String(500), nullable=True)
    is_read = mapped_column(Boolean, nullable=False, server_default=text("0"))
    created_at = mapped_column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        Index(
            "idx_notifications_recipient_read_created",
            "recipient_id",
            "is_read",
            "created_at",
        ),
    )
