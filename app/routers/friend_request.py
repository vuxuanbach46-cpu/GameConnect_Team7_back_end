
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db

from app.models.user import User

from app.schemas.friend_request import (
    FriendRequestCreate,
    FriendRequestResponse
)

from app.schemas.api_response import api_repoint

from app.crud.friend_request import (
    send_friend_request,
    cancel_friend_request,
    get_sent_friend_requests,
    get_received_friend_requests,
    accept_friend_request,
    reject_friend_request
)


router = APIRouter(
    prefix="/friend-requests",
    tags=["Friend Requests"]
)


def format_request_list(results):
    """Định dạng lời mời kèm thông tin người liên quan."""

    data = []

    for request, user in results:
        data.append({
            "id": request.id,
            "sender_id": request.sender_id,
            "receiver_id": request.receiver_id,
            "status": request.status,
            "created_at": request.created_at,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })

    return data


@router.post("/", summary="Gửi lời mời kết bạn")
def create_friend_request(
    req: Request,
    response: Response,
    data: FriendRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = send_friend_request(
        db=db,
        sender=current_user,
        receiver_id=data.receiver_id
    )

    if isinstance(result, dict):
        response_data = result
        message = result["message"]
        response_status = status.HTTP_200_OK

    else:
        target_user = db.query(User).filter(
            User.id == result.receiver_id
        ).first()

        response_data = {
            **FriendRequestResponse.model_validate(
                result
            ).model_dump(),
            "target_username": target_user.username
        }

        message = f"Đã gửi lời mời đến {target_user.username}"
        response_status = status.HTTP_201_CREATED

    response.status_code = response_status

    return api_repoint(
        req=req,
        status_code=response_status,
        message=message,
        data=response_data
    )


@router.delete("/{request_id}", summary="Hủy lời mời kết bạn")
def delete_friend_request(
    request_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = cancel_friend_request(
        db=db,
        sender=current_user,
        request_id=request_id
    )

    target_user = db.query(User).filter(
        User.id == result.receiver_id
    ).first()

    response_data = {
        **FriendRequestResponse.model_validate(
            result
        ).model_dump(),
        "target_username": target_user.username
    }

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Đã hủy lời mời gửi đến {target_user.username}",
        data=response_data
    )


@router.get("/sent", summary="Xem danh sách lời mời đã gửi")
def list_sent_friend_requests(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = get_sent_friend_requests(
        db=db,
        current_user=current_user
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Danh sách lời mời kết bạn đã gửi",
        data=format_request_list(results)
    )


@router.get("/received", summary="Xem danh sách lời mời đã nhận")
def list_received_friend_requests(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = get_received_friend_requests(
        db=db,
        current_user=current_user
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Danh sách lời mời kết bạn đã nhận",
        data=format_request_list(results)
    )


@router.post("/{request_id}/accept", summary="Chấp nhận lời mời kết bạn")
def accept_request(
    request_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = accept_friend_request(
        db=db,
        current_user=current_user,
        request_id=request_id
    )

    sender = db.query(User).filter(
        User.id == result.sender_id
    ).first()

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Bạn đã trở thành bạn bè với {sender.username}",
        data={
            **FriendRequestResponse.model_validate(
                result
            ).model_dump(),
            "friend_username": sender.username
        }
    )


@router.post("/{request_id}/reject", summary="Từ chối lời mời kết bạn")
def reject_request(
    request_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = reject_friend_request(
        db=db,
        current_user=current_user,
        request_id=request_id
    )

    sender = db.query(User).filter(
        User.id == result.sender_id
    ).first()

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Đã từ chối lời mời từ {sender.username}",
        data={
            **FriendRequestResponse.model_validate(
                result
            ).model_dump(),
            "sender_username": sender.username
        }
    )
