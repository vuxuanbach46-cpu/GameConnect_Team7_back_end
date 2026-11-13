"""CRUD và Thuật toán Auto Matchmaking tinh gọn cho Web GameConnect.

Hỗ trợ đầy đủ luồng:
1. Tạo sảnh đội (Lobby) & Mời bạn bè (+ Mời vào đội qua Notifications)
2. Bạn bè bấm 'Đồng ý tham gia' -> Nhập vào sảnh đội
3. Bấm 'Tìm trận' (Nút cam FIND MATCH) -> Tự động ghép nhóm (3+2=5, 4+1=5...)
4. Khi đủ người -> Bắn thông báo MATCH_FOUND cho cả 5 người và mở Code Game!
"""
import secrets
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.matchmaking import MatchRoom, MatchRoomMember, RoomStatus
from app.models.user import User
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.notification import Notification
from app.models.block import Block
from app.schemas.matchmaking import (
    CreateLobbyRequest,
    CreateMatchRoomRequest,
    FindMatchRequest,
    QuickMatchRequest,
    QuickMatchResponse,
    MatchRoomOut,
    RoomMemberOut,
    MyRoomResponse,
    InviteFriendResponse,
)


def _enrich_room_detail(db: Session, room: MatchRoom, current_user_id: int | None = None) -> MatchRoomOut:
    """Trả về chi tiết phòng và danh sách người trong phòng kèm ID và Username."""
    game = db.get(Game, room.game_id)
    game_name = game.name if game else None

    # Lấy danh sách thành viên trong phòng
    members_stmt = (
        select(MatchRoomMember)
        .where(MatchRoomMember.room_id == room.id)
        .order_by(MatchRoomMember.is_host.desc(), MatchRoomMember.joined_at.asc())
    )
    db_members = list(db.scalars(members_stmt))

    member_user_ids = [m.user_id for m in db_members]
    is_user_in_room = current_user_id in member_user_ids if current_user_id else False

    enriched_members: list[RoomMemberOut] = []
    for m in db_members:
        user = db.get(User, m.user_id)
        username = user.username if user else f"User#{m.user_id}"

        enriched_members.append(
            RoomMemberOut(
                user_id=m.user_id,
                username=username,
                is_host=m.is_host,
                joined_at=m.joined_at,
            )
        )

    # Chỉ hiển thị game_code khi phòng đã FULL hoặc người xem đang ở trong phòng
    should_show_code = (room.status == RoomStatus.FULL) or is_user_in_room
    code_to_show = room.game_code if should_show_code else "****** (Hiện khi đủ người)"

    return MatchRoomOut(
        id=room.id,
        host_id=room.host_id,
        game_id=room.game_id,
        game_name=game_name,
        room_name=room.room_name,
        game_code=code_to_show,
        max_players=room.max_players,
        current_players=room.current_players,
        min_rank_id=room.min_rank_id,
        max_rank_id=room.max_rank_id,
        label=room.label,
        status=room.status,
        members=enriched_members,
        created_at=room.created_at,
        updated_at=room.updated_at,
    )


def _normalize_label(label: str | None) -> str | None:
    """Chuẩn hóa nhãn phong cách chơi để phân loại vào các nhóm tương đương."""
    if not label:
        return None
    cleaned = label.strip().lower()

    # 1. Nhóm HARD_RANK: hard rank, try hard, hardrank, tryhard, hard
    if cleaned in ("hard rank", "hardrank", "try hard", "tryhard", "hard"):
        return "HARD_RANK"

    # 2. Nhóm CHILL_RANK: chill rank, chillrank, chill
    if cleaned in ("chill rank", "chillrank", "chill"):
        return "CHILL_RANK"

    # 3. Nhóm THUONG / UNRANK: thường, thuong, unrank, unr
    if cleaned in ("thường", "thuong", "unrank", "unr"):
        return "THUONG"

    # 4. Nhóm KHONG_TOXIC: không toxic, khong toxic, nontoxic, non toxic, khongtoxic
    if cleaned in ("không toxic", "khong toxic", "nontoxic", "non toxic", "khongtoxic"):
        return "KHONG_TOXIC"

    return cleaned


