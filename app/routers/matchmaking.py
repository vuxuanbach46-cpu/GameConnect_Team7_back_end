"""Router API cho Auto Matchmaking (Web GameConnect).

Chuẩn hóa dữ liệu trả về theo format 6 trường của toàn hệ thống (APIRepoint):
1. status_code (mã HTTP)
2. message (thông điệp)
3. data (dữ liệu chính)
4. error (lỗi nếu có)
5. timestamp (thời gian)
6. path (đường dẫn gọi API)
"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.crud import matchmaking as matchmaking_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.api_response import APIRepoint, api_repoint
from app.schemas.matchmaking import (
    CreateLobbyRequest,
    CreateMatchRoomRequest,
    FindMatchRequest,
    QuickMatchRequest,
)

router = APIRouter(prefix="/matchmaking", tags=["Auto Match"])


# ===========================================================================
# 1. Sảnh đội (Lobby) & Mời bạn bè
# ===========================================================================

@router.post(
    "/lobby",
    response_model=APIRepoint,
    status_code=status.HTTP_201_CREATED,
    summary="Khởi tạo sảnh đội (Lobby)",
)
def create_lobby(
    req: Request,
    data: CreateLobbyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tạo sảnh đội để chuẩn bị mời bạn bè hoặc bấm tìm trận. Trả về đủ 6 trường chuẩn."""
    result = matchmaking_crud.create_or_get_lobby(db, user_id=current_user.id, data=data)
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Khởi tạo sảnh đội thành công",
        data=result.model_dump(),
    )


@router.post(
    "/invite/{friend_id}",
    response_model=APIRepoint,
    summary="Mời bạn bè vào sảnh đội (+ Mời vào đội)",
)
def invite_friend(
    friend_id: int,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bấm nút '+ Mời vào đội' cạnh tên bạn bè (gửi thông báo kèm room_id vào Notifications)."""
    result = matchmaking_crud.invite_friend_to_lobby(db, user_id=current_user.id, friend_id=friend_id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result.message,
        data=result.model_dump(),
    )


@router.post(
    "/accept-invite/{room_id}",
    response_model=APIRepoint,
    summary="Chấp nhận lời mời tham gia sảnh đội (Từ Notifications)",
)
def accept_invite(
    room_id: int,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bạn bè bấm 'Đồng ý tham gia' bằng room_id hoặc notification_id."""
    result = matchmaking_crud.accept_lobby_invite(db, user_id=current_user.id, room_id=room_id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Tham gia sảnh đội thành công",
        data=result.model_dump(),
    )


@router.post(
    "/accept-notification/{notification_id}",
    response_model=APIRepoint,
    summary="Đồng ý tham gia đội trực tiếp bằng ID thông báo",
)
def accept_invite_by_notification(
    notification_id: int,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bấm nút 'Đồng ý tham gia' trực tiếp từ thẻ thông báo (dùng ID của thông báo)."""
    result = matchmaking_crud.accept_lobby_invite(db, user_id=current_user.id, room_id=notification_id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Tham gia sảnh đội thành công",
        data=result.model_dump(),
    )


# ===========================================================================
# 2. Tìm trận tự động (Nút cam FIND MATCH)
# ===========================================================================

@router.post(
    "/find-match",
    response_model=APIRepoint,
    summary="Tìm trận tự động (Nút cam FIND MATCH)",
)
def find_match(
    data: FindMatchRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Nút cam FIND MATCH (Tự động gom nhóm và người lẻ). Trả về đủ 6 trường chuẩn."""
    result = matchmaking_crud.find_match(db, user_id=current_user.id, data=data)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result.message,
        data=result.model_dump(),
    )


@router.post(
    "/cancel-search",
    response_model=APIRepoint,
    summary="Hủy tìm trận khi đang trong hàng chờ",
)
def cancel_search(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trưởng nhóm hủy tìm trận."""
    result = matchmaking_crud.cancel_search(db, user_id=current_user.id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result["message"],
        data=result,
    )


# ===========================================================================
# 3. Quản lý Đội / Phòng hiện tại (Xem & Rời)
# ===========================================================================

@router.get(
    "/my-team",
    response_model=APIRepoint,
    summary="Xem sảnh đội hiện tại của tôi",
)
def get_my_team(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Xem đội/sảnh hiện tại của bạn kèm danh sách thành viên và Code Game."""
    result = matchmaking_crud.get_my_current_room(db, user_id=current_user.id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result.message,
        data=result.room.model_dump() if result.room else None,
    )


@router.post(
    "/leave-team",
    response_model=APIRepoint,
    summary="Rời khỏi sảnh đội hiện tại",
)
def leave_team(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rời khỏi đội."""
    result = matchmaking_crud.leave_current_room(db, user_id=current_user.id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result["message"],
        data=result,
    )


# ===========================================================================
# 4. Tương thích ngược (Backward Compatibility)
# ===========================================================================

@router.post(
    "/rooms",
    response_model=APIRepoint,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo sảnh đội (Tương thích ngược)",
    include_in_schema=False,
)
def create_room_legacy(
    req: Request,
    data: CreateMatchRoomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = matchmaking_crud.create_room(db, user_id=current_user.id, data=data)
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Khởi tạo sảnh đội thành công",
        data=result.model_dump(),
    )


@router.post(
    "/quick-match",
    response_model=APIRepoint,
    summary="Vào đội nhanh (Tương thích ngược)",
    include_in_schema=False,
)
def quick_match_legacy(
    req: Request,
    data: QuickMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = matchmaking_crud.quick_match(db, user_id=current_user.id, data=data)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result.message,
        data=result.model_dump(),
    )


@router.get(
    "/my-room",
    response_model=APIRepoint,
    summary="Xem phòng hiện tại (Tương thích ngược)",
    include_in_schema=False,
)
def get_my_room_legacy(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = matchmaking_crud.get_my_current_room(db, user_id=current_user.id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result.message,
        data=result.room.model_dump() if result.room else None,
    )


@router.post(
    "/leave-room",
    response_model=APIRepoint,
    summary="Rời phòng (Tương thích ngược)",
    include_in_schema=False,
)
def leave_room_legacy(
    req: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = matchmaking_crud.leave_current_room(db, user_id=current_user.id)
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message=result["message"],
        data=result,
    )
