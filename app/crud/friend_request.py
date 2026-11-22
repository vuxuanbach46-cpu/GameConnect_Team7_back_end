"""Nghiệp vụ gửi, hủy, xem và xử lý lời mời kết bạn."""

from typing import Optional
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud.notification import create_notification
from app.models.user import User
from app.models.friend_request import FriendRequest
from app.models.friendships import Friendship
from app.models.block import Block
from app.models.gamer_profile import GamerProfile
from app.models.user_game import UserGame
from app.models.game import Game
from app.models.game_rank import GameRank
from app.models.game_role import GameRole
from app.models.matchmaking import MatchRoom, MatchRoomMember, RoomStatus


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
    """Gửi lời mời kết bạn và tạo thông báo cho người nhận."""

    sender_id = sender.id

    # VALIDATE 1: Không được gửi lời mời cho chính mình
    if sender_id == receiver_id:
        raise HTTPException(
            status_code=400,
            detail="Không thể gửi lời mời cho chính mình"
        )

    # VALIDATE 2: Kiểm tra người nhận có tồn tại không
    receiver = db.query(User).filter(
        User.id == receiver_id
    ).first()

    if receiver is None:
        raise HTTPException(
            status_code=404,
            detail="Người nhận không tồn tại"
        )

    # VALIDATE 3: Kiểm tra trạng thái tài khoản người nhận
    if receiver.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Tài khoản người nhận không hoạt động"
        )

    # VALIDATE 4: Kiểm tra hai người đã là bạn bè chưa
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

    # VALIDATE 5: Kiểm tra có bị chặn không
    if check_block(db, sender_id, receiver_id):
        raise HTTPException(
            status_code=403,
            detail="Một trong hai người đã chặn người còn lại"
        )

    # VALIDATE 6: Nếu người nhận đã gửi lời mời cho người gửi,
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

            # Tạo thông báo cho người gửi ban đầu rằng lời mời đã được đồng ý
            create_notification(
                db=db,
                recipient_id=receiver.id,
                type="FRIEND_ACCEPTED",
                content=f"{sender.username} đã chấp nhận lời mời kết bạn",
                link=f"/friends/requests/{reverse_request.id}"
            )

            db.commit()
            db.refresh(reverse_request)

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Quan hệ bạn bè đã tồn tại"
            )
        except Exception:
            db.rollback()
            raise

        return reverse_request

    # VALIDATE 7: Không cho gửi trùng lời mời đang chờ
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

    # TẠO LỜI MỜI KẾT BẠN
    request = FriendRequest(
        sender_id=sender_id,
        receiver_id=receiver_id,
        status="PENDING"
    )

    try:
        db.add(request)

        # Lưu tạm để lấy ID lời mời
        db.flush()

        # TẠO THÔNG BÁO CHO NGƯỜI NHẬN
        create_notification(
            db=db,
            recipient_id=receiver.id,
            type="FRIEND_REQUEST",
            content=f"{sender.username} đã gửi lời mời kết bạn",
            link=f"/friends/requests/{request.id}"
        )

        # Lưu lời mời và thông báo
        db.commit()
        db.refresh(request)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Không thể tạo lời mời kết bạn"
        )

    except Exception:
        db.rollback()
        raise

    return request


def cancel_friend_request(
    db: Session,
    sender: User,
    request_id: int
):
    """Hủy lời mời kết bạn đã gửi."""

    request = db.query(FriendRequest).filter(
        FriendRequest.id == request_id
    ).first()

    # Kiểm tra lời mời có tồn tại không
    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Lời mời kết bạn không tồn tại"
        )

    # Chỉ người gửi mới được hủy
    if request.sender_id != sender.id:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền hủy lời mời này"
        )

    # Chỉ hủy lời mời đang chờ
    if request.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Chỉ có thể hủy lời mời đang chờ"
        )

    try:
        request.status = "CANCELLED"

        db.commit()
        db.refresh(request)

    except Exception:
        db.rollback()
        raise

    return request


