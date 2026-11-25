from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user_game import UserGameResponse


class GamerProfileCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    bio: Optional[str] = None
    region: Optional[str] = Field(None, max_length=100)
    play_time: Optional[str] = Field(None, max_length=100)
    has_mic: bool = False
    is_public: bool = False


class GamerProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = None
    region: Optional[str] = Field(None, max_length=100)
    play_time: Optional[str] = Field(None, max_length=100)
    has_mic: Optional[bool] = None
    is_public: Optional[bool] = None


class GamerProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    display_name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    region: Optional[str] = None
    play_time: Optional[str] = None
    has_mic: bool
    is_public: bool = False
    created_at: datetime
    updated_at: datetime


class PublicTeamBrief(BaseModel):
    id: int
    name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    game_id: int
    game_name: str
    game_image: Optional[str] = None
    captain_id: int
    is_captain: bool = False
    member_role: str
    member_count: int
    max_members: int
    join_mode: str
    joined_at: datetime


class PublicGamerProfileResponse(BaseModel):
    id: int
    user_id: int
    username: str
    display_name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    region: Optional[str] = None
    play_time: Optional[str] = None
    has_mic: bool
    is_public: bool = True
    friend_status: str = "NONE"
    user_games: list[UserGameResponse] = Field(default_factory=list)
    teams: list[PublicTeamBrief] = Field(default_factory=list)
