
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class FriendRequestCreate(BaseModel):
    receiver_id: int


class FriendRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime


class FriendRequestUserInfo(BaseModel):
    id: int
    username: str
    email: str


class FriendRequestListResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime
    user: FriendRequestUserInfo
