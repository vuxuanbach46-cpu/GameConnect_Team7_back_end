"""Router & CRUD cho tính năng [Bonus] Chat 1-1 giữa bạn bè (REST API + WebSocket)."""

from datetime import datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, get_current_user
from app.db.session import SessionLocal, get_db
from app.models.block import Block
from app.models.direct_message import DirectMessage
from app.models.friendships import Friendship
from app.models.gamer_profile import GamerProfile
from app.models.notification import Notification
from app.models.user import User
from app.schemas.api_response import api_repoint
from app.schemas.chat import SendMessageRequest

router = APIRouter(prefix="/chat", tags=["Direct Chat 1-1"])
ws_router = APIRouter(tags=["Direct Chat 1-1"])


# ===========================================================================
# WebSocket Connection Manager
# ===========================================================================

class ChatConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        conns = self.active_connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns and user_id in self.active_connections:
            self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, payload: dict) -> None:
        conns = list(self.active_connections.get(user_id, []))
        dead_conns: list[WebSocket] = []
        encoded = jsonable_encoder(payload)
        for ws in conns:
            try:
                await ws.send_json(encoded)
            except Exception:
                dead_conns.append(ws)
        for ws in dead_conns:
            self.disconnect(user_id, ws)

    async def broadcast_message(self, msg_dict: dict) -> None:
        sender_id = int(msg_dict["sender_id"])
        receiver_id = int(msg_dict["receiver_id"])

        receiver_msg = {**msg_dict, "is_mine": False}
        sender_msg = {**msg_dict, "is_mine": True}

        await self.send_to_user(
            receiver_id,
            {"event": "new_message", "data": receiver_msg},
        )
        if sender_id != receiver_id:
            await self.send_to_user(
                sender_id,
                {"event": "new_message", "data": sender_msg},
            )


ws_manager = ChatConnectionManager()


# ===========================================================================
# Helpers kiểm tra quyền nhắn tin (Bạn bè & Không chặn)
# ===========================================================================

def _verify_can_chat(db: Session, current_user_id: int, friend_id: int) -> User:
    if current_user_id == friend_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự nhắn tin cho chính mình",
        )

    friend = db.query(User).filter(User.id == friend_id).first()
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại",
        )

    # Kiểm tra chặn 2 chiều
    blocked = (
        db.query(Block)
        .filter(
            or_(
                and_(Block.blocker_id == current_user_id, Block.blocked_id == friend_id),
                and_(Block.blocker_id == friend_id, Block.blocked_id == current_user_id),
            )
        )
        .first()
    )
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không thể nhắn tin vì một trong hai người đã chặn người còn lại",
        )

    # Kiểm tra quan hệ bạn bè trong bảng friendships
    user_a, user_b = sorted((current_user_id, friend_id))
    friendship = (
        db.query(Friendship)
        .filter(
            or_(
                and_(Friendship.user_a == user_a, Friendship.user_b == user_b),
                and_(Friendship.user_a == user_b, Friendship.user_b == user_a),
            )
        )
        .first()
    )
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ có thể nhắn tin với người trong danh sách bạn bè",
        )

    return friend


def _serialize_message(msg: DirectMessage, current_user_id: int) -> dict:
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "receiver_id": msg.receiver_id,
        "content": msg.content,
        "is_read": bool(msg.is_read),
        "created_at": msg.created_at,
        "is_mine": msg.sender_id == current_user_id,
    }


def _upsert_chat_notification(
    db: Session, sender_id: int, receiver_id: int, content: str
) -> None:
    """Tạo hoặc cập nhật thông báo NEW_MESSAGE cho người nhận (gộp theo từng người gửi để tránh spam)."""
    try:
        sender_display_name = None
        try:
            prof_row = (
                db.query(GamerProfile.display_name)
                .filter(GamerProfile.user_id == sender_id)
                .first()
            )
            if prof_row and prof_row[0]:
                sender_display_name = prof_row[0]
        except Exception:
            pass

        if not sender_display_name:
            sender_user = db.query(User.username).filter(User.id == sender_id).first()
            sender_display_name = (
                sender_user[0] if sender_user and sender_user[0] else f"User#{sender_id}"
            )

        unread_count = (
            db.query(func.count(DirectMessage.id))
            .filter(
                and_(
                    DirectMessage.sender_id == sender_id,
                    DirectMessage.receiver_id == receiver_id,
                    DirectMessage.is_read.is_(False),
                )
            )
            .scalar()
            or 1
        )

        clean_preview = " ".join((content or "").split())
        if len(clean_preview) > 60:
            clean_preview = clean_preview[:57] + "..."

        notif_link = f"/chat/{sender_id}"
        msg_text = (
            f'{sender_display_name} đã gửi {unread_count} tin nhắn mới: "{clean_preview}"'
            if unread_count > 1
            else f'{sender_display_name} đã nhắn: "{clean_preview}"'
        )

        existing = (
            db.query(Notification)
            .filter(
                and_(
                    Notification.recipient_id == receiver_id,
                    Notification.type == "NEW_MESSAGE",
                    Notification.link == notif_link,
                    Notification.is_read.is_(False),
                )
            )
            .order_by(Notification.id.desc())
            .first()
        )
        if existing:
            existing.content = msg_text[:500]
            existing.created_at = datetime.now()
        else:
            db.add(
                Notification(
                    recipient_id=receiver_id,
                    type="NEW_MESSAGE",
                    content=msg_text[:500],
                    link=notif_link,
                    is_read=False,
                )
            )
        db.commit()
    except Exception:
        db.rollback()