def _is_label_compatible(user_label: str | None, room_label: str | None) -> tuple[bool, int]:
    """
    Kiểm tra tương thích nhãn phong cách chơi giữa người tìm và phòng.
    Trả về (is_compatible: bool, match_priority: int).
    """
    u = _normalize_label(user_label)
    r = _normalize_label(room_label)

    # 1. HARD_RANK chỉ ghép với HARD_RANK
    if r == "HARD_RANK" or u == "HARD_RANK":
        if u == "HARD_RANK" and r == "HARD_RANK":
            return True, 3
        return False, 0

    # 2. Cả 2 đều tự do
    if not u and not r:
        return True, 1

    # 3. Phòng tự do
    if not r:
        return True, 1

    # 4. Người tìm tự do
    if not u:
        return True, 1

    # 5. Trùng khớp chính xác
    if u == r:
        return True, 3

    # 6. KHONG_TOXIC vào được CHILL_RANK và THUONG
    if u == "KHONG_TOXIC" and r in ("CHILL_RANK", "THUONG"):
        return True, 2

    # 7. CHILL_RANK hoặc THUONG vào phòng KHONG_TOXIC
    if u in ("CHILL_RANK", "THUONG") and r == "KHONG_TOXIC":
        return True, 2

    return False, 0


# ===========================================================================
# 1. Sảnh đội (Lobby) & Mời bạn bè (+ Mời vào đội)
# ===========================================================================

def create_or_get_lobby(db: Session, user_id: int, data: CreateLobbyRequest | CreateMatchRoomRequest) -> MatchRoomOut:
    """Tạo mới hoặc lấy sảnh đội hiện tại của người dùng."""
    # Kiểm tra xem người này có đang ở sảnh WAITING nào không
    existing_member = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status == RoomStatus.WAITING,
            )
        )
    )
    if existing_member:
        room = db.get(MatchRoom, existing_member.room_id)
        if room and existing_member.is_host:
            # Cập nhật cài đặt sảnh nếu là chủ phòng
            room.game_id = data.game_id
            room.max_players = data.max_players
            room.min_rank_id = data.min_rank_id if (data.min_rank_id and data.min_rank_id > 0) else None
            room.max_rank_id = data.max_rank_id if (data.max_rank_id and data.max_rank_id > 0) else None
            room.label = _normalize_label(data.label)
            db.commit()
            db.refresh(room)
        return _enrich_room_detail(db, room, current_user_id=user_id)

    # Kiểm tra Game
    game = db.get(Game, data.game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game id={data.game_id} không tồn tại trong hệ thống."
        )

    # Kiểm tra Rank
    min_rank_id = data.min_rank_id if (data.min_rank_id and data.min_rank_id > 0) else None
    max_rank_id = data.max_rank_id if (data.max_rank_id and data.max_rank_id > 0) else None

    user = db.get(User, user_id)
    username = user.username if user else "Người chơi"
    game_code = getattr(data, "game_code", None) or f"GC-{secrets.token_hex(3).upper()}"
    room_name = getattr(data, "room_name", None) or f"Đội của {username}"

    # Tạo sảnh mới
    room = MatchRoom(
        host_id=user_id,
        game_id=data.game_id,
        room_name=room_name,
        game_code=game_code,
        max_players=data.max_players,
        current_players=1,
        min_rank_id=min_rank_id,
        max_rank_id=max_rank_id,
        label=data.label,
        status=RoomStatus.WAITING,
    )
    db.add(room)
    db.flush()

    host_member = MatchRoomMember(
        room_id=room.id,
        user_id=user_id,
        is_host=True,
    )
    db.add(host_member)
    db.commit()
    db.refresh(room)

    return _enrich_room_detail(db, room, current_user_id=user_id)


def create_room(db: Session, user_id: int, data: CreateMatchRoomRequest) -> MatchRoomOut:
    """Tương thích ngược với create_room."""
    return create_or_get_lobby(db, user_id, data)


