from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GameRankCreate(BaseModel):
    rank_name: str = Field(..., min_length=1, max_length=100)
    rank_order: int = Field(0, ge=0)


class GameRankUpdate(BaseModel):
    rank_name: Optional[str] = Field(None, min_length=1, max_length=100)
    rank_order: Optional[int] = Field(None, ge=0)


class GameRankResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    game_id: int
    rank_name: str
    rank_order: int
    created_at: datetime