def _mark_chat_notifications_read(
    db: Session, current_user_id: int, friend_id: int
) -> None:
    """Đánh dấu thông báo NEW_MESSAGE từ friend_id sang current_user_id là đã đọc."""
    try:
        db.query(Notification).filter(
            and_(
                Notification.recipient_id == current_user_id,
                Notification.type == "NEW_MESSAGE",
                Notification.link == f"/chat/{friend_id}",
                Notification.is_read.is_(False),
            )
        ).update({Notification.is_read: True}, synchronize_session=False)
    except Exception:
        pass


# ===========================================================================
# REST API Endpoints
# ===========================================================================

@router.post(
    "/messages/{friend_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Gửi tin nhắn 1-1 cho bạn bè",
)
async def send_direct_message(
    friend_id: int,
    data: SendMessageRequest,
    req: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gửi tin nhắn 1-1 cho một người bạn (chỉ cho phép khi đã là bạn bè và không chặn nhau)."""
    _verify_can_chat(db, current_user.id, friend_id)

    new_msg = DirectMessage(
        sender_id=current_user.id,
        receiver_id=friend_id,
        content=data.content,
        is_read=False,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    _upsert_chat_notification(db, current_user.id, friend_id, data.content)

    msg_dict = _serialize_message(new_msg, current_user.id)
    await ws_manager.broadcast_message(msg_dict)

    response.status_code = status.HTTP_201_CREATED
    return api_repoint(
        req=req,
        status_code=status.HTTP_201_CREATED,
        message="Gửi tin nhắn thành công",
        data=msg_dict,
    )


@router.get(
    "/messages/{friend_id}",
    summary="Lấy lịch sử tin nhắn 1-1 với bạn bè (Hỗ trợ polling 3s qua after_id)",
)
def get_direct_messages(
    friend_id: int,
    req: Request,
    limit: int = Query(default=50, ge=1, le=200, description="Số tin nhắn tối đa"),
    after_id: int | None = Query(
        default=None,
        description="Chỉ lấy các tin nhắn mới có id > after_id (dùng cho polling định kỳ 3 giây)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy lịch sử tin nhắn 1-1 giữa người dùng hiện tại và `friend_id`, tự động đánh dấu đã đọc."""
    _verify_can_chat(db, current_user.id, friend_id)

    # Tự động đánh dấu các tin nhắn do friend_id gửi cho current_user và thông báo NEW_MESSAGE là đã đọc
    try:
        db.query(DirectMessage).filter(
            and_(
                DirectMessage.sender_id == friend_id,
                DirectMessage.receiver_id == current_user.id,
                DirectMessage.is_read.is_(False),
            )
        ).update({DirectMessage.is_read: True}, synchronize_session=False)
        _mark_chat_notifications_read(db, current_user.id, friend_id)
        db.commit()
    except Exception:
        db.rollback()

    base_filter = or_(
        and_(
            DirectMessage.sender_id == current_user.id,
            DirectMessage.receiver_id == friend_id,
        ),
        and_(
            DirectMessage.sender_id == friend_id,
            DirectMessage.receiver_id == current_user.id,
        ),
    )

    if after_id is not None and after_id > 0:
        messages = (
            db.query(DirectMessage)
            .filter(and_(base_filter, DirectMessage.id > after_id))
            .order_by(DirectMessage.id.asc())
            .limit(limit)
            .all()
        )
    else:
        recent_messages = (
            db.query(DirectMessage)
            .filter(base_filter)
            .order_by(DirectMessage.id.desc())
            .limit(limit)
            .all()
        )
        messages = list(reversed(recent_messages))

    data = [_serialize_message(m, current_user.id) for m in messages]
    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy lịch sử tin nhắn thành công",
        data=data,
    )