def get_sent_friend_requests(
    db: Session,
    current_user: User,
    status: Optional[str] = "PENDING",
    skip: int = 0,
    limit: int = 20
):
    """Danh sách lời mời do người đăng nhập gửi (mặc định chỉ lấy lời mời đang chờ, có phân trang)."""

    query = db.query(
        FriendRequest, User
    ).join(
        User, User.id == FriendRequest.receiver_id
    ).filter(
        FriendRequest.sender_id == current_user.id
    )

    if status:
        query = query.filter(FriendRequest.status == status)

    return (
        query.order_by(FriendRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_received_friend_requests(
    db: Session,
    current_user: User,
    status: Optional[str] = "PENDING",
    skip: int = 0,
    limit: int = 20
):
    """Danh sách lời mời người khác gửi cho người đăng nhập (mặc định chỉ lấy lời mời đang chờ, có phân trang)."""

    query = db.query(
        FriendRequest, User
    ).join(
        User, User.id == FriendRequest.sender_id
    ).filter(
        FriendRequest.receiver_id == current_user.id
    )

    if status:
        query = query.filter(FriendRequest.status == status)

    return (
        query.order_by(FriendRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


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

    # Kiểm tra người gửi lời mời có còn tồn tại và hoạt động không
    sender = db.query(User).filter(
        User.id == request.sender_id
    ).first()

    if not sender:
        raise HTTPException(
            status_code=404,
            detail="Người gửi lời mời không còn tồn tại"
        )

    if sender.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Tài khoản người gửi không hoạt động"
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

        # TẠO THÔNG BÁO CHO NGƯỜI GỬI BIẾT LỜI MỜI ĐÃ ĐƯỢC CHẤP NHẬN
        create_notification(
            db=db,
            recipient_id=sender.id,
            type="FRIEND_ACCEPTED",
            content=f"{current_user.username} đã chấp nhận lời mời kết bạn",
            link=f"/friends/requests/{request.id}"
        )

        db.commit()
        db.refresh(request)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Không thể tạo quan hệ bạn bè"
        )

    except Exception:
        db.rollback()
        raise

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

    try:
        request.status = "REJECTED"

        db.commit()
        db.refresh(request)

    except Exception:
        db.rollback()
        raise

    return request


def unfriend(db: Session, current_user: User, friend_id: int) -> User:
    """Hủy quan hệ bạn bè giữa hai người."""
    if current_user.id == friend_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể hủy kết bạn với chính mình"
        )

    friend = db.query(User).filter(User.id == friend_id).first()
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại"
        )

    user_a, user_b = sorted((current_user.id, friend_id))
    friendship = db.query(Friendship).filter(
        Friendship.user_a == user_a,
        Friendship.user_b == user_b
    ).first()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bạn và {friend.username} chưa phải là bạn bè"
        )

    try:
        # Xóa quan hệ bạn bè trong bảng friendships
        db.delete(friendship)

        # Xóa các bản ghi lời mời kết bạn cũ giữa 2 người để sau này có thể gửi lại lời mời mới
        db.query(FriendRequest).filter(
            or_(
                and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == friend_id),
                and_(FriendRequest.sender_id == friend_id, FriendRequest.receiver_id == current_user.id)
            )
        ).delete(synchronize_session=False)

        db.commit()
    except Exception:
        db.rollback()
        raise

    return friend


