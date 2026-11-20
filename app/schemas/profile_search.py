from typing import Optional
from pydantic import BaseModel, Field


class ProfileSearchRank(BaseModel):
    id: int
    rank_name: str
    rank_order: int


class ProfileSearchRole(BaseModel):
    id: int
    role_name: str


class ProfileSearchGame(BaseModel):
    id: int
    name: str
    image: Optional[str] = None
    genre: str
    rank: Optional[ProfileSearchRank] = None
    role: Optional[ProfileSearchRole] = None
    in_game_id: Optional[str] = None


class GamerProfileSearchItem(BaseModel):
    id: int
    user_id: int
    username: str
    display_name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    region: Optional[str] = None
    play_time: Optional[str] = None
    has_mic: bool
    games: list[ProfileSearchGame] = Field(default_factory=list)


class GamerProfileSearchPagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class GamerProfileSearchResponse(BaseModel):
    items: list[GamerProfileSearchItem]
    pagination: GamerProfileSearchPagination