def invite_friend_to_lobby(db: Session, user_id: int, friend_id: int) -> InviteFriendResponse:
    """Chủ sảnh gửi lời mời tham gia đội đến một người bạn (Bắn thông báo vào Notifications)."""
    if user_id == friend_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn không thể tự mời chính mình vào đội!"
        )

    # 1. Lấy sảnh WAITING của người mời
    member = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status == RoomStatus.WAITING,
            )
        )
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn chưa có sảnh đội nào đang mở. Vui lòng tạo sảnh trước khi mời bạn bè!"
        )

    room = db.get(MatchRoom, member.room_id)
    if not room or room.status != RoomStatus.WAITING:
        raise HTTPException(status_code=400, detail="Sảnh đội hiện không khả dụng.")

    if room.current_players >= room.max_players:
        raise HTTPException(status_code=400, detail="Sảnh đội của bạn đã đủ thành viên!")

    # 2. Kiểm tra bạn bè
    friend = db.get(User, friend_id)
    if not friend:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng này.")

    # 3. Kiểm tra xem bạn bè đã ở trong sảnh này chưa
    already_in = db.scalar(
        select(MatchRoomMember).where(
            and_(
                MatchRoomMember.room_id == room.id,
                MatchRoomMember.user_id == friend_id,
            )
        )
    )
    if already_in:
        raise HTTPException(status_code=400, detail=f"{friend.username} đã có mặt trong đội của bạn rồi!")

    # 4. Kiểm tra chặn (Block)
    is_blocked = db.scalar(
        select(Block).where(
            or_(
                and_(Block.blocker_id == user_id, Block.blocked_id == friend_id),
                and_(Block.blocker_id == friend_id, Block.blocked_id == user_id),
            )
        )
    )
    if is_blocked:
        raise HTTPException(status_code=400, detail="Không thể gửi lời mời do có chặn giữa hai tài khoản.")

    # 5. Tạo thông báo PARTY_INVITE gửi đến bạn bè
    user = db.get(User, user_id)
    sender_name = user.username if user else "Một người bạn"
    game = db.get(Game, room.game_id)
    game_name = game.name if game else "Game"

    noti = Notification(
        recipient_id=friend_id,
        type="PARTY_INVITE",
        content=f"{sender_name} đã mời bạn tham gia đội chơi {game_name}!",
        link=f"/api/matchmaking/accept-invite/{room.id}",
    )
    db.add(noti)
    db.commit()
    db.refresh(noti)

    return InviteFriendResponse(
        message=f"Đã gửi lời mời tham gia đội đến {friend.username} thành công!",
        friend_id=friend.id,
        friend_username=friend.username,
        notification_id=noti.id,
    )


def accept_lobby_invite(db: Session, user_id: int, room_id: int) -> MatchRoomOut:
    """Người được mời bấm 'Đồng ý tham gia' từ Notifications -> Gia nhập sảnh đội."""
    room = db.get(MatchRoom, room_id)
    if not room or room.status != RoomStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sảnh đội này không tồn tại hoặc đã đủ người / đã đóng."
        )

    if room.current_players >= room.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sảnh đội đã đủ người, không thể tham gia thêm."
        )

    # Nếu đã ở trong sảnh này rồi
    existing = db.scalar(
        select(MatchRoomMember).where(
            and_(
                MatchRoomMember.room_id == room.id,
                MatchRoomMember.user_id == user_id,
            )
        )
    )
    if existing:
        return _enrich_room_detail(db, room, current_user_id=user_id)

    # Nếu đang ở một sảnh WAITING khác -> Tự động rời sảnh cũ trước
    old_membership = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status == RoomStatus.WAITING,
                MatchRoom.id != room.id,
            )
        )
    )
    if old_membership:
        old_room = db.get(MatchRoom, old_membership.room_id)
        db.delete(old_membership)
        if old_room:
            old_room.current_players = max(1, old_room.current_players - 1)
            if old_membership.is_host:
                old_room.status = RoomStatus.CANCELLED

    # Thêm vào sảnh mới
    new_member = MatchRoomMember(
        room_id=room.id,
        user_id=user_id,
        is_host=False,
    )
    db.add(new_member)
    room.current_players += 1

    # Nếu vừa đủ người
    if room.current_players >= room.max_players:
        room.status = RoomStatus.FULL
        all_members = list(db.scalars(select(MatchRoomMember.user_id).where(MatchRoomMember.room_id == room.id)))
        for mid in all_members:
            noti = Notification(
                recipient_id=mid,
                type="MATCH_FOUND",
                content=f"Đội '{room.room_name}' đã đủ người! Mã Code Game: {room.game_code}",
                link=f"/rooms/{room.id}",
            )
            db.add(noti)

    # Đánh dấu thông báo mời liên quan là đã đọc
    pending_notis = list(
        db.scalars(
            select(Notification).where(
                and_(
                    Notification.recipient_id == user_id,
                    Notification.type == "PARTY_INVITE",
                    Notification.link.contains(str(room.id)),
                )
            )
        )
    )
    for n in pending_notis:
        n.is_read = True

    db.commit()
    db.refresh(room)
    return _enrich_room_detail(db, room, current_user_id=user_id)


