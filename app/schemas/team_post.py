"""Pydantic schemas cho TeamPost, TeamPostRole, TeamPostApplication.

Khớp chuẩn schema GameConnect (task T3CCC1C).
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.team_post import ApplicationStatus, PostStatus


# ---------------------------------------------------------------------------
# TeamPost schemas
# ---------------------------------------------------------------------------

class TeamPostBase(BaseModel):
    game_id: int = Field(examples=[1], description="ID game (FK → games.id)")
    title: str = Field(min_length=1, max_length=150, examples=["[VN] Tìm Jungle + Support leo Plat"])
    min_rank_id: int | None = Field(default=None, examples=[3], description="ID rank tối thiểu (FK → game_ranks.id)")
    max_rank_id: int | None = Field(default=None, examples=[6], description="ID rank tối đa (FK → game_ranks.id)")
    needed_players: int = Field(default=1, ge=1, le=9, examples=[2], description="Số người cần tuyển (1–9 người)")
    play_time: str | None = Field(default=None, max_length=100, examples=["20:00-23:00"])
    region: str | None = Field(default=None, max_length=100, examples=["VN"])
    description: str | None = Field(default=None, examples=["Mic on bắt buộc, không toxic."])
    expires_at: datetime | None = Field(default=None, examples=["2026-11-17T23:59:59"], description="Hạn hiển thị tối đa 7 ngày")


class TeamPostCreate(TeamPostBase):
    """Dữ liệu gửi lên khi TẠO bài đăng tìm đội."""
    user_id: int | None = Field(default=None, description="ID người đăng (tự động lấy từ token nếu có)")
    role_ids: list[int] = Field(
        default=[], examples=[[2, 4]], description="Danh sách game_role_id vai trò cần tuyển"
    )


class TeamPostUpdate(BaseModel):
    """Dữ liệu gửi lên khi CẬP NHẬT bài đăng."""
    title: str | None = Field(default=None, min_length=1, max_length=150)
    min_rank_id: int | None = None
    max_rank_id: int | None = None
    needed_players: int | None = Field(default=None, ge=1, le=9)
    play_time: str | None = None
    region: str | None = None
    description: str | None = None
    status: PostStatus | None = None
    expires_at: datetime | None = None
    role_ids: list[int] | None = Field(default=None, description="Ghi đè danh sách vai trò")


class TeamPostOut(TeamPostBase):
    """Dữ liệu API trả về."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    role_ids: list[int] = []


# ---------------------------------------------------------------------------
# TeamPostApplication schemas
# ---------------------------------------------------------------------------

class TeamPostApplicationBase(BaseModel):
    message: str | None = Field(
        default=None, examples=["Mình main Jungle Diamond, mic on, chơi được 20h-24h."]
    )


class TeamPostApplicationCreate(TeamPostApplicationBase):
    """Dữ liệu gửi lên khi NỘP đơn ứng tuyển."""
    user_id: int | None = Field(default=None, description="ID người ứng tuyển (tự động lấy từ token nếu có)")


class TeamPostApplicationUpdate(BaseModel):
    """Cập nhật trạng thái đơn ứng tuyển."""
    status: ApplicationStatus


class TeamPostApplicationOut(TeamPostApplicationBase):
    """Dữ liệu đơn ứng tuyển trả về."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_post_id: int
    user_id: int
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class TeamPostDetailOut(TeamPostOut):
    """Chi tiết bài đăng kèm danh sách đơn ứng tuyển."""
    applications: list[TeamPostApplicationOut] = []
