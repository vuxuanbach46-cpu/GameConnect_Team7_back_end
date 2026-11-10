
"""Nghiệp vụ gửi, hủy, xem và xử lý lời mời kết bạn."""

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.friend_request import FriendRequest
from app.models.friendships import Friendship
from app.models.block import Block


def check_block(db: Session, user_a: int, user_b: int):
    """Kiểm tra một trong hai người có chặn người còn lại không."""
    return db.query(Block).filter(or_(
        and_(
            Block.blocker_id == user_a,
            Block.blocked_id == user_b
        ),
        and_(
            Block.blocker_id == user_b,
            Block.blocked_id == user_a
        )
    )).first()


def send_friend_request(db: Session, sender: User, receiver_id: int):
    """Gửi lời mời kết bạn."""

    sender_id = sender.id

    if sender_id == receiver_id:
        raise HTTPException(
            status_code=400,
            detail="Không thể gửi lời mời cho chính mình"
        )

    receiver = db.query(User).filter(
        User.id == receiver_id
    ).first()

    if receiver is None:
        raise HTTPException(
            status_code=404,
            detail="Người nhận không tồn tại"
        )

    if receiver.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Tài khoản người nhận không hoạt động"
        )

    user_a, user_b = sorted((sender_id, receiver_id))

    friendship = db.query(Friendship).filter(
        Friendship.user_a == user_a,
        Friendship.user_b == user_b
    ).first()

    if friendship:
        raise HTTPException(
            status_code=409,
            detail="Hai người đã là bạn bè"
        )

    if check_block(db, sender_id, receiver_id):
        raise HTTPException(
            status_code=403,
            detail="Một trong hai người đã chặn người còn lại"
        )

    # Nếu người nhận đã gửi lời mời cho người gửi,
    # tự động chấp nhận và tạo quan hệ bạn bè.
    reverse_request = db.query(FriendRequest).filter(
        FriendRequest.sender_id == receiver_id,
        FriendRequest.receiver_id == sender_id,
        FriendRequest.status == "PENDING"
    ).first()

    if reverse_request:
        try:
            reverse_request.status = "ACCEPTED"

            db.add(Friendship(
                user_a=user_a,
                user_b=user_b
            ))

            db.commit()
            db.refresh(reverse_request)

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Quan hệ bạn bè đã tồn tại"
            )

        return {
            "message": "Hai người đã trở thành bạn bè",
            "status": "ACCEPTED",
            "friend_request_id": reverse_request.id
        }

    # Không cho gửi trùng lời mời đang chờ.
    existing_request = db.query(FriendRequest).filter(
        FriendRequest.sender_id == sender_id,
        FriendRequest.receiver_id == receiver_id,
        FriendRequest.status == "PENDING"
    ).first()

    if existing_request:
        raise HTTPException(
            status_code=409,
            detail="Bạn đã gửi lời mời kết bạn đang chờ"
        )

    # Tạm thời chưa kiểm tra allow_friend_requests
    # vì model User hiện tại chưa có trường này.

    request = FriendRequest(
        sender_id=sender_id,
        receiver_id=receiver_id,
        status="PENDING"
    )

    try:
        db.add(request)
        db.commit()
        db.refresh(request)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Không thể tạo lời mời kết bạn"
        )

    return request


def cancel_friend_request(db: Session, sender: User, request_id: int):
    """Người gửi mới được hủy lời mời đang chờ."""

    request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id
    ).first()

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lời mời kết bạn"
        )

    if request.sender_id != sender.id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền hủy lời mời này"
        )

    if request.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Chỉ có thể hủy lời mời đang chờ"
        )

    request.status = "CANCELLED"

    db.commit()
    db.refresh(request)

    return request


def get_sent_friend_requests(db: Session, current_user: User):
    """Danh sách lời mời do người đăng nhập gửi."""

    results = db.query(
        FriendRequest, User
    ).join(
        User, User.id == FriendRequest.receiver_id
    ).filter(
        FriendRequest.sender_id == current_user.id
    ).order_by(
        FriendRequest.created_at.desc()
    ).all()

    return results


def get_received_friend_requests(db: Session, current_user: User):
    """Danh sách lời mời người khác gửi cho người đăng nhập."""

    results = db.query(
        FriendRequest, User
    ).join(
        User, User.id == FriendRequest.sender_id
    ).filter(
        FriendRequest.receiver_id == current_user.id
    ).order_by(
        FriendRequest.created_at.desc()
    ).all()

    return results


def accept_friend_request(
    db: Session,
    current_user: User,
    request_id: int
):
    """Người nhận chấp nhận lời mời kết bạn."""

    request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id
    ).first()

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lời mời kết bạn"
        )

    # Chỉ người nhận mới được chấp nhận.
    if request.receiver_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền chấp nhận lời mời này"
        )

    if request.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Lời mời không còn ở trạng thái chờ"
        )

    user_a, user_b = sorted((
        request.sender_id,
        request.receiver_id
    ))

    if check_block(db, user_a, user_b):
        raise HTTPException(
            status_code=403,
            detail="Không thể kết bạn vì một trong hai người đã chặn nhau"
        )

    friendship = db.query(Friendship).filter(
        Friendship.user_a == user_a,
        Friendship.user_b == user_b
    ).first()

    if friendship:
        raise HTTPException(
            status_code=409,
            detail="Hai người đã là bạn bè"
        )

    try:
        request.status = "ACCEPTED"

        db.add(Friendship(
            user_a=user_a,
            user_b=user_b
        ))

        db.commit()
        db.refresh(request)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Không thể tạo quan hệ bạn bè"
        )

    return request


def reject_friend_request(
    db: Session,
    current_user: User,
    request_id: int
):
    """Người nhận từ chối lời mời kết bạn."""

    request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id
    ).first()

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lời mời kết bạn"
        )

    # Chỉ người nhận mới được từ chối.
    if request.receiver_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền từ chối lời mời này"
        )

    if request.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Chỉ có thể từ chối lời mời đang chờ"
        )

    request.status = "REJECTED"

    db.commit()
    db.refresh(request)

    return request