# ===========================================================================
# 2. Tìm trận tự động (Nút cam FIND MATCH) & Ghép nhóm thông minh
# ===========================================================================

def find_match(db: Session, user_id: int, data: FindMatchRequest | QuickMatchRequest) -> QuickMatchResponse:
    """Nút cam FIND MATCH: Tự động gom người lẻ và các nhóm (3+2=5, 4+1=5...) thành 1 phòng."""
    game_id = data.game_id

    # 1. Kiểm tra xem người dùng đang có sảnh WAITING nào không
    member = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status == RoomStatus.WAITING,
            )
        )
    )

    if member:
        my_room = db.get(MatchRoom, member.room_id)
        # Chỉ trưởng nhóm mới có quyền bấm Tìm trận
        if not member.is_host:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bạn đang ở trong một đội. Chỉ có trưởng nhóm mới có quyền bấm Tìm trận!"
            )
        if data.label:
            my_room.label = _normalize_label(data.label)
    else:
        # Người đi một mình (solo) chưa tạo sảnh -> Tự động sinh sảnh 1 người
        game = db.get(Game, game_id)
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Game id={game_id} không tồn tại trong hệ thống."
            )
        user = db.get(User, user_id)
        username = user.username if user else "Người chơi"

        my_room = MatchRoom(
            host_id=user_id,
            game_id=game_id,
            room_name=f"Đội của {username}",
            game_code=f"GC-{secrets.token_hex(3).upper()}",
            max_players=5,
            current_players=1,
            label=_normalize_label(data.label),
            status=RoomStatus.WAITING,
        )
        db.add(my_room)
        db.flush()

        db.add(MatchRoomMember(room_id=my_room.id, user_id=user_id, is_host=True))
        db.flush()

    # Kiểm tra số lượng người còn thiếu để đủ đội
    needed = my_room.max_players - my_room.current_players
    if needed <= 0:
        my_room.status = RoomStatus.FULL
        db.commit()
        return QuickMatchResponse(
            status="MATCHED",
            message="Đội của bạn đã đủ người!",
            room=_enrich_room_detail(db, my_room, user_id),
        )

    # 2. Lấy danh sách những người bị block liên quan đến các thành viên trong đội mình
    my_members_ids = set(db.scalars(select(MatchRoomMember.user_id).where(MatchRoomMember.room_id == my_room.id)))
    blocked_subquery = select(Block.blocked_id).where(Block.blocker_id.in_(my_members_ids))
    blocker_subquery = select(Block.blocker_id).where(Block.blocked_id.in_(my_members_ids))
    all_blocked_ids = set(db.scalars(blocked_subquery)).union(set(db.scalars(blocker_subquery)))

    # 3. Lấy rank người tìm nếu có
    player_rank_order = None
    if data.rank_id and data.rank_id > 0:
        p_rank = db.get(GameRank, data.rank_id)
        if p_rank and p_rank.game_id == game_id:
            player_rank_order = p_rank.rank_order

    # 4. Tìm các sảnh/nhóm khác cùng Game đang WAITING
    query = (
        select(MatchRoom)
        .where(
            and_(
                MatchRoom.id != my_room.id,
                MatchRoom.game_id == game_id,
                MatchRoom.status == RoomStatus.WAITING,
                MatchRoom.current_players <= needed,
            )
        )
        .order_by(MatchRoom.current_players.desc(), MatchRoom.created_at.asc())
    )
    candidates = list(db.scalars(query))

    valid_candidates: list[tuple[int, MatchRoom]] = []
    for cand in candidates:
        # Không ghép với người bị block
        cand_member_ids = set(db.scalars(select(MatchRoomMember.user_id).where(MatchRoomMember.room_id == cand.id)))
        if cand_member_ids.intersection(all_blocked_ids):
            continue

        # Kiểm tra rank nếu phòng có yêu cầu
        cand_has_rank = (cand.min_rank_id is not None) or (cand.max_rank_id is not None)
        if cand_has_rank:
            if player_rank_order is None:
                continue
            if cand.min_rank_id:
                min_r = db.get(GameRank, cand.min_rank_id)
                if min_r and player_rank_order < min_r.rank_order:
                    continue
            if cand.max_rank_id:
                max_r = db.get(GameRank, cand.max_rank_id)
                if max_r and player_rank_order > max_r.rank_order:
                    continue

        # Kiểm tra tương thích nhãn phong cách chơi
        compatible, priority = _is_label_compatible(my_room.label, cand.label)
        if not compatible:
            continue

        valid_candidates.append((priority, cand))

    # Sắp xếp ưu tiên:
    # 1. Trùng khít số lượng cần tìm (ví dụ cần 2 người gặp đúng nhóm 2 người)
    # 2. Độ ưu tiên nhãn (3 > 2 > 1)
    # 3. Số người trong nhóm ứng viên giảm dần
    valid_candidates.sort(
        key=lambda item: (
            1 if item[1].current_players == needed else 0,
            item[0],
            item[1].current_players,
            -item[1].id,
        ),
        reverse=True,
    )

    # 5. Thực hiện gộp nhóm (Merge Parties)
    for _, cand in valid_candidates:
        remaining_needed = my_room.max_players - my_room.current_players
        if cand.current_players <= remaining_needed:
            # Chuyển toàn bộ thành viên của cand sang my_room
            cand_members = list(db.scalars(select(MatchRoomMember).where(MatchRoomMember.room_id == cand.id)))
            for cm in cand_members:
                cm.room_id = my_room.id
                cm.is_host = False

            my_room.current_players += cand.current_players
            cand.status = RoomStatus.CANCELLED

            if my_room.current_players >= my_room.max_players:
                break

    # 6. Kiểm tra xem đã đủ 5 người chưa
    if my_room.current_players >= my_room.max_players:
        my_room.status = RoomStatus.FULL
        if not my_room.game_code or my_room.game_code == "AUTO":
            my_room.game_code = f"GC-{secrets.token_hex(3).upper()}"

        # Bắn thông báo MATCH_FOUND cho toàn bộ thành viên trong đội
        final_member_ids = list(db.scalars(select(MatchRoomMember.user_id).where(MatchRoomMember.room_id == my_room.id)))
        for mid in final_member_ids:
            noti = Notification(
                recipient_id=mid,
                type="MATCH_FOUND",
                content=f"Đã tìm thấy phòng cho đội '{my_room.room_name}'! Mã Code Game: {my_room.game_code}",
                link=f"/rooms/{my_room.id}",
            )
            db.add(noti)

        db.commit()
        db.refresh(my_room)
        return QuickMatchResponse(
            status="MATCHED",
            message="Đã tìm thấy phòng và tự động ghép đội thành công!",
            room=_enrich_room_detail(db, my_room, user_id),
        )

    # Nếu vẫn chưa đủ người -> Tiếp tục ở trạng thái chờ
    db.commit()
    db.refresh(my_room)
    return QuickMatchResponse(
        status="SEARCHING",
        message=f"Đang tìm kiếm thêm đồng đội... ({my_room.current_players}/{my_room.max_players} thành viên)",
        room=_enrich_room_detail(db, my_room, user_id),
    )


