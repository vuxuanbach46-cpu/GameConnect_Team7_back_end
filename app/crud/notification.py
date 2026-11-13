from typing import Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    recipient_id: int,
    type: str,
    content: str,
    link: Optional[str] = None,
):
    notification = Notification(
        recipient_id=recipient_id,
        type=type,
        content=content,
        link=link,
        is_read=False,
    )

    db.add(notification)
    db.flush()
    return notification
