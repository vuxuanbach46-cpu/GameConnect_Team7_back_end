"""Pydantic schemas cho TeamPost, TeamPostRole, TeamPostApplication.

Khớp với schema DBML GameConnect (task T3CCC1C).
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
    needed_players: int = Field(default=1, ge=1, le=50, examples=[2])
    play_time: str | None = Field(default=None, max_length=100, examples=["20:00-23:00"])
    region: str | None = Field(default=None, max_length=100, examples=["VN"])
    description: str | None = Field(default=None, examples=["Mic on bắt buộc, không toxic."])
    expires_at: datetime | None = Field(default=None, examples=["2026-11-30T23:59:59"])


class TeamPostCreate(TeamPostBase):
    """Dữ liệu FE gửi lên khi TẠO bài đăng."""
    user_id: int = Field(examples=[1], description="ID người đăng (FK → users.id)")
    role_ids: list[int] = Field(
        default=[], examples=[[2, 4]], description="Danh sách game_role_id cần tuyển"
    )


class TeamPostUpdate(BaseModel):
    """Dữ liệu FE gửi lên khi CẬP NHẬT (trường nào không gửi thì giữ nguyên)."""
    title: str | None = Field(default=None, min_length=1, max_length=150)
    min_rank_id: int | None = None
    max_rank_id: int | None = None
    needed_players: int | None = Field(default=None, ge=1, le=50)
    play_time: str | None = None
    region: str | None = None
    description: str | None = None
    status: PostStatus | None = None
    expires_at: datetime | None = None
    role_ids: list[int] | None = Field(default=None, description="Ghi đè toàn bộ danh sách vai trò")


class TeamPostOut(TeamPostBase):
    """Dữ liệu API trả về (không kèm đơn ứng tuyển)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: PostStatus
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# TeamPostApplication schemas
# ---------------------------------------------------------------------------

class TeamPostApplicationBase(BaseModel):
    message: str | None = Field(
        default=None, examples=["Mình main Jungle Diamond, mic on, chơi được 20h-24h."]
    )


class TeamPostApplicationCreate(TeamPostApplicationBase):
    """Dữ liệu FE gửi lên khi NỘP đơn ứng tuyển."""
    user_id: int = Field(examples=[5], description="ID người ứng tuyển (FK → users.id)")


class TeamPostApplicationUpdate(BaseModel):
    """Cập nhật trạng thái đơn (poster duyệt / từ chối, hoặc applicant tự rút)."""
    status: ApplicationStatus


class TeamPostApplicationOut(TeamPostApplicationBase):
    """Dữ liệu API trả về."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_post_id: int
    user_id: int
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class TeamPostDetailOut(TeamPostOut):
    """Bài đăng + danh sách đơn ứng tuyển (endpoint chi tiết)."""
    applications: list[TeamPostApplicationOut] = []
