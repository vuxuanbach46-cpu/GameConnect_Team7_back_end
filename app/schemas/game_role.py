from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class GameRoleCreate(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=100)


class GameRoleUpdate(BaseModel):
    role_name: Optional[str] = Field(None, min_length=1, max_length=100)


class GameRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    game_id: int
    role_name: str
    created_at: datetime
