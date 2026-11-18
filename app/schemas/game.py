from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class GameBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    image: Optional[str] = Field(None, max_length=500)
    genre: str = Field(..., min_length=1, max_length=100)


class GameCreate(GameBase):
    pass


class GameUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    image: Optional[str] = Field(None, max_length=500)
    genre: Optional[str] = Field(None, min_length=1, max_length=100)


class GameResponse(GameBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class GameRankBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rank_name: str
    rank_order: int


class GameRoleBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role_name: str


class GameCatalogResponse(GameResponse):
    ranks: List[GameRankBrief] = Field(default_factory=list)
    roles: List[GameRoleBrief] = Field(default_factory=list)