def _get_real_user_card(
    db: Session,
    target_user: User,
    current_user_id: int,
) -> dict:
    """Truy vấn đầy đủ thông tin thật từ Database cho thẻ người chơi:
    - user_id, username, display_name, avatar, region, play_time, has_mic
    - mutual_friends_count
    - in_room, room_info (nếu đang trong MatchRoom có status == WAITING)
    - games (danh sách toàn bộ game từ user_games join games, game_ranks, game_roles)
    - primary_game (phần tử đầu tiên trong games hoặc None)
    """
    # 1. Lấy display_name, avatar, region, play_time, has_mic từ GamerProfile
    display_name = target_user.username
    avatar = None
    region = None
    play_time = None
    has_mic = False
    try:
        prof_row = (
            db.query(
                GamerProfile.display_name,
                GamerProfile.avatar,
                GamerProfile.region,
                GamerProfile.play_time,
                GamerProfile.has_mic,
            )
            .filter(GamerProfile.user_id == target_user.id)
            .first()
        )
        if prof_row:
            if prof_row[0]:
                display_name = prof_row[0]
            avatar = prof_row[1]
            region = prof_row[2]
            play_time = prof_row[3]
            has_mic = bool(prof_row[4]) if prof_row[4] is not None else False
    except Exception:
        db.rollback()

    # 2. Tính số bạn chung thực tế giữa current_user_id và target_user.id
    mutual_friends_count = 0
    if current_user_id != target_user.id:
        try:
            my_friends = get_user_friend_ids(db, current_user_id)
            target_friends = get_user_friend_ids(db, target_user.id)
            mutual_friends_count = len(my_friends.intersection(target_friends))
        except Exception:
            db.rollback()
            mutual_friends_count = 0

    # 3. Kiểm tra trạng thái phòng chờ (MatchRoom có status == WAITING)
    in_room = False
    room_info = None
    try:
        active_room = (
            db.query(MatchRoom)
            .join(MatchRoomMember, MatchRoomMember.room_id == MatchRoom.id)
            .filter(
                and_(
                    MatchRoomMember.user_id == target_user.id,
                    MatchRoom.status == RoomStatus.WAITING,
                )
            )
            .order_by(MatchRoom.created_at.desc())
            .first()
        )
        if active_room:
            in_room = True
            room_info = {
                "room_id": active_room.id,
                "room_name": active_room.room_name,
                "current_players": active_room.current_players,
                "max_players": active_room.max_players,
                "label": active_room.label,
            }
    except Exception:
        db.rollback()
        in_room = False
        room_info = None

    # 4. Lấy danh sách toàn bộ games từ user_games (join games, game_ranks, game_roles)
    games_list: list[dict] = []
    try:
        ug_rows = (
            db.query(UserGame)
            .filter(UserGame.user_id == target_user.id)
            .order_by(UserGame.updated_at.desc(), UserGame.id.asc())
            .all()
        )
        for ug in ug_rows:
            game = None
            rank = None
            role_obj = None
            try:
                game = db.query(Game).filter(Game.id == ug.game_id).first()
            except Exception:
                db.rollback()
            if ug.rank_id:
                try:
                    rank = db.query(GameRank).filter(GameRank.id == ug.rank_id).first()
                except Exception:
                    db.rollback()
            if ug.role_id:
                try:
                    role_obj = db.query(GameRole).filter(GameRole.id == ug.role_id).first()
                except Exception:
                    db.rollback()

            rank_name = (
                getattr(rank, "rank_name", None) or getattr(rank, "name", None)
                if rank
                else None
            )
            rank_tier = (
                getattr(rank, "rank_tier", None)
                if (rank and hasattr(rank, "rank_tier"))
                else (getattr(rank, "rank_order", None) if rank else None)
            )
            rank_icon = getattr(rank, "icon_url", None) if rank else None
            role_name = (
                getattr(role_obj, "role_name", None) or getattr(role_obj, "name", None)
                if role_obj
                else None
            )
            roles_arr = [role_name] if role_name else []

            games_list.append({
                "game_id": ug.game_id,
                "game_name": game.name if game else None,
                "game_image": game.image if game else None,
                "rank_id": ug.rank_id,
                "rank_name": rank_name,
                "rank_tier": rank_tier,
                "rank_icon": rank_icon,
                "role_id": ug.role_id,
                "role_name": role_name,
                "roles": roles_arr,
                "in_game_id": ug.in_game_id,
                "in_game_name": ug.in_game_id,
                "elo": getattr(ug, "elo", None) or ug.in_game_id,
            })
    except Exception:
        db.rollback()
        games_list = []

    primary_game = games_list[0] if games_list else None

    return {
        "user_id": target_user.id,
        "username": target_user.username,
        "display_name": display_name,
        "avatar": avatar,
        "region": region,
        "play_time": play_time,
        "has_mic": has_mic,
        "last_seen": target_user.last_seen,
        "mutual_friends_count": mutual_friends_count,
        "in_room": in_room,
        "room_info": room_info,
        "games": games_list,
        "primary_game": primary_game,
    }


