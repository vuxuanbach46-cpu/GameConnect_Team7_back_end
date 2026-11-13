
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


class FriendRequestListResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime
    user: FriendRequestUserInfo


# ---------------------------------------------------------------------------
# Schemas cho Bạn chung (Mutual Friends) & Gợi ý kết bạn (Friend Suggestions)
# ---------------------------------------------------------------------------

class MutualFriendItem(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    avatar: str | None = None


class MutualFriendsResponse(BaseModel):
    target_user_id: int
    target_username: str
    mutual_friends_count: int
    mutual_friends: list[MutualFriendItem] = []


class SharedGameItem(BaseModel):
    id: int
    name: str
    image: str | None = None


class FriendSuggestionItem(BaseModel):
    user_id: int
    username: str
    display_name: str | None = None
    avatar: str | None = None
    mutual_friends_count: int = 0
    mutual_friends_sample: list[str] = []
    shared_games: list[SharedGameItem] = []
    shared_games_count: int = 0
    reason: str


class FriendSuggestionsResponse(BaseModel):
    total: int
    suggestions: list[FriendSuggestionItem] = []

