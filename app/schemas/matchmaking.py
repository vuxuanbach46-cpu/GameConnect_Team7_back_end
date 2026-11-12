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


class CreateMatchRoomRequest(BaseModel):
    game_id: int = Field(default=1, examples=[1], description="ID Game (vd: 1)")
    room_name: str = Field(default="Phòng leo rank tối nay, mic on", min_length=1, max_length=150, examples=["Phòng leo rank tối nay, mic on"])
    game_code: str = Field(default="AMONG-9981", min_length=1, max_length=100, examples=["AMONG-9981", "VALO-7721"])
    max_players: int = Field(default=2, ge=2, le=50, examples=[2], description="Số người tối đa để đủ đội")
    min_rank_id: int | None = Field(default=None, examples=[None], description="Rank tối thiểu (để null nếu không yêu cầu; bắt buộc null nếu game không có rank)")
    max_rank_id: int | None = Field(default=None, examples=[None], description="Rank tối đa (để null nếu không yêu cầu; bắt buộc null nếu game không có rank)")
    label: str | None = Field(default=None, examples=["Tryhard"], description="Nhãn / Phong cách chơi: Tryhard, Vui vẻ, Có Mic... (để null nếu không chọn)")


class QuickMatchRequest(BaseModel):
    game_id: int = Field(default=1, examples=[1], description="ID Game muốn tìm phòng (vd: 1)")
    label: str | None = Field(default=None, examples=["Tryhard"], description="Ưu tiên ghép vào phòng có cùng nhãn này (để null nếu chơi tự do)")
    rank_id: int | None = Field(default=None, examples=[None], description="Rank của bạn (để null nếu không yêu cầu)")


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
    status: str = Field(description="'MATCHED' hoặc 'NO_ROOM'")
    message: str
    room: MatchRoomOut | None = None
