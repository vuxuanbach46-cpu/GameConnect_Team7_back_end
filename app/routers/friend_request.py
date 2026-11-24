"""API Router cho chức năng quản lý lời mời kết bạn."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, Response, status
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
    reject_friend_request,
    unfriend,
    get_friends_list,
    get_mutual_friends,
    get_friend_suggestions,
    block_user,
    unblock_user,
    get_blocked_users,
    _get_real_user_card,
)


router = APIRouter(
    prefix="/friend-requests",
    tags=["Friend Requests"]
)


def format_request_list(
    results,
    db: Session | None = None,
    current_user_id: int | None = None,
):
    """Định dạng lời mời kèm thông tin người liên quan (mở rộng đầy đủ thẻ người chơi)."""

    data = []

    for request, user in results:
        card_info = (
            _get_real_user_card(db, user, current_user_id)
            if (db is not None and current_user_id is not None)
            else {}
        )
        data.append({
            "id": request.id,
            "sender_id": request.sender_id,
            "receiver_id": request.receiver_id,
            "status": request.status,
            "created_at": request.created_at,
            "user": {
                "id": user.id,
                "username": user.username,
                **card_info,
            }
        })

    return data


@router.post("", summary="Gửi lời mời kết bạn")
@router.post("/", summary="Gửi lời mời kết bạn", include_in_schema=False)
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

    # Xác định đối tượng liên quan để hiển thị username
    target_id = result.receiver_id if result.sender_id == current_user.id else result.sender_id
    target_user = db.query(User).filter(User.id == target_id).first()
    target_username = target_user.username if target_user else "Người dùng"

    if result.status == "ACCEPTED":
        response_status = status.HTTP_200_OK
        message = f"Hai người đã trở thành bạn bè với {target_username}"
    else:
        response_status = status.HTTP_201_CREATED
        message = f"Đã gửi lời mời đến {target_username}"

    response.status_code = response_status

    response_data = {
        **FriendRequestResponse.model_validate(result).model_dump(),
        "target_username": target_username
    }

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
    target_username = target_user.username if target_user else "Người dùng"

    response_data = {
        **FriendRequestResponse.model_validate(
            result
        ).model_dump(),
        "target_username": target_username
    }

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Đã hủy lời mời gửi đến {target_username}",
        data=response_data
    )


@router.get("/sent", summary="Xem danh sách lời mời đã gửi")
def list_sent_friend_requests(
    req: Request,
    request_status: Optional[str] = Query(
        default="PENDING",
        alias="status",
        description="Trạng thái lọc: PENDING, ACCEPTED, REJECTED, CANCELLED. Bỏ trống để lấy tất cả"
    ),
    skip: int = Query(default=0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(default=20, ge=1, le=100, description="Số bản ghi tối đa trả về"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = get_sent_friend_requests(
        db=db,
        current_user=current_user,
        status=request_status,
        skip=skip,
        limit=limit
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Danh sách lời mời kết bạn đã gửi",
        data=format_request_list(results, db=db, current_user_id=current_user.id)
    )


@router.get("/received", summary="Xem danh sách lời mời đã nhận")
def list_received_friend_requests(
    req: Request,
    request_status: Optional[str] = Query(
        default="PENDING",
        alias="status",
        description="Trạng thái lọc: PENDING, ACCEPTED, REJECTED, CANCELLED. Bỏ trống để lấy tất cả"
    ),
    skip: int = Query(default=0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(default=20, ge=1, le=100, description="Số bản ghi tối đa trả về"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = get_received_friend_requests(
        db=db,
        current_user=current_user,
        status=request_status,
        skip=skip,
        limit=limit
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Danh sách lời mời kết bạn đã nhận",
        data=format_request_list(results, db=db, current_user_id=current_user.id)
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
    sender_username = sender.username if sender else "Người dùng"

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Bạn đã trở thành bạn bè với {sender_username}",
        data={
            **FriendRequestResponse.model_validate(
                result
            ).model_dump(),
            "friend_username": sender_username
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
    sender_username = sender.username if sender else "Người dùng"

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Đã từ chối lời mời từ {sender_username}",
        data={
            **FriendRequestResponse.model_validate(
                result
            ).model_dump(),
            "sender_username": sender_username
        }
    )


@router.get("/friends", summary="Xem danh sách bạn bè hiện tại")
def list_friends(
    req: Request,
    skip: int = Query(default=0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(default=50, ge=1, le=100, description="Số lượng tối đa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách tất cả những người đang là bạn bè với tài khoản hiện tại."""
    friends = get_friends_list(db=db, current_user=current_user, skip=skip, limit=limit)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Danh sách bạn bè",
        data=friends
    )


