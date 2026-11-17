from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class TeamJoinModeSchema(str, Enum):
    PUBLIC = "PUBLIC"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class TeamMemberRoleSchema(str, Enum):
    CAPTAIN = "CAPTAIN"
    MEMBER = "MEMBER"


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    logo_url: Optional[str] = Field(default=None, max_length=500)

    main_game_id: int

    description: Optional[str] = None

    max_members: int = Field(default=5, ge=2, le=100)

    join_mode: TeamJoinModeSchema = TeamJoinModeSchema.PUBLIC


class TeamUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)

    logo_url: Optional[str] = Field(default=None, max_length=500)

    main_game_id: Optional[int] = None

    description: Optional[str] = None

    max_members: Optional[int] = Field(default=None, ge=2, le=100)

    join_mode: Optional[TeamJoinModeSchema] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    logo_url: Optional[str]
    main_game_id: int
    description: Optional[str]
    captain_id: int
    max_members: int
    join_mode: TeamJoinModeSchema
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
    user_id: int
    username: str
    role: TeamMemberRoleSchema
    joined_at: datetime


class TeamDetailResponse(BaseModel):
    id: int
    name: str
    logo_url: Optional[str]
    main_game_id: int
    description: Optional[str]
    captain_id: int
    max_members: int
    join_mode: TeamJoinModeSchema
    total_members: int
    members: list[TeamMemberResponse]

    created_at: datetime
    updated_at: datetime


class TeamListResponse(BaseModel):
    items: list[TeamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JoinRequestStatusAction(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ReviewJoinRequest(BaseModel):
    status: JoinRequestStatusAction = Field(
        ...,
        description="Trạng thái duyệt đơn: ACCEPTED hoặc REJECTED",
    )


class TransferCaptainRequest(BaseModel):
    new_captain_id: int = Field(
        ...,
        gt=0,
        description="ID người dùng mới sẽ trở thành đội trưởng",
    )
