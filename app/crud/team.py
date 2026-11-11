from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.game import Game
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate


def create_team(db: Session, data: TeamCreate, current_user: User):
    game = db.query(Game).filter(Game.id == data.main_game_id).first()

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy game"
        )

    duplicate = db.query(Team).filter(Team.name == data.name).first()

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tên đội đã tồn tại"
        )

    team = Team(
        **data.model_dump(),
        captain_id=current_user.id
    )

    db.add(team)
    db.flush()

    captain = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=TeamMemberRole.CAPTAIN
    )

    db.add(captain)
    db.commit()
    db.refresh(team)

    return team


def get_teams(
    db: Session,
    name: str | None = None,
    game_id: int | None = None,
    page: int = 1,
    page_size: int = 10
):
    query = db.query(Team)

    if name:
        query = query.filter(Team.name.ilike(f"%{name}%"))

    if game_id is not None:
        query = query.filter(Team.main_game_id == game_id)

    total = query.count()

    teams = (
        query.order_by(Team.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": teams,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_team_detail(db: Session, team_id: int):
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy đội"
        )

    members = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id)
        .all()
    )

    return {
        "id": team.id,
        "name": team.name,
        "logo": team.logo,
        "main_game_id": team.main_game_id,
        "description": team.description,
        "captain_id": team.captain_id,
        "max_members": team.max_members,
        "join_mode": team.join_mode,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
        "members": members
    }


def update_team(
    db: Session,
    team: Team,
    data: TeamUpdate
):
    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data:
        duplicate = (
            db.query(Team)
            .filter(
                Team.name == update_data["name"],
                Team.id != team.id
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tên đội đã tồn tại"
            )

    if "main_game_id" in update_data:
        game = (
            db.query(Game)
            .filter(Game.id == update_data["main_game_id"])
            .first()
        )

        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy game"
            )

    if "max_members" in update_data:
        member_count = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team.id)
            .count()
        )

        if update_data["max_members"] < member_count:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số thành viên tối đa không được nhỏ hơn số thành viên hiện tại"
            )

    for field, value in update_data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)

    return team
