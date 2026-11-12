from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.api_response import api_repoint

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def notification_data(notification: Notification):
    return {
        "id": notification.id,
        "recipient_id": notification.recipient_id,
        "type": notification.type,
        "content": notification.content,
        "link": notification.link,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
    }


@router.get("", summary="Danh sách thông báo")
def get_notifications(
    req: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách thông báo thành công",
        data=[notification_data(item) for item in notifications],
    )


@router.get("/unread-count", summary="Số thông báo chưa đọc")
def get_unread_count(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(
            Notification.recipient_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .count()
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy số thông báo chưa đọc thành công",
        data={"unread_count": count},
    )


@router.patch("/read-all", summary="Đánh dấu tất cả thông báo đã đọc")
def read_all_notifications(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_count = (
        db.query(Notification)
        .filter(
            Notification.recipient_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Đã đánh dấu tất cả thông báo là đã đọc",
        data={"updated_count": updated_count},
    )


@router.patch("/{notification_id}/read", summary="Đánh dấu một thông báo đã đọc")
def read_notification(
    notification_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông báo",
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Đánh dấu thông báo đã đọc thành công",
        data=notification_data(notification),
    )
