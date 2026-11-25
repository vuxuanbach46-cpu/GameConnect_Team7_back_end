from datetime import date, time
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_feed_post import TeamFeedPost
from app.models.user import User

router = APIRouter(prefix='/api/teams', tags=['Team feed'])

class FeedPostCreate(BaseModel):
    type: Literal['announcement', 'schedule']
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=5000)
    play_date: date | None = None
    play_time: time | None = None

    @model_validator(mode='after')
    def validate_content(self):
        self.title = self.title.strip()
        self.content = self.content.strip()
        if not self.title or not self.content: raise ValueError('Vui lòng nhập tiêu đề và nội dung')
        if self.type == 'schedule' and (not self.play_date or not self.play_time): raise ValueError('Vui lòng nhập ngày và giờ chơi')
        return self

def check_access(db, team_id, user, captain=False):
    team = db.query(Team).filter_by(id=team_id).first()
    if not team: raise HTTPException(404, 'Không tìm thấy đội')
    is_captain = team.captain_id == user.id
    if captain and not is_captain: raise HTTPException(403, 'Chỉ đội trưởng mới được đăng bài')
    if not is_captain and not db.query(TeamMember.id).filter_by(team_id=team_id, user_id=user.id).first():
        raise HTTPException(403, 'Chỉ thành viên mới được xem bảng tin')
    return team, is_captain

def serialize(post, author):
    return {'id':post.id, 'teamId':post.team_id, 'type':post.type, 'title':post.title,
            'content':post.content, 'author':author.username, 'createdAt':post.created_at,
            'playDate':post.play_date, 'playTime':post.play_time}

@router.get('/{team_id}/feed')
def get_feed(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team, is_captain = check_access(db, team_id, user)
    rows = db.query(TeamFeedPost, User).join(User, User.id == TeamFeedPost.author_id).filter(TeamFeedPost.team_id == team_id).order_by(TeamFeedPost.created_at.desc(), TeamFeedPost.id.desc()).all()
    return {'data': {'team': {'id':team.id,'name':team.name,'role':'captain' if is_captain else 'member'}, 'posts':[serialize(post, author) for post, author in rows]}}

@router.post('/{team_id}/feed', status_code=201)
def create_feed_post(team_id: int, body: FeedPostCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_access(db, team_id, user, captain=True)
    post = TeamFeedPost(team_id=team_id, author_id=user.id, type=body.type, title=body.title, content=body.content,
                        play_date=body.play_date.isoformat() if body.type == 'schedule' else None,
                        play_time=body.play_time.strftime('%H:%M') if body.type == 'schedule' else None)
    db.add(post); db.commit(); db.refresh(post)
    return {'data':serialize(post, user)}