_build_player_card_info = _get_real_user_card


def get_friends_list(db: Session, current_user: User, skip: int = 0, limit: int = 50):
    """Lấy danh sách bạn bè hiện tại của người dùng kèm đầy đủ thông tin thẻ người chơi."""
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user_a == current_user.id,
            Friendship.user_b == current_user.id
        )
    ).offset(skip).limit(limit).all()

    friends = []
    for f in friendships:
        friend_id = f.user_b if f.user_a == current_user.id else f.user_a
        friend_user = db.query(User).filter(User.id == friend_id).first()
        if friend_user:
            card_info = _build_player_card_info(db, friend_user, current_user.id)
            friends.append({
                "friendship_id": f.id,
                "friend_id": friend_user.id,
                "username": friend_user.username,
                "email": friend_user.email,
                "created_at": f.created_at,
                **card_info,
            })
    return friends


# ===========================================================================
# Bạn chung (Mutual Friends) & Gợi ý kết bạn (Friend Suggestions)
# ===========================================================================

def get_user_friend_ids(db: Session, user_id: int) -> set[int]:
    """Lấy danh sách ID bạn bè của một người dùng."""
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user_a == user_id,
            Friendship.user_b == user_id,
        )
    ).all()
    friend_ids = set()
    for f in friendships:
        friend_ids.add(f.user_b if f.user_a == user_id else f.user_a)
    return friend_ids


def get_mutual_friends(db: Session, current_user_id: int, target_user_id: int) -> dict:
    """Lấy số lượng và danh sách bạn chung giữa current_user và target_user."""
    if current_user_id == target_user_id:
        user = db.get(User, current_user_id)
        return {
            "target_user_id": current_user_id,
            "target_username": user.username if user else "",
            "mutual_friends_count": 0,
            "mutual_friends": [],
        }

    target_user = db.get(User, target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng mục tiêu không tồn tại trong hệ thống."
        )

    # Lấy tập bạn bè của 2 người
    friends_current = get_user_friend_ids(db, current_user_id)
    friends_target = get_user_friend_ids(db, target_user_id)
    mutual_ids = friends_current.intersection(friends_target)

    mutual_list = []
    if mutual_ids:
        users = db.query(User).filter(User.id.in_(mutual_ids)).all()
        profiles = {}
        try:
            prof_rows = db.query(
                GamerProfile.user_id,
                GamerProfile.display_name,
                GamerProfile.avatar,
            ).filter(GamerProfile.user_id.in_(mutual_ids)).all()
            profiles = {r[0]: {"display_name": r[1], "avatar": r[2]} for r in prof_rows}
        except Exception:
            profiles = {}

        for u in users:
            prof = profiles.get(u.id, {})
            disp = prof.get("display_name") or u.username
            avat = prof.get("avatar")
            mutual_list.append({
                "id": u.id,
                "username": u.username,
                "display_name": disp,
                "avatar": avat,
            })

    return {
        "target_user_id": target_user.id,
        "target_username": target_user.username,
        "mutual_friends_count": len(mutual_ids),
        "mutual_friends": mutual_list,
    }


