from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.game import GameResponse, GameRankBrief, GameRoleBrief


class UserGameCreate(BaseModel):
    game_id: int = Field(..., gt=0)
    rank_id: Optional[int] = Field(None, gt=0)
    role_id: Optional[int] = Field(None, gt=0)
    in_game_id: Optional[str] = Field(None, max_length=150)


class UserGameUpdate(BaseModel):
    rank_id: Optional[int] = Field(None, gt=0)
    role_id: Optional[int] = Field(None, gt=0)
    in_game_id: Optional[str] = Field(None, max_length=150)


class UserGameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    game_id: int
    rank_id: Optional[int] = None
    role_id: Optional[int] = None
    in_game_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    game: GameResponse
    rank: Optional[GameRankBrief] = None
    role: Optional[GameRoleBrief] = None
