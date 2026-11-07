"""Pydantic schemas cho TeamPost và TeamPostApplication.

Request  schemas : TeamPostCreate, TeamPostUpdate, TeamPostApplicationCreate, TeamPostApplicationUpdate
Response schemas : TeamPostOut, TeamPostApplicationOut, TeamPostDetailOut
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.team_post import ApplicationStatus, PostStatus


# ---------------------------------------------------------------------------
# TeamPost schemas
# ---------------------------------------------------------------------------

class TeamPostBase(BaseModel):
    game: str = Field(min_length=1, max_length=100, examples=["Liên Minh Huyền Thoại"])
    min_rank: str | None = Field(default=None, max_length=50, examples=["Silver"])
    max_rank: str | None = Field(default=None, max_length=50, examples=["Platinum"])
    roles_needed: str | None = Field(default=None, max_length=255, examples=["Jungle, Support"])
    slots_needed: int = Field(default=1, ge=1, le=50, examples=[2])
    play_time: str | None = Field(default=None, max_length=100, examples=["20:00-23:00"])
    region: str | None = Field(default=None, max_length=100, examples=["VN"])
    description: str | None = Field(default=None, examples=["Tìm 2 người chơi ranked flex, mic on."])
    expires_at: datetime | None = Field(default=None, examples=["2026-11-30T23:59:59"])


class TeamPostCreate(TeamPostBase):
    """Dữ liệu FE gửi lên khi TẠO bài đăng mới."""
    poster_id: int = Field(examples=[1])


class TeamPostUpdate(BaseModel):
    """Dữ liệu FE gửi lên khi CẬP NHẬT bài đăng (trường nào không gửi thì giữ nguyên)."""
    game: str | None = Field(default=None, min_length=1, max_length=100)
    min_rank: str | None = None
    max_rank: str | None = None
    roles_needed: str | None = None
    slots_needed: int | None = Field(default=None, ge=1, le=50)
    play_time: str | None = None
    region: str | None = None
    description: str | None = None
    status: PostStatus | None = None
    expires_at: datetime | None = None


class TeamPostOut(TeamPostBase):
    """Dữ liệu API trả về cho FE (không kèm danh sách đơn ứng tuyển)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    poster_id: int
    status: PostStatus
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# TeamPostApplication schemas
# ---------------------------------------------------------------------------

class TeamPostApplicationBase(BaseModel):
    message: str | None = Field(default=None, examples=["Mình main Jungle, rank Diamond, có thể chơi tối hàng ngày."])


class TeamPostApplicationCreate(TeamPostApplicationBase):
    """Dữ liệu FE gửi lên khi NỘP đơn ứng tuyển."""
    applicant_id: int = Field(examples=[5])


class TeamPostApplicationUpdate(BaseModel):
    """Dữ liệu cập nhật trạng thái đơn (chỉ dùng bởi poster)."""
    status: ApplicationStatus


class TeamPostApplicationOut(TeamPostApplicationBase):
    """Dữ liệu API trả về."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    applicant_id: int
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime


class TeamPostDetailOut(TeamPostOut):
    """Bài đăng + danh sách tất cả đơn ứng tuyển (dùng cho endpoint chi tiết)."""
    applications: list[TeamPostApplicationOut] = []