def quick_match(db: Session, user_id: int, data: QuickMatchRequest) -> QuickMatchResponse:
    """Tương thích ngược với quick_match."""
    return find_match(db, user_id, data)


def cancel_search(db: Session, user_id: int) -> dict:
    """Hủy tìm trận khi đang trong hàng chờ."""
    member = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status == RoomStatus.WAITING,
            )
        )
    )
    if not member:
        return {"success": True, "message": "Bạn hiện không ở trong hàng chờ tìm trận."}

    room = db.get(MatchRoom, member.room_id)
    if not member.is_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ có trưởng nhóm mới có quyền hủy tìm trận!"
        )

    # Nếu sảnh chỉ có 1 mình -> đóng sảnh
    if room.current_players <= 1:
        room.status = RoomStatus.CANCELLED
        db.delete(member)
        db.commit()
        return {"success": True, "message": "Đã hủy tìm trận thành công."}

    # Nếu là nhóm nhiều người -> giữ nguyên sảnh nhưng hủy trạng thái tìm trận
    db.commit()
    return {"success": True, "message": "Đã dừng tìm trận. Đội của bạn vẫn được giữ nguyên sảnh."}


# ===========================================================================
# 3. Quản lý Đội / Phòng hiện tại (Xem & Rời)
# ===========================================================================

