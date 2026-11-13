"""Router API cho Auto Matchmaking (Web GameConnect).

Hỗ trợ chuẩn mô hình Gaming Hub / FACEIT:
1. POST /api/matchmaking/lobby               - Khởi tạo sảnh đội (Lobby)
2. POST /api/matchmaking/invite/{friend_id}  - Mời bạn bè (+ Mời vào đội qua Notifications)
3. POST /api/matchmaking/accept-invite/{id}  - Bạn bè bấm Đồng ý tham gia -> Vào sảnh
4. POST /api/matchmaking/find-match          - Nút cam FIND MATCH (Tự động ghép 3+2=5, 4+1=5...)
5. POST /api/matchmaking/cancel-search       - Hủy tìm trận
6. GET  /api/matchmaking/my-team             - Xem trạng thái sảnh/đội hiện tại
7. POST /api/matchmaking/leave-team          - Rời khỏi đội
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.crud import matchmaking as matchmaking_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.matchmaking import (
    CreateLobbyRequest,
    CreateMatchRoomRequest,
    FindMatchRequest,
    InviteFriendResponse,
    MatchRoomOut,
    MyRoomResponse,
    QuickMatchRequest,
    QuickMatchResponse,
)

router = APIRouter(prefix="/matchmaking", tags=["Auto Match"])


# ===========================================================================
# 1. Sảnh đội (Lobby) & Mời bạn bè
# ===========================================================================

@router.post(
    "/lobby",
    response_model=MatchRoomOut,
    status_code=status.HTTP_201_CREATED,
    summary="Khởi tạo sảnh đội (Lobby)",
)
def create_lobby(
    data: CreateLobbyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tạo sảnh đội để chuẩn bị mời bạn bè hoặc bấm tìm trận:
    - Không cần nhập Code Game hay tên phòng rườm rà.
    - Nhập: `game_id`, `max_players` (mặc định 5), min/max rank, label phong cách chơi.
    """
    return matchmaking_crud.create_or_get_lobby(db, user_id=current_user.id, data=data)


@router.post(
    "/invite/{friend_id}",
    response_model=InviteFriendResponse,
    summary="Mời bạn bè vào sảnh đội (+ Mời vào đội)",
)
def invite_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bấm nút '+ Mời vào đội' cạnh tên bạn bè:
    - Tự động gửi thông báo (Notification) `type: 'PARTY_INVITE'` vào chuông thông báo của bạn bè.
    - Bên bạn bè mở chuông thông báo sẽ thấy nút 'Đồng ý tham gia'.
    """
    return matchmaking_crud.invite_friend_to_lobby(db, user_id=current_user.id, friend_id=friend_id)


@router.post(
    "/accept-invite/{room_id}",
    response_model=MatchRoomOut,
    summary="Chấp nhận lời mời tham gia sảnh đội (Từ Notifications)",
)
def accept_invite(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bạn bè bấm 'Đồng ý tham gia':
    - Tự động nhập bạn bè vào sảnh đội của người mời (`match_room_members`).
    - Đánh dấu thông báo mời là đã đọc (`is_read = True`).
    """
    return matchmaking_crud.accept_lobby_invite(db, user_id=current_user.id, room_id=room_id)


# ===========================================================================
# 2. Tìm trận tự động (Nút cam FIND MATCH)
# ===========================================================================

@router.post(
    "/find-match",
    response_model=QuickMatchResponse,
    summary="Tìm trận tự động (Nút cam FIND MATCH)",
)
def find_match(
    data: FindMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Nút cam FIND MATCH (Hoàn toàn tự động):
    - Dù đi 1 mình (solo) hay đi nhóm 2, 3, 4 người: Hệ thống tự quét tìm các nhóm/người còn thiếu ghép lại cho đủ 5.
    - Khi đủ 5 người: Tự động đổi trạng thái sang FULL, mở Code Game và bắn thông báo `MATCH_FOUND` cho toàn đội!
    """
    return matchmaking_crud.find_match(db, user_id=current_user.id, data=data)


@router.post(
    "/cancel-search",
    summary="Hủy tìm trận khi đang trong hàng chờ",
)
def cancel_search(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trưởng nhóm hủy tìm trận:
    - Dừng quá trình quét ghép phòng. Sảnh đội vẫn được giữ nguyên.
    """
    return matchmaking_crud.cancel_search(db, user_id=current_user.id)


# ===========================================================================
# 3. Quản lý Đội / Phòng hiện tại (Xem & Rời)
# ===========================================================================

@router.get(
    "/my-team",
    response_model=MyRoomResponse,
    summary="Xem sảnh đội hiện tại của tôi",
)
def get_my_team(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Xem đội/sảnh hiện tại của bạn:
    - Hiển thị danh sách các thành viên trong đội (ai là trưởng nhóm, ai là thành viên).
    - Hiển thị trạng thái đang chờ hay đã đủ người, và mở Code Game khi trận đã sẵn sàng.
    """
    return matchmaking_crud.get_my_current_room(db, user_id=current_user.id)


@router.post(
    "/leave-team",
    summary="Rời khỏi sảnh đội hiện tại",
)
def leave_team(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rời khỏi đội:
    - Nếu thành viên rời: Giảm số người trong đội.
    - Nếu trưởng nhóm rời và còn thành viên: Chuyển quyền trưởng nhóm cho người tiếp theo.
    - Nếu sảnh không còn ai: Tự động giải tán sảnh.
    """
    return matchmaking_crud.leave_current_room(db, user_id=current_user.id)


# ===========================================================================
# 4. Tương thích ngược (Backward Compatibility)
# ===========================================================================

@router.post(
    "/rooms",
    response_model=MatchRoomOut,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo sảnh đội (Tương thích ngược)",
    include_in_schema=False,
)
def create_room_legacy(
    data: CreateMatchRoomRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return matchmaking_crud.create_room(db, user_id=current_user.id, data=data)


@router.post(
    "/quick-match",
    response_model=QuickMatchResponse,
    summary="Vào đội nhanh (Tương thích ngược)",
    include_in_schema=False,
)
def quick_match_legacy(
    data: QuickMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return matchmaking_crud.quick_match(db, user_id=current_user.id, data=data)


@router.get(
    "/my-room",
    response_model=MyRoomResponse,
    summary="Xem phòng hiện tại (Tương thích ngược)",
    include_in_schema=False,
)
def get_my_room_legacy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return matchmaking_crud.get_my_current_room(db, user_id=current_user.id)


@router.post(
    "/leave-room",
    summary="Rời phòng (Tương thích ngược)",
    include_in_schema=False,
)
def leave_room_legacy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return matchmaking_crud.leave_current_room(db, user_id=current_user.id)