def get_friend_suggestions(
    db: Session,
    current_user_id: int,
    limit: int = 20,
    q: Optional[str] = None,
) -> dict:
    """Gợi ý kết bạn theo bạn chung, game chung và hỗ trợ tìm kiếm người chơi toàn hệ thống theo từ khóa `q`."""
    # 1. Danh sách bạn bè hiện tại
    try:
        my_friend_ids = get_user_friend_ids(db, current_user_id)
    except Exception:
        db.rollback()
        my_friend_ids = set()

    # 2. Danh sách những người đang có lời mời kết bạn PENDING (cả gửi và nhận)
    pending_ids: set[int] = set()
    try:
        pending_reqs = db.query(FriendRequest).filter(
            and_(
                FriendRequest.status == "PENDING",
                or_(
                    FriendRequest.sender_id == current_user_id,
                    FriendRequest.receiver_id == current_user_id,
                ),
            )
        ).all()
        pending_ids = {
            r.receiver_id if r.sender_id == current_user_id else r.sender_id
            for r in pending_reqs
        }
    except Exception:
        db.rollback()
        pending_ids = set()

    # 3. Danh sách người bị chặn (2 chiều)
    blocked_ids: set[int] = set()
    try:
        blocks = db.query(Block).filter(
            or_(
                Block.blocker_id == current_user_id,
                Block.blocked_id == current_user_id,
            )
        ).all()
        blocked_ids = {
            b.blocked_id if b.blocker_id == current_user_id else b.blocker_id
            for b in blocks
        }
    except Exception:
        db.rollback()
        blocked_ids = set()

    # Tập ID cần loại trừ: Bạn bè đã có, lời mời đang chờ, block và chính mình
    exclude_ids = my_friend_ids | pending_ids | blocked_ids | {current_user_id}

    # 4. Lấy game của người dùng hiện tại
    my_game_ids: set[int] = set()
    try:
        my_user_games = db.query(UserGame).filter(UserGame.user_id == current_user_id).all()
        my_game_ids = {ug.game_id for ug in my_user_games if ug.game_id is not None}
    except Exception:
        db.rollback()
        my_game_ids = set()

    keyword = q.strip() if q else ""
    candidate_ids: set[int] = set()

    if keyword:
        # Tìm kiếm toàn hệ thống theo username, display_name hoặc in_game_id
        try:
            like_pattern = f"%{keyword}%"
            matched_rows = (
                db.query(User.id)
                .outerjoin(GamerProfile, GamerProfile.user_id == User.id)
                .outerjoin(UserGame, UserGame.user_id == User.id)
                .filter(
                    and_(
                        ~User.id.in_(exclude_ids),
                        or_(
                            User.status == "ACTIVE",
                            User.status.is_(None),
                        ),
                        or_(
                            User.username.ilike(like_pattern),
                            GamerProfile.display_name.ilike(like_pattern),
                            UserGame.in_game_id.ilike(like_pattern),
                        ),
                    )
                )
                .distinct()
                .limit(limit)
                .all()
            )
            candidate_ids = {row[0] for row in matched_rows}
        except Exception:
            db.rollback()
            try:
                like_pattern = f"%{keyword}%"
                matched_rows = (
                    db.query(User.id)
                    .filter(
                        and_(
                            ~User.id.in_(exclude_ids),
                            User.username.ilike(like_pattern),
                        )
                    )
                    .limit(limit)
                    .all()
                )
                candidate_ids = {row[0] for row in matched_rows}
            except Exception:
                db.rollback()
                candidate_ids = set()
    else:
        # 5. Tìm các ứng viên có bạn chung (Friends of Friends)
        fof_ids: set[int] = set()
        try:
            for fid in my_friend_ids:
                fof_ids.update(get_user_friend_ids(db, fid))
            fof_ids -= exclude_ids
        except Exception:
            db.rollback()
            fof_ids = set()

        # 6. Tìm các ứng viên có cùng game
        game_peer_ids: set[int] = set()
        if my_game_ids:
            try:
                ug_peers = db.query(UserGame.user_id).filter(
                    and_(
                        UserGame.game_id.in_(my_game_ids),
                        ~UserGame.user_id.in_(exclude_ids),
                    )
                ).all()
                game_peer_ids = {row[0] for row in ug_peers}
            except Exception:
                db.rollback()
                game_peer_ids = set()

        # Tập ứng viên tiềm năng: Ưu tiên người có bạn chung hoặc game chung
        candidate_ids = (fof_ids | game_peer_ids) - exclude_ids

        # Nếu số lượng ít hơn limit, lấy thêm tất cả người dùng khác trong bảng users
        if len(candidate_ids) < limit:
            try:
                other_users = (
                    db.query(User.id)
                    .filter(
                        and_(
                            or_(User.status == "ACTIVE", User.status.is_(None)),
                            ~User.id.in_(exclude_ids | candidate_ids),
                        )
                    )
                    .order_by(User.id.desc())
                    .limit(limit - len(candidate_ids))
                    .all()
                )
                candidate_ids.update(row[0] for row in other_users)
            except Exception:
                db.rollback()
                try:
                    other_users = (
                        db.query(User.id)
                        .filter(~User.id.in_(exclude_ids | candidate_ids))
                        .order_by(User.id.desc())
                        .limit(limit - len(candidate_ids))
                        .all()
                    )
                    candidate_ids.update(row[0] for row in other_users)
                except Exception:
                    db.rollback()

    if not candidate_ids:
        return {"total": 0, "suggestions": []}

    # Lấy thông tin user, profile, game của toàn bộ ứng viên
    try:
        candidates = db.query(User).filter(User.id.in_(candidate_ids)).all()
    except Exception:
        db.rollback()
        return {"total": 0, "suggestions": []}

    profiles = {}
    try:
        prof_rows = db.query(
            GamerProfile.user_id,
            GamerProfile.display_name,
            GamerProfile.avatar,
        ).filter(GamerProfile.user_id.in_(candidate_ids)).all()
        profiles = {r[0]: {"display_name": r[1], "avatar": r[2]} for r in prof_rows}
    except Exception:
        db.rollback()
        profiles = {}

    cand_games_map: dict[int, list[Game]] = {}
    try:
        cand_games_data = (
            db.query(UserGame, Game)
            .join(Game, UserGame.game_id == Game.id)
            .filter(UserGame.user_id.in_(candidate_ids))
            .all()
        )
        for ug, g in cand_games_data:
            cand_games_map.setdefault(ug.user_id, []).append(g)
    except Exception:
        db.rollback()
        cand_games_map = {}

    # Danh sách tên bạn bè hiện tại để làm sample text
    all_my_friends = {}
    if my_friend_ids:
        try:
            all_my_friends = {
                u.id: u.username
                for u in db.query(User).filter(User.id.in_(my_friend_ids)).all()
            }
        except Exception:
            db.rollback()
            all_my_friends = {}

    suggestions = []
    for cand in candidates:
        try:
            cand_friend_ids = get_user_friend_ids(db, cand.id)
            mutual_ids = my_friend_ids.intersection(cand_friend_ids)
            mutual_count = len(mutual_ids)
        except Exception:
            db.rollback()
            mutual_ids = set()
            mutual_count = 0

        # Mẫu tên bạn chung (tối đa 2 người)
        mutual_sample = [all_my_friends[mid] for mid in list(mutual_ids)[:2] if mid in all_my_friends]

        # Game chung
        cand_all_g = cand_games_map.get(cand.id, [])
        shared_g = [g for g in cand_all_g if g.id in my_game_ids]
        shared_games_count = len(shared_g)

        # Điểm trọng số: Mỗi bạn chung = 3 điểm, mỗi game chung = 2 điểm
        score = mutual_count * 3 + shared_games_count * 2

        # Lý do gợi ý
        reasons = []
        if mutual_count > 0:
            reasons.append(f"{mutual_count} bạn chung")
        if shared_games_count > 0:
            game_names = ", ".join([g.name for g in shared_g[:2]])
            reasons.append(f"Cùng chơi {game_names}")
        if not reasons:
            reasons.append("Gợi ý kết bạn")
        reason_str = " • ".join(reasons)

        prof = profiles.get(cand.id, {})
        disp = prof.get("display_name") or cand.username
        avat = prof.get("avatar")
        card_info = _get_real_user_card(db, cand, current_user_id)
        suggestions.append({
            **card_info,
            "user_id": cand.id,
            "username": cand.username,
            "display_name": disp or card_info["display_name"],
            "avatar": avat if avat is not None else card_info["avatar"],
            "mutual_friends_count": mutual_count,
            "mutual_friends_sample": mutual_sample,
            "shared_games": [
                {"id": g.id, "name": g.name, "image": g.image}
                for g in shared_g
            ],
            "shared_games_count": shared_games_count,
            "reason": reason_str,
            "_score": score,
        })

    # Sắp xếp theo score giảm dần, mutual_friends_count giảm dần, shared_games_count giảm dần
    suggestions.sort(
        key=lambda s: (s["_score"], s["mutual_friends_count"], s["shared_games_count"]),
        reverse=True,
    )
    suggestions = suggestions[:limit]

    # Xóa trường `_score` nội bộ
    for s in suggestions:
        s.pop("_score", None)

    return {
        "total": len(suggestions),
        "suggestions": suggestions,
    }


