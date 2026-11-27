from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.block import Block
from app.models.notification import Notification
from app.models.team import Team
from app.models.team import TeamJoinMode
from app.models.team_invitation import TeamInvitation, InvitationStatus
from app.models.team_join_request import TeamJoinRequest, TeamJoinRequestStatus
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.friendships import Friendship
from app.models.gamer_profile import GamerProfile
from app.models.user import User, UserStatus

router = APIRouter(prefix='/api/team-invitations', tags=['Team invitations'])

class InviteBody(BaseModel):
    team_id: int = Field(gt=0)
    user_id: int = Field(gt=0)

class ResponseBody(BaseModel):
    action: Literal['accept', 'reject']

def blocked(db, a, b):
    return db.query(Block.id).filter(or_(and_(Block.blocker_id == a, Block.blocked_id == b), and_(Block.blocker_id == b, Block.blocked_id == a))).first() is not None

def member_count(db, team):
    members = db.query(TeamMember).filter(TeamMember.team_id == team.id)
    return members.count() + (0 if members.filter(TeamMember.user_id == team.captain_id).first() else 1)

def as_dict(invitation, team, inviter):
    return {'id': invitation.id, 'team_id': team.id, 'team_name': team.name, 'join_mode': team.join_mode.value, 'inviter_id': inviter.id, 'inviter_name': inviter.username, 'status': invitation.status.value, 'created_at': invitation.created_at}

def require_team_member(db, team, user):
    if team.captain_id == user.id:
        return
    if not db.query(TeamMember.id).filter_by(team_id=team.id, user_id=user.id).first():
        raise HTTPException(403, 'Chỉ thành viên câu lạc bộ mới có thể mời bạn bè')

@router.get('/captain-teams')
def captain_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    teams = db.query(Team).filter(Team.captain_id == user.id).order_by(Team.name).all()
    return {'data': [{'id': team.id, 'name': team.name} for team in teams]}

