"""CRUD và Thuật toán Auto Matchmaking tinh gọn cho Web GameConnect."""
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.matchmaking import MatchRoom, MatchRoomMember, RoomStatus
from app.models.user import User
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.notification import Notification
from app.models.block import Block
from app.schemas.matchmaking import (
    CreateMatchRoomRequest,
    QuickMatchRequest,
    QuickMatchResponse,
    MatchRoomOut,
    RoomMemberOut,
    MyRoomResponse,
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


def create_room(db: Session, user_id: int, data: CreateMatchRoomRequest) -> MatchRoomOut:
    """Chủ phòng tạo phòng chơi với Code Game."""
    # 1. Kiểm tra xem người này có đang ở trong phòng khác chưa
    existing_room = db.scalar(
        select(MatchRoomMember)
        .join(MatchRoom, MatchRoomMember.room_id == MatchRoom.id)
        .where(
            and_(
                MatchRoomMember.user_id == user_id,
                MatchRoom.status == RoomStatus.WAITING,
            )
        )
    )
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn đang ở trong một phòng khác rồi. Vui lòng rời phòng hiện tại trước khi tạo phòng mới!"
        )

    # 2. Kiểm tra Game có tồn tại không
    game = db.get(Game, data.game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game id={data.game_id} không tồn tại trong hệ thống."
        )

    # 3. KIỂM TRA DỮ LIỆU RANK CỦA GAME NÀY TRONG SQL
    game_ranks = list(db.scalars(select(GameRank).where(GameRank.game_id == data.game_id)))

    min_rank_id = data.min_rank_id if (data.min_rank_id and data.min_rank_id > 0) else None
    max_rank_id = data.max_rank_id if (data.max_rank_id and data.max_rank_id > 0) else None

    if len(game_ranks) == 0:
        # Game KHÔNG CÓ dữ liệu rank trong SQL (ví dụ Among Us)
        if min_rank_id is not None or max_rank_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Game '{game.name}' không có hệ thống rank trong cơ sở dữ liệu. Vui lòng để trống min_rank_id và max_rank_id (để null)!"
            )
        min_rank_id = None
        max_rank_id = None
    else:
        # Game CÓ dữ liệu rank trong SQL (ví dụ LOL, Valorant)
        min_rank_obj = None
        max_rank_obj = None
        if min_rank_id:
            min_rank_obj = db.get(GameRank, min_rank_id)
            if not min_rank_obj or min_rank_obj.game_id != data.game_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rank id={min_rank_id} không thuộc về game '{game.name}'."
                )
        if max_rank_id:
            max_rank_obj = db.get(GameRank, max_rank_id)
            if not max_rank_obj or max_rank_obj.game_id != data.game_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rank id={max_rank_id} không thuộc về game '{game.name}'."
                )
        if min_rank_obj and max_rank_obj:
            if min_rank_obj.rank_order > max_rank_obj.rank_order:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rank tối thiểu ({min_rank_obj.rank_name}) không được cao hơn rank tối đa ({max_rank_obj.rank_name})!"
                )

    # 4. Xử lý Label (Phong cách chơi)
    label = data.label.strip() if (data.label and data.label.strip()) else None

    # 5. Tạo phòng mới
    room = MatchRoom(
        host_id=user_id,
        game_id=data.game_id,
        room_name=data.room_name,
        game_code=data.game_code,
        max_players=data.max_players,
        current_players=1,
        min_rank_id=min_rank_id,
        max_rank_id=max_rank_id,
        label=label,
        status=RoomStatus.WAITING,
    )
    db.add(room)
    db.flush()

    # 6. Thêm Host vào danh sách thành viên
    host_member = MatchRoomMember(
        room_id=room.id,
        user_id=user_id,
        is_host=True,
    )
    db.add(host_member)
    db.commit()
    db.refresh(room)

    return _enrich_room_detail(db, room, current_user_id=user_id)


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
    Kiểm tra xem người tìm (user_label) có được phép vào phòng (room_label) hay không.
    Trả về (is_compatible: bool, match_priority: int).

    Ma trận nghiệp vụ:
    - HARD_RANK chỉ được vào HARD_RANK, phòng HARD_RANK chỉ nhận HARD_RANK.
    - KHONG_TOXIC vào được CHILL_RANK, THUONG, KHONG_TOXIC (Cấm HARD_RANK).
    - THUONG (unrank/thường/unr) vào được THUONG, KHONG_TOXIC (Cấm CHILL_RANK, cấm HARD_RANK).
    - CHILL_RANK vào được CHILL_RANK, KHONG_TOXIC (Cấm THUONG, cấm HARD_RANK).
    """
    u = _normalize_label(user_label)
    r = _normalize_label(room_label)

    # 1. Quy tắc HARD_RANK: Tuyệt đối chỉ ghép với HARD_RANK
    if r == "HARD_RANK" or u == "HARD_RANK":
        if u == "HARD_RANK" and r == "HARD_RANK":
            return True, 3  # Trùng khớp hoàn hảo Hard Rank
        return False, 0     # Không được phép ghép

    # 2. Cả 2 đều không chọn nhãn (tự do)
    if not u and not r:
        return True, 1

    # 3. Nếu phòng không để nhãn (phòng tự do): Chấp nhận mọi người tìm (trừ Hard Rank đã chặn ở trên)
    if not r:
        return True, 1

    # 4. Nếu người tìm không chọn nhãn: Được vào các phòng thường / chill / không toxic
    if not u:
        return True, 1

    # 5. Nếu trùng chính xác nhóm nhãn
    if u == r:
        return True, 3

    # 6. Người tìm là KHONG_TOXIC -> Vào được cả CHILL_RANK và THUONG
    if u == "KHONG_TOXIC" and r in ("CHILL_RANK", "THUONG"):
        return True, 2

    # 7. Người tìm là CHILL_RANK hoặc THUONG vào phòng KHONG_TOXIC
    if u in ("CHILL_RANK", "THUONG") and r == "KHONG_TOXIC":
        return True, 2

    # Các trường hợp còn lại (Ví dụ người tìm là THUONG muốn vào CHILL_RANK, hoặc CHILL_RANK vào THUONG) -> CẤM
    return False, 0


def quick_match(db: Session, user_id: int, data: QuickMatchRequest) -> QuickMatchResponse:
    """Người chơi bấm tìm đội nhanh: Tự động xếp vào phòng đang mở."""
    game_id = data.game_id

    # 1. Kiểm tra xem người này có đang ở phòng WAITING nào chưa
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
        return QuickMatchResponse(
            status="MATCHED",
            message="Bạn đang ở trong phòng này rồi!",
            room=_enrich_room_detail(db, room, current_user_id=user_id),
        )

    # 2. Kiểm tra game có tồn tại không
    game = db.get(Game, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game id={game_id} không tồn tại trong hệ thống."
        )

    # 3. Lấy danh sách những người bị block (không xếp chung phòng)
    blocked_subquery = select(Block.blocked_id).where(Block.blocker_id == user_id)
    blocker_subquery = select(Block.blocker_id).where(Block.blocked_id == user_id)
    blocked_ids = set(db.scalars(blocked_subquery)).union(set(db.scalars(blocker_subquery)))

    # 4. Lấy rank của người chơi nếu có truyền
    player_rank_order = None
    if data.rank_id and data.rank_id > 0:
        p_rank = db.get(GameRank, data.rank_id)
        if p_rank and p_rank.game_id == game_id:
            player_rank_order = p_rank.rank_order

    search_label = data.label.strip() if (data.label and data.label.strip()) else None

    # 5. Lấy danh sách các phòng WAITING còn slot trống
    query = (
        select(MatchRoom)
        .where(
            and_(
                MatchRoom.game_id == game_id,
                MatchRoom.status == RoomStatus.WAITING,
                MatchRoom.current_players < MatchRoom.max_players,
            )
        )
        .order_by(MatchRoom.current_players.desc(), MatchRoom.created_at.asc())
    )
    candidate_rooms = list(db.scalars(query))

    # Lọc phòng hợp lệ (không block, đúng rank nếu có)
    valid_rooms: list[MatchRoom] = []
    for r in candidate_rooms:
        if r.host_id in blocked_ids:
            continue

        room_member_ids = set(db.scalars(select(MatchRoomMember.user_id).where(MatchRoomMember.room_id == r.id)))
        if room_member_ids.intersection(blocked_ids):
            continue

        # Kiểm tra rank nếu phòng có yêu cầu (thực sự hoạt động 100%)
        has_rank_requirement = (r.min_rank_id is not None) or (r.max_rank_id is not None)
        if has_rank_requirement:
            # Nếu phòng có yêu cầu rank mà người tìm không có rank (hoặc rank_id không hợp lệ) -> Loại ngay
            if player_rank_order is None:
                continue

            # Kiểm tra min_rank
            if r.min_rank_id:
                min_r = db.get(GameRank, r.min_rank_id)
                if min_r and player_rank_order < min_r.rank_order:
                    continue  # Rank của người chơi thấp hơn min_rank của phòng -> Loại

            # Kiểm tra max_rank
            if r.max_rank_id:
                max_r = db.get(GameRank, r.max_rank_id)
                if max_r and player_rank_order > max_r.rank_order:
                    continue  # Rank của người chơi cao hơn max_rank của phòng -> Loại

        valid_rooms.append(r)

    # 6. Lọc và xếp thứ tự ưu tiên các phòng theo Ma trận Label
    eligible_rooms: list[tuple[int, MatchRoom]] = []
    for r in valid_rooms:
        compatible, priority = _is_label_compatible(search_label, r.label)
        if compatible:
            eligible_rooms.append((priority, r))

    # Sắp xếp các phòng hợp lệ theo:
    # 1) Độ ưu tiên tương thích label giảm dần (3: trùng hoàn hảo, 2: tương thích, 1: tự do)
    # 2) Số người hiện có giảm dần (ưu tiên phòng sắp đủ người)
    # 3) ID nhỏ hơn xếp trước (phòng tạo trước vào trước)
    eligible_rooms.sort(
        key=lambda item: (item[0], item[1].current_players, -item[1].id),
        reverse=True,
    )

    matched_room: MatchRoom | None = eligible_rooms[0][1] if eligible_rooms else None

    # 7. Xử lý khi tìm thấy phòng
    if matched_room:
        new_member = MatchRoomMember(
            room_id=matched_room.id,
            user_id=user_id,
            is_host=False,
        )
        db.add(new_member)
        matched_room.current_players += 1

        # Kiểm tra nếu đủ người
        if matched_room.current_players >= matched_room.max_players:
            matched_room.status = RoomStatus.FULL

            # Bắn thông báo cho tất cả thành viên trong phòng
            all_members = list(db.scalars(select(MatchRoomMember.user_id).where(MatchRoomMember.room_id == matched_room.id)))
            for mid in all_members:
                noti = Notification(
                    recipient_id=mid,
                    type="TEAM_FULL",
                    content=f"Đội '{matched_room.room_name}' đã đủ người! Mã Code Game: {matched_room.game_code}",
                    link=f"/rooms/{matched_room.id}",
                )
                db.add(noti)

        db.commit()
        db.refresh(matched_room)

        msg = "Ghép phòng thành công!"
        if matched_room.status == RoomStatus.FULL:
            msg = "Đã đủ người! Mã Code Game đã mở khóa."

        return QuickMatchResponse(
            status="MATCHED",
            message=msg,
            room=_enrich_room_detail(db, matched_room, current_user_id=user_id),
        )

    # 8. Nếu không có phòng nào phù hợp
    return QuickMatchResponse(
        status="NO_ROOM",
        message="Hiện tại chưa có phòng nào phù hợp cho game này. Bạn hãy bấm tạo phòng để người khác tham gia nhé!",
        room=None,
    )


def get_my_current_room(db: Session, user_id: int) -> MyRoomResponse:
    """Xem phòng hiện tại của người dùng đang đăng nhập."""
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
            message="Bạn chưa tham gia phòng nào.",
            room=None,
        )

    room = db.get(MatchRoom, member.room_id)
    if not room or room.status == RoomStatus.CANCELLED:
        return MyRoomResponse(
            in_room=False,
            message="Bạn chưa tham gia phòng nào.",
            room=None,
        )

    return MyRoomResponse(
        in_room=True,
        message="Đã tìm thấy phòng hiện tại của bạn.",
        room=_enrich_room_detail(db, room, current_user_id=user_id),
    )


def leave_current_room(db: Session, user_id: int) -> dict:
    """Rời khỏi phòng hiện tại của người dùng."""
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
            detail="Bạn hiện không ở trong phòng nào cả."
        )

    room = db.get(MatchRoom, member.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Phòng không tồn tại.")

    if member.is_host:
        # Nếu là chủ phòng rời -> Đóng phòng
        room.status = RoomStatus.CANCELLED
        db.delete(member)
        db.commit()
        return {"success": True, "message": "Bạn là chủ phòng. Bạn đã rời phòng và phòng này đã được đóng."}
    else:
        # Nếu là thành viên rời -> Giảm người, mở lại WAITING nếu đang FULL
        db.delete(member)
        room.current_players = max(1, room.current_players - 1)
        if room.status == RoomStatus.FULL:
            room.status = RoomStatus.WAITING
        db.commit()
        return {"success": True, "message": "Bạn đã rời phòng thành công."}