# ===========================================================================
# Chặn & Bỏ chặn bạn bè / người dùng (Block & Unblock)
# ===========================================================================

def block_user(db: Session, current_user: User, target_user_id: int) -> dict:
    """Chặn một người dùng:
    - Tạo bản ghi trong bảng `blocks`.
    - Nếu đang là bạn bè trong `friendships` -> tự động xóa kết bạn.
    - Nếu đang có lời mời kết bạn trong `friend_requests` -> tự động xóa lời mời.
    """
    if current_user.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự chặn chính mình",
        )

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại",
        )

    existing_block = db.query(Block).filter(
        Block.blocker_id == current_user.id,
        Block.blocked_id == target_user_id,
    ).first()
    if existing_block:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bạn đã chặn {target_user.username} trước đó rồi",
        )

    user_a, user_b = sorted((current_user.id, target_user_id))

    try:
        # 1. Nếu hai người đang là bạn bè -> Xóa quan hệ bạn bè
        db.query(Friendship).filter(
            Friendship.user_a == user_a,
            Friendship.user_b == user_b,
        ).delete(synchronize_session=False)

        # 2. Xóa các lời mời kết bạn (cả 2 chiều) giữa hai người
        db.query(FriendRequest).filter(
            or_(
                and_(
                    FriendRequest.sender_id == current_user.id,
                    FriendRequest.receiver_id == target_user_id,
                ),
                and_(
                    FriendRequest.sender_id == target_user_id,
                    FriendRequest.receiver_id == current_user.id,
                ),
            )
        ).delete(synchronize_session=False)

        # 3. Thêm bản ghi chặn vào bảng blocks
        new_block = Block(
            blocker_id=current_user.id,
            blocked_id=target_user_id,
        )
        db.add(new_block)
        db.commit()
        db.refresh(new_block)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Người dùng này đã nằm trong danh sách chặn",
        )
    except Exception:
        db.rollback()
        raise

    return {
        "id": new_block.id,
        "blocker_id": new_block.blocker_id,
        "blocked_id": new_block.blocked_id,
        "blocked_username": target_user.username,
        "created_at": new_block.created_at,
    }


