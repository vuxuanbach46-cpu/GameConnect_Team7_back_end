"""Schemas Pydantic cho Auto Matchmaking (Tối ưu cho Web GameConnect)."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.matchmaking import RoomStatus


class RoomMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    is_host: bool = False
    joined_at: datetime


class CreateLobbyRequest(BaseModel):
    """Tạo sảnh đội (Lobby) để chuẩn bị mời bạn bè hoặc tìm trận."""
    game_id: int = Field(default=1, examples=[1], description="ID Game muốn chơi")
    max_players: int = Field(default=5, ge=2, le=50, examples=[5], description="Số người tối đa của đội (mặc định 5)")
    min_rank_id: int | None = Field(default=None, examples=[None], description="Rank tối thiểu (để null nếu không yêu cầu)")
    max_rank_id: int | None = Field(default=None, examples=[None], description="Rank tối đa (để null nếu không yêu cầu)")
    label: str | None = Field(default=None, examples=["Tryhard"], description="Phong cách chơi: Tryhard, Vui vẻ, Có Mic... (để null nếu không chọn)")


class CreateMatchRoomRequest(CreateLobbyRequest):
    """Tương thích ngược với CreateMatchRoomRequest."""
    room_name: str | None = Field(default=None, max_length=150)
    game_code: str | None = Field(default=None, max_length=100)


class InviteFriendResponse(BaseModel):
    message: str
    friend_id: int
    friend_username: str
    notification_id: int | None = None


class QuickMatchRequest(BaseModel):
    """Tìm đội nhanh (Nút cam FIND MATCH)."""
    game_id: int = Field(default=1, examples=[1], description="ID Game muốn tìm phòng")
    label: str | None = Field(default=None, examples=["Tryhard"], description="Ưu tiên ghép vào phòng có cùng nhãn này (để null nếu chơi tự do)")
    rank_id: int | None = Field(default=None, examples=[None], description="Rank của bạn (để null nếu không yêu cầu)")


class FindMatchRequest(QuickMatchRequest):
    """Alias cho QuickMatchRequest."""
    pass


class MatchRoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host_id: int
    game_id: int
    game_name: str | None = None
    room_name: str
    game_code: str | None = None
    max_players: int
    current_players: int
    min_rank_id: int | None = None
    max_rank_id: int | None = None
    label: str | None = None
    status: RoomStatus
    members: list[RoomMemberOut] = []
    created_at: datetime
    updated_at: datetime


class MyRoomResponse(BaseModel):
    in_room: bool
    message: str
    room: MatchRoomOut | None = None


class QuickMatchResponse(BaseModel):
    status: str = Field(description="'MATCHED' hoặc 'SEARCHING' hoặc 'NO_ROOM'")
    message: str
    room: MatchRoomOut | None = None

