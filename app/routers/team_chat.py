from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.gamer_profile import GamerProfile
from app.models.team import Team
from app.models.team_chat_message import TeamChatMessage
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.chat import SendMessageRequest

router = APIRouter(prefix="/api/teams", tags=["Team Club Chat"])


def _require_team_member(db: Session, team_id: int, user: User) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    is_member = (
        team.captain_id == user.id
        or db.query(TeamMember.id)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id)
        .first()
        is not None
    )
    if not is_member:
        raise HTTPException(
            status_code=403,
            detail="Chỉ thành viên câu lạc bộ mới được xem và gửi tin nhắn trong phòng chat này",
        )
    return team


def _serialize(message: TeamChatMessage, author: User, profile: GamerProfile | None, viewer_id: int) -> dict:
    return {
        "id": message.id,
        "team_id": message.team_id,
        "sender_id": message.sender_id,
        "sender_name": (profile.display_name if profile and profile.display_name else author.username),
        "sender_username": author.username,
        "avatar": profile.avatar if profile else None,
        "content": message.content,
        "created_at": message.created_at,
        "is_mine": message.sender_id == viewer_id,
    }


@router.get("/{team_id}/chat/messages", summary="Lấy tin nhắn chat câu lạc bộ")
def get_team_chat_messages(
    team_id: int,
    after_id: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_team_member(db, team_id, user)
    query = (
        db.query(TeamChatMessage, User, GamerProfile)
        .join(User, User.id == TeamChatMessage.sender_id)
        .outerjoin(GamerProfile, GamerProfile.user_id == User.id)
        .filter(TeamChatMessage.team_id == team_id)
    )

    if after_id:
        rows = (
            query.filter(TeamChatMessage.id > after_id)
            .order_by(TeamChatMessage.id.asc())
            .limit(limit)
            .all()
        )
    else:
        rows = (
            query.order_by(TeamChatMessage.id.desc())
            .limit(limit)
            .all()
        )[::-1]

    return {
        "data": {
            "team_id": team_id,
            "messages": [_serialize(message, author, profile, user.id) for message, author, profile in rows],
        }
    }


@router.post(
    "/{team_id}/chat/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Gửi tin nhắn vào chat câu lạc bộ",
)
def send_team_chat_message(
    team_id: int,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_team_member(db, team_id, user)
    message = TeamChatMessage(team_id=team_id, sender_id=user.id, content=body.content)
    db.add(message)
    db.commit()
    db.refresh(message)

    profile = db.query(GamerProfile).filter(GamerProfile.user_id == user.id).first()
    return {
        "data": _serialize(message, user, profile, user.id),
        "message": "Đã gửi tin nhắn vào câu lạc bộ",
    }