def unblock_user(db: Session, current_user: User, target_user_id: int) -> User:
    """Bỏ chặn một người dùng đã chặn trước đó."""
    if current_user.id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể bỏ chặn chính mình",
        )

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại",
        )

    block_record = db.query(Block).filter(
        Block.blocker_id == current_user.id,
        Block.blocked_id == target_user_id,
    ).first()
    if not block_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bạn chưa chặn {target_user.username}",
        )

    try:
        db.delete(block_record)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return target_user


def get_blocked_users(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """Lấy danh sách những người dùng đang bị current_user chặn."""
    rows = (
        db.query(Block, User)
        .join(User, User.id == Block.blocked_id)
        .filter(Block.blocker_id == current_user.id)
        .order_by(Block.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    blocked_ids = [u.id for _, u in rows]
    profiles = {}
    if blocked_ids:
        try:
            prof_rows = (
                db.query(
                    GamerProfile.user_id,
                    GamerProfile.display_name,
                    GamerProfile.avatar,
                )
                .filter(GamerProfile.user_id.in_(blocked_ids))
                .all()
            )
            profiles = {
                r[0]: {"display_name": r[1], "avatar": r[2]} for r in prof_rows
            }
        except Exception:
            profiles = {}

    result = []
    for block_rec, u in rows:
        prof = profiles.get(u.id, {})
        card_info = _get_real_user_card(db, u, current_user.id)
        result.append({
            **card_info,
            "block_id": block_rec.id,
            "user_id": u.id,
            "username": u.username,
            "display_name": prof.get("display_name") or card_info["display_name"] or u.username,
            "avatar": prof.get("avatar") if prof.get("avatar") is not None else card_info["avatar"],
            "blocked_at": block_rec.created_at,
        })

    return result