def get_my_current_room(db: Session, user_id: int) -> MyRoomResponse:
    """Xem sảnh/phòng hiện tại của người dùng đang đăng nhập."""
    member = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status != RoomStatus.CANCELLED,
            )
        )
        .order_by(MatchRoom.created_at.desc())
    )
    if not member:
        return MyRoomResponse(
            in_room=False,
            message="Bạn chưa tham gia đội nào.",
            room=None,
        )

    room = db.get(MatchRoom, member.room_id)
    if not room or room.status == RoomStatus.CANCELLED:
        return MyRoomResponse(
            in_room=False,
            message="Bạn chưa tham gia đội nào.",
            room=None,
        )

    return MyRoomResponse(
        in_room=True,
        message="Đã tìm thấy đội hiện tại của bạn.",
        room=_enrich_room_detail(db, room, current_user_id=user_id),
    )


def leave_current_room(db: Session, user_id: int) -> dict:
    """Rời khỏi đội / sảnh hiện tại."""
    member = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status != RoomStatus.CANCELLED,
            )
        )
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn hiện không ở trong đội nào cả."
        )

    room = db.get(MatchRoom, member.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Phòng không tồn tại.")

    # Kiểm tra xem còn thành viên khác trong phòng không
    other_members = list(
        db.scalars(
            select(MatchRoomMember).where(
                and_(
                    MatchRoomMember.room_id == room.id,
                    MatchRoomMember.user_id != user_id,
                )
            )
        )
    )

    if member.is_host:
        if other_members:
            # Chuyển quyền trưởng nhóm cho thành viên tiếp theo
            new_host = other_members[0]
            new_host.is_host = True
            room.host_id = new_host.user_id
            room.current_players = max(1, room.current_players - 1)
            if room.status == RoomStatus.FULL:
                room.status = RoomStatus.WAITING
            db.delete(member)
            db.commit()
            return {"success": True, "message": "Bạn đã rời đội. Quyền trưởng nhóm đã được chuyển cho thành viên tiếp theo."}
        else:
            # Không còn ai -> Hủy phòng
            room.status = RoomStatus.CANCELLED
            db.delete(member)
            db.commit()
            return {"success": True, "message": "Bạn đã rời đội và giải tán sảnh."}
    else:
        # Thành viên thường rời đội
        db.delete(member)
        room.current_players = max(1, room.current_players - 1)
        if room.status == RoomStatus.FULL:
            room.status = RoomStatus.WAITING
        db.commit()
        return {"success": True, "message": "Bạn đã rời đội thành công."}