@router.delete("/friends/{friend_id}", summary="Hủy kết bạn (Unfriend)")
def remove_friend(
    friend_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hủy kết bạn khi hai người đã là bạn bè.
    - Xóa quan hệ bạn bè trong bảng `friendships`.
    - Dọn dẹp trạng thái lời mời cũ để có thể kết bạn lại sau này.
    """
    friend = unfriend(
        db=db,
        current_user=current_user,
        friend_id=friend_id
    )

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Đã hủy kết bạn thành công với {friend.username}",
        data={
            "unfriended_user_id": friend.id,
            "unfriended_username": friend.username
        }
    )


# ===========================================================================
# Bạn chung (Mutual Friends) & Gợi ý kết bạn (Friend Suggestions)
# ===========================================================================

@router.get("/mutual-friends/{target_user_id}", summary="Xem số bạn chung và danh sách bạn chung")
@router.get("/friends/mutual/{target_user_id}", summary="Xem số bạn chung (Alias)", include_in_schema=False)
def list_mutual_friends(
    target_user_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy số lượng và danh sách bạn chung giữa bạn và một người dùng khác:
    - Trả về số lượng `mutual_friends_count`.
    - Danh sách các bạn chung kèm `id`, `username`, `display_name`, `avatar`.
    """
    data = get_mutual_friends(db=db, current_user_id=current_user.id, target_user_id=target_user_id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách bạn chung thành công",
        data=data,
    )


@router.get("/suggestions", summary="Gợi ý kết bạn theo bạn chung và game chung")
@router.get("/friends/suggestions", summary="Gợi ý kết bạn (Alias)", include_in_schema=False)
def list_friend_suggestions(
    req: Request,
    limit: int = Query(default=20, ge=1, le=100, description="Số lượng người gợi ý tối đa"),
    q: Optional[str] = Query(
        default=None,
        description="Từ khóa tìm kiếm username, display_name hoặc in_game_id",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gợi ý kết bạn thông minh hiển thị ở tab GỢI Ý KẾT BẠN trên trang Bạn bè:
    - Thuật toán ưu tiên người có bạn chung và người cùng chơi các tựa game.
    - Hỗ trợ tìm kiếm người chơi toàn hệ thống theo từ khóa `q`.
    - Loại trừ chính mình, những người đã là bạn bè, lời mời đang chờ và người bị chặn.
    - Trả về: bạn chung, mẫu tên bạn chung, các game cùng chơi và lý do gợi ý.
    """
    data = get_friend_suggestions(db=db, current_user_id=current_user.id, limit=limit, q=q)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy danh sách gợi ý kết bạn thành công",
        data=data,
    )


# ===========================================================================
# Chặn & Bỏ chặn bạn bè / người dùng (Block & Unblock)
# ===========================================================================

@router.get("/blocks", summary="Xem danh sách người dùng đã chặn")
def list_blocked_users(
    req: Request,
    skip: int = Query(default=0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(default=50, ge=1, le=100, description="Số lượng tối đa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách tất cả những người dùng mà bạn đang chặn."""
    data = get_blocked_users(db=db, current_user=current_user, skip=skip, limit=limit)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Danh sách người dùng đã chặn",
        data=data,
    )


@router.post(
    "/blocks/{target_user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Chặn bạn bè / người dùng (Block)",
)
@router.post(
    "/block/{target_user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Chặn bạn bè / người dùng (Alias)",
    include_in_schema=False,
)
def create_block_user(
    target_user_id: int,
    req: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chặn một người dùng hoặc bạn bè:
    - Tự động hủy kết bạn nếu hai người đang là bạn bè.
    - Tự động xóa mọi lời mời kết bạn đang chờ giữa hai người.
    - Không thể gửi/nhận lời mời kết bạn hoặc ghép đội chung khi đang chặn.
    """
    result = block_user(db=db, current_user=current_user, target_user_id=target_user_id)
    response.status_code = status.HTTP_201_CREATED
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message=f"Đã chặn {result['blocked_username']} thành công",
        data=result,
    )


@router.delete(
    "/blocks/{target_user_id}",
    summary="Bỏ chặn bạn bè / người dùng (Unblock)",
)
@router.delete(
    "/block/{target_user_id}",
    summary="Bỏ chặn bạn bè / người dùng (Alias)",
    include_in_schema=False,
)
def remove_block_user(
    target_user_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bỏ chặn một người dùng đã bị chặn trước đó."""
    unblocked_user = unblock_user(
        db=db,
        current_user=current_user,
        target_user_id=target_user_id,
    )
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=f"Đã bỏ chặn {unblocked_user.username} thành công",
        data={
            "unblocked_user_id": unblocked_user.id,
            "unblocked_username": unblocked_user.username,
        },
    )


