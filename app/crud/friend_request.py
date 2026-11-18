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


def get_friends_list(db: Session, current_user: User, skip: int = 0, limit: int = 50):
    """Lấy danh sách bạn bè hiện tại của người dùng."""
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
            friends.append({
                "friendship_id": f.id,
                "friend_id": friend_user.id,
                "username": friend_user.username,
                "email": friend_user.email,
                "created_at": f.created_at
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


def get_friend_suggestions(db: Session, current_user_id: int, limit: int = 20) -> dict:
    """Gợi ý kết bạn theo bạn chung và game chung."""
    # 1. Danh sách bạn bè hiện tại
    my_friend_ids = get_user_friend_ids(db, current_user_id)

    # 2. Danh sách những người đang có lời mời kết bạn PENDING (cả gửi và nhận)
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

    # 3. Danh sách người bị chặn (2 chiều)
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

    # Tập ID cần loại trừ: Bạn bè đã có, lời mời đang chờ, block và chính mình
    exclude_ids = my_friend_ids | pending_ids | blocked_ids | {current_user_id}

    # 4. Lấy game của người dùng hiện tại
    my_user_games = db.query(UserGame).filter(UserGame.user_id == current_user_id).all()
    my_game_ids = {ug.game_id for ug in my_user_games}

    # 5. Tìm các ứng viên có bạn chung (Friends of Friends)
    fof_ids = set()
    for fid in my_friend_ids:
        fof_ids.update(get_user_friend_ids(db, fid))
    fof_ids -= exclude_ids

    # 6. Tìm các ứng viên có cùng game
    game_peer_ids = set()
    if my_game_ids:
        ug_peers = db.query(UserGame.user_id).filter(
            and_(
                UserGame.game_id.in_(my_game_ids),
                ~UserGame.user_id.in_(exclude_ids),
            )
        ).all()
        game_peer_ids = {row[0] for row in ug_peers}

    # Tập ứng viên tiềm năng: Ưu tiên người có bạn chung hoặc game chung
    candidate_ids = (fof_ids | game_peer_ids) - exclude_ids

    # Nếu số lượng ít hơn limit, lấy thêm các người dùng ACTIVE khác trong hệ thống
    if len(candidate_ids) < limit:
        other_users = db.query(User.id).filter(
            and_(
                User.status == "ACTIVE",
                ~User.id.in_(exclude_ids | candidate_ids),
            )
        ).limit(limit - len(candidate_ids)).all()
        candidate_ids.update(row[0] for row in other_users)

    if not candidate_ids:
        return {"total": 0, "suggestions": []}

    # Lấy thông tin user, profile, game của toàn bộ ứng viên
    candidates = db.query(User).filter(User.id.in_(candidate_ids)).all()
    profiles = {}
    try:
        prof_rows = db.query(
            GamerProfile.user_id,
            GamerProfile.display_name,
            GamerProfile.avatar,
        ).filter(GamerProfile.user_id.in_(candidate_ids)).all()
        profiles = {r[0]: {"display_name": r[1], "avatar": r[2]} for r in prof_rows}
    except Exception:
        profiles = {}
    cand_games_data = (
        db.query(UserGame, Game)
        .join(Game, UserGame.game_id == Game.id)
        .filter(UserGame.user_id.in_(candidate_ids))
        .all()
    )
    cand_games_map: dict[int, list[Game]] = {}
    for ug, g in cand_games_data:
        cand_games_map.setdefault(ug.user_id, []).append(g)

    # Danh sách tên bạn bè hiện tại để làm sample text
    all_my_friends = {
        u.id: u.username
        for u in db.query(User).filter(User.id.in_(my_friend_ids)).all()
    }

    suggestions = []
    for cand in candidates:
        cand_friend_ids = get_user_friend_ids(db, cand.id)
        mutual_ids = my_friend_ids.intersection(cand_friend_ids)
        mutual_count = len(mutual_ids)

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
        suggestions.append({
            "user_id": cand.id,
            "username": cand.username,
            "display_name": disp,
            "avatar": avat,
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

