
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class GamerProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(
        None, min_length=1, max_length=100
    )
    bio: Optional[str] = None
    region: Optional[str] = Field(
        None, max_length=100
    )
    play_time: Optional[str] = Field(
        None, max_length=100
    )
    has_mic: Optional[bool] = None


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
    created_at: datetime
    updated_at: datetime


class PublicGamerProfileResponse(BaseModel):
    id: int
    username: str
    display_name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    region: Optional[str] = None
    play_time: Optional[str] = None
    has_mic: bool