@router.get('/available-friends')
def available_friends(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team: raise HTTPException(404, 'Không tìm thấy câu lạc bộ')
    require_team_member(db, team, user)
    friendships = db.query(Friendship).filter(or_(Friendship.user_a == user.id, Friendship.user_b == user.id)).all()
    friend_ids = [f.user_b if f.user_a == user.id else f.user_a for f in friendships]
    if not friend_ids: return {'data': []}
    users = (db.query(User, GamerProfile.avatar)
             .outerjoin(GamerProfile, GamerProfile.user_id == User.id)
             .filter(User.id.in_(friend_ids), User.status == UserStatus.ACTIVE)
             .order_by(User.username).all())
    pending_invites = {row.invitee_id for row in db.query(TeamInvitation.invitee_id).filter_by(team_id=team_id, status=InvitationStatus.PENDING).all()}
    members = {row.user_id for row in db.query(TeamMember.user_id).filter_by(team_id=team_id).all()}
    available = []
    for friend, avatar in users:
        if friend.id in members or friend.id in pending_invites or blocked(db, user.id, friend.id):
            continue
        available.append({'user_id': friend.id, 'username': friend.username, 'avatar': avatar})
    return {'data': available}

@router.post('', status_code=status.HTTP_201_CREATED)
def invite(body: InviteBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        team = db.query(Team).filter(Team.id == body.team_id).with_for_update().first()
        if not team: raise HTTPException(404, 'Không tìm thấy đội')
        require_team_member(db, team, user)
        target = db.query(User).filter(User.id == body.user_id, User.status == UserStatus.ACTIVE).first()
        if not target: raise HTTPException(404, 'Không tìm thấy game thủ')
        low_id, high_id = sorted((user.id, target.id))
        if not db.query(Friendship.id).filter_by(user_a=low_id, user_b=high_id).first():
            raise HTTPException(403, 'Bạn chỉ có thể mời người trong danh sách bạn bè của mình')
        if target.id == user.id or db.query(TeamMember.id).filter_by(team_id=team.id, user_id=target.id).first(): raise HTTPException(409, 'Game thủ đã là thành viên của đội')
        if blocked(db, user.id, target.id): raise HTTPException(403, 'Không thể gửi lời mời tới người dùng này')
        if member_count(db, team) >= team.max_members: raise HTTPException(409, 'Đội đã đủ thành viên')
        existing = db.query(TeamInvitation).filter_by(team_id=team.id, invitee_id=target.id).with_for_update().first()
        if existing and existing.status == InvitationStatus.PENDING: raise HTTPException(409, 'Lời mời đang chờ phản hồi')
        if existing:
            existing.status = InvitationStatus.PENDING
            existing.inviter_id = user.id
            invitation = existing
        else:
            invitation = TeamInvitation(team_id=team.id, inviter_id=user.id, invitee_id=target.id)
            db.add(invitation)
        db.add(Notification(recipient_id=target.id, type='TEAM_INVITATION', content=f'{user.username} mời bạn vào đội {team.name}', link='/pages/team-invitations.html'))
        db.commit(); db.refresh(invitation)
        return {'message': 'Đã gửi lời mời', 'data': as_dict(invitation, team, user)}
    except IntegrityError:
        db.rollback(); raise HTTPException(409, 'Lời mời đã tồn tại')

@router.get('/me')
def my_invitations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (db.query(TeamInvitation, Team, User).join(Team, Team.id == TeamInvitation.team_id).join(User, User.id == TeamInvitation.inviter_id).filter(TeamInvitation.invitee_id == user.id, TeamInvitation.status == InvitationStatus.PENDING).order_by(TeamInvitation.updated_at.desc(), TeamInvitation.id.desc()).all())
    return {'data': [as_dict(invitation, team, inviter) for invitation, team, inviter in rows]}

@router.patch('/{invitation_id}')
def respond(invitation_id: int, body: ResponseBody, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        # Lock the team before the invitation, matching the order used when inviting.
        existing = db.query(TeamInvitation).filter(TeamInvitation.id == invitation_id).first()
        if not existing: raise HTTPException(404, 'Không tìm thấy lời mời')
        team = db.query(Team).filter(Team.id == existing.team_id).with_for_update().first()
        invitation = db.query(TeamInvitation).filter_by(id=invitation_id).populate_existing().with_for_update().first()
        if not team or not invitation: raise HTTPException(404, 'Không tìm thấy lời mời')
        if invitation.invitee_id != user.id: raise HTTPException(403, 'Bạn không có quyền phản hồi lời mời này')
        if invitation.status != InvitationStatus.PENDING: raise HTTPException(409, 'Lời mời đã được xử lý')
        if body.action == 'accept':
            if blocked(db, invitation.inviter_id, user.id): raise HTTPException(403, 'Không thể chấp nhận lời mời này')
            if team.captain_id == user.id or db.query(TeamMember.id).filter_by(team_id=team.id, user_id=user.id).first(): raise HTTPException(409, 'Bạn đã là thành viên của đội')
            if member_count(db, team) >= team.max_members: raise HTTPException(409, 'Đội đã đủ thành viên')
            join_request = db.query(TeamJoinRequest).filter_by(team_id=team.id, user_id=user.id).with_for_update().first()
            if team.join_mode == TeamJoinMode.APPROVAL_REQUIRED:
                if join_request:
                    join_request.status = TeamJoinRequestStatus.PENDING
                    join_request.message = 'Chấp nhận lời mời tham gia câu lạc bộ'
                else:
                    join_request = TeamJoinRequest(team_id=team.id, user_id=user.id, message='Chấp nhận lời mời tham gia câu lạc bộ', status=TeamJoinRequestStatus.PENDING)
                    db.add(join_request)
                db.add(Notification(recipient_id=team.captain_id, type='TEAM_JOIN_REQUEST', content=f'{user.username} đã nhận lời mời và đang chờ bạn duyệt tham gia câu lạc bộ {team.name}.', link=f'/pages/team-feed.html?id={team.id}'))
                response_message = 'Đã nhận lời mời. Yêu cầu tham gia đang chờ đội trưởng phê duyệt.'
            else:
                db.add(TeamMember(team_id=team.id, user_id=user.id, role=TeamMemberRole.MEMBER))
                if join_request and join_request.status == TeamJoinRequestStatus.PENDING:
                    join_request.status = TeamJoinRequestStatus.ACCEPTED
                response_message = 'Đã tham gia câu lạc bộ thành công.'
            invitation.status = InvitationStatus.ACCEPTED
        else:
            invitation.status = InvitationStatus.REJECTED
        if body.action == 'reject':
            response_message = 'Đã từ chối lời mời.'
        db.add(Notification(recipient_id=invitation.inviter_id, type='TEAM_INVITATION_RESPONSE', content=f'{user.username} đã {"chấp nhận" if body.action == "accept" else "từ chối"} lời mời vào đội {team.name}', link=f'/pages/team-detail.html?id={team.id}'))
        db.commit()
        return {'message': response_message, 'data': {'id': invitation.id, 'status': invitation.status.value, 'join_status': 'PENDING' if body.action == 'accept' and team.join_mode == TeamJoinMode.APPROVAL_REQUIRED else ('JOINED' if body.action == 'accept' else 'REJECTED')}}
    except IntegrityError:
        db.rollback(); raise HTTPException(409, 'Không thể thêm thành viên hoặc lời mời đã được xử lý')
