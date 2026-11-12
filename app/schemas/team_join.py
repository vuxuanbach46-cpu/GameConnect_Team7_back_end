from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class JoinTeamRequest(BaseModel):
    message: Optional[str] = Field(default=None, max_length=1000)


class JoinTeamResponse(BaseModel):
    message: str
    status: str
    request_id: Optional[int] = None


class MyJoinRequestResponse(BaseModel):
    exists: bool
    request_id: Optional[int] = None
    team_id: Optional[int] = None
    status: Optional[str] = None
    message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
