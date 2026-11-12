"""Router API cho Auto Matchmaking (Web GameConnect).

Toàn bộ API đều tự động nhận diện tài khoản đã đăng nhập qua Token (JWT).
Người dùng không cần nhập user_id hay bất kỳ ID nào!

Endpoints:
    POST /api/matchmaking/rooms        - Tạo phòng mới với Code Game
    POST /api/matchmaking/quick-match  - Vào đội nhanh (ghép vào phòng đang mở)
    GET  /api/matchmaking/my-room      - Xem phòng hiện tại của tôi (kèm danh sách người chơi)
    POST /api/matchmaking/leave-room   - Rời khỏi phòng hiện tại
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.crud import matchmaking as matchmaking_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.matchmaking import (
    CreateMatchRoomRequest,
    MatchRoomOut,
    MyRoomResponse,
    QuickMatchRequest,
    QuickMatchResponse,
)

router = APIRouter(prefix="/matchmaking", tags=["Auto Match"])


@router.post(
    "/rooms",
    response_model=MatchRoomOut,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phòng chơi mới với Code Game",
)
def create_room(
    data: CreateMatchRoomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Người dùng tạo phòng mới:
    - Tự động lấy tài khoản của bạn qua Token đăng nhập.
    - Nhập: `game_id`, `room_name`, `game_code`, `max_players`.
    """
    return matchmaking_crud.create_room(db, user_id=current_user.id, data=data)


@router.post(
    "/quick-match",
    response_model=QuickMatchResponse,
    summary="Vào đội nhanh (Tìm phòng đang mở)",
)
def quick_match(
    data: QuickMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Người chơi bấm tìm đội nhanh:
    - Tự động lấy tài khoản của bạn qua Token đăng nhập.
    - Nhập `game_id` muốn chơi $\rightarrow$ Hệ thống tự động ghép bạn vào phòng đang còn chỗ.
    """
    return matchmaking_crud.quick_match(db, user_id=current_user.id, data=data)


@router.get(
    "/my-room",
    response_model=MyRoomResponse,
    summary="Xem phòng hiện tại của tôi",
)
def get_my_room(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Xem phòng của tài khoản đang đăng nhập:
    - Không cần nhập bất kỳ tham số nào!
    - Nếu chưa tham gia phòng nào: Báo 'Bạn chưa tham gia phòng nào'.
    - Nếu đã tham gia: Hiển thị đầy đủ thông tin phòng, Code Game và danh sách các bạn đang ở trong phòng.
    """
    return matchmaking_crud.get_my_current_room(db, user_id=current_user.id)


@router.post(
    "/leave-room",
    summary="Rời khỏi phòng hiện tại",
)
def leave_room(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rời khỏi phòng bạn đang tham gia:
    - Không cần nhập ID nào cả! Hệ thống tự nhận diện phòng của bạn và cho rời đi.
    """
    return matchmaking_crud.leave_current_room(db, user_id=current_user.id)
