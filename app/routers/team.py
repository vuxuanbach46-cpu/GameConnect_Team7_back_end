from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.team import Team
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamOut,
    TeamDetailOut,
    TeamListOut
)
from app.crud import team as team_crud


router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return team_crud.create_team(db, data, current_user)


@router.get("", response_model=TeamListOut)
def get_teams(
    name: str | None = Query(default=None, description="Tìm theo tên đội"),
    game_id: int | None = Query(default=None, description="Lọc theo game"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return team_crud.get_teams(
        db,
        name=name,
        game_id=game_id,
        page=page,
        page_size=page_size
    )


@router.get("/{team_id}", response_model=TeamDetailOut)
def get_team_detail(
    team_id: int,
    db: Session = Depends(get_db)
):
    return team_crud.get_team_detail(db, team_id)


@router.put("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: int,
    data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đội"
        )

    if team.captain_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ đội trưởng mới có quyền sửa thông tin đội"
        )

    return team_crud.update_team(db, team, data)
