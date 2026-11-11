
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.team import TeamJoinMode
from app.models.team_member import TeamMemberRole


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    logo: str | None = None
    main_game_id: int
    description: str | None = None
    max_members: int = Field(ge=1)
    join_mode: TeamJoinMode = TeamJoinMode.APPROVAL_REQUIRED


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    logo: str | None = None
    main_game_id: int | None = None
    description: str | None = None
    max_members: int | None = Field(default=None, ge=1)
    join_mode: TeamJoinMode | None = None


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: TeamMemberRole
    joined_at: datetime


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    logo: str | None
    main_game_id: int
    description: str | None
    captain_id: int
    max_members: int
    join_mode: TeamJoinMode
    created_at: datetime
    updated_at: datetime


class TeamDetailOut(TeamOut):
    members: list[TeamMemberOut] = []


class TeamListOut(BaseModel):
    items: list[TeamOut]
    total: int
    page: int
    page_size: int
    total_pages: int