@router.get(
    "/unread-counts",
    summary="Lấy tổng số tin nhắn chưa đọc và số tin chưa đọc theo từng người bạn",
)
def get_unread_message_counts(
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trả về tổng số tin nhắn chưa đọc, map by_friend và danh sách senders kèm avatar/tin nhắn cuối."""
    rows = (
        db.query(
            DirectMessage.sender_id,
            func.count(DirectMessage.id),
            func.max(DirectMessage.id),
        )
        .filter(
            and_(
                DirectMessage.receiver_id == current_user.id,
                DirectMessage.is_read.is_(False),
            )
        )
        .group_by(DirectMessage.sender_id)
        .order_by(func.max(DirectMessage.id).desc())
        .all()
    )

    by_friend = {str(sender_id): int(cnt) for sender_id, cnt, _ in rows if cnt > 0}
    total_unread = sum(by_friend.values())

    senders: list[dict] = []
    if rows:
        sender_ids = [int(sender_id) for sender_id, cnt, _ in rows if cnt > 0]
        max_ids = [int(max_id) for _, cnt, max_id in rows if cnt > 0 and max_id]

        last_msgs_map: dict[int, DirectMessage] = {}
        if max_ids:
            last_msgs = (
                db.query(DirectMessage)
                .filter(DirectMessage.id.in_(max_ids))
                .all()
            )
            last_msgs_map = {int(m.id): m for m in last_msgs}

        users_map: dict[int, User] = {}
        if sender_ids:
            users = db.query(User).filter(User.id.in_(sender_ids)).all()
            users_map = {int(u.id): u for u in users}

        profiles_map: dict[int, tuple[str | None, str | None]] = {}
        if sender_ids:
            try:
                prof_rows = (
                    db.query(
                        GamerProfile.user_id,
                        GamerProfile.display_name,
                        GamerProfile.avatar,
                    )
                    .filter(GamerProfile.user_id.in_(sender_ids))
                    .all()
                )
                profiles_map = {int(r[0]): (r[1], r[2]) for r in prof_rows}
            except Exception:
                profiles_map = {}

        for sender_id, cnt, max_id in rows:
            if cnt <= 0:
                continue
            sid = int(sender_id)
            user_obj = users_map.get(sid)
            prof_disp, prof_avatar = profiles_map.get(sid, (None, None))
            username = user_obj.username if user_obj else f"User#{sid}"
            display_name = prof_disp or username
            last_msg = last_msgs_map.get(int(max_id)) if max_id else None

            senders.append({
                "user_id": sid,
                "username": username,
                "display_name": display_name,
                "avatar": prof_avatar,
                "unread_count": int(cnt),
                "last_message": last_msg.content if last_msg else "",
                "last_message_at": last_msg.created_at if last_msg else None,
            })

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Lấy số tin nhắn chưa đọc thành công",
        data={
            "total_unread": total_unread,
            "by_friend": by_friend,
            "senders": senders,
        },
    )


@router.patch(
    "/messages/{friend_id}/read",
    summary="Đánh dấu toàn bộ tin nhắn từ friend_id là đã đọc",
)
@router.post(
    "/messages/{friend_id}/read",
    summary="Đánh dấu toàn bộ tin nhắn từ friend_id là đã đọc (Alias)",
    include_in_schema=False,
)
def mark_friend_messages_read(
    friend_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật `is_read = True` cho toàn bộ tin nhắn mà `friend_id` gửi cho `current_user`."""
    updated_count = (
        db.query(DirectMessage)
        .filter(
            and_(
                DirectMessage.sender_id == friend_id,
                DirectMessage.receiver_id == current_user.id,
                DirectMessage.is_read.is_(False),
            )
        )
        .update({DirectMessage.is_read: True}, synchronize_session=False)
    )
    _mark_chat_notifications_read(db, current_user.id, friend_id)
    db.commit()

    return api_repoint(
        req=req,
        status_code=status.HTTP_200_OK,
        message="Đã đánh dấu tin nhắn là đã đọc",
        data={
            "friend_id": friend_id,
            "updated_count": updated_count,
        },
    )


# ===========================================================================
# FastAPI WebSocket Endpoint (/ws/chat/{token} & /chat/ws/{token})
# ===========================================================================

@ws_router.websocket("/ws/chat/{token}")
@router.websocket("/ws/{token}")
async def websocket_direct_chat(websocket: WebSocket, token: str):
    try:
        user_id = decode_access_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            if not isinstance(payload, dict):
                continue

            if payload.get("type") == "ping":
                await websocket.send_json({"event": "pong"})
                continue

            receiver_id = payload.get("receiver_id") or payload.get("friend_id")
            content = (payload.get("content") or "").strip()
            if not receiver_id or not content:
                continue

            db = SessionLocal()
            try:
                _verify_can_chat(db, user_id, int(receiver_id))
                new_msg = DirectMessage(
                    sender_id=user_id,
                    receiver_id=int(receiver_id),
                    content=content[:2000],
                    is_read=False,
                )
                db.add(new_msg)
                db.commit()
                db.refresh(new_msg)
                msg_dict = _serialize_message(new_msg, user_id)
                _upsert_chat_notification(db, user_id, int(receiver_id), content[:2000])
            except Exception as err:
                db.rollback()
                detail = getattr(err, "detail", "Không thể gửi tin nhắn")
                await websocket.send_json({"event": "error", "error": detail})
                continue
            finally:
                db.close()

            await ws_manager.broadcast_message(msg_dict)
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
    except Exception:
        ws_manager.disconnect(user_id, websocket)
