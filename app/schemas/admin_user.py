from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import AuthProvider, UserRole, UserStatus


class AdminUserItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    email: str
    username: str
    role: UserRole
    status: UserStatus
    auth_provider: AuthProvider
    locked_until: datetime | None = None
    locked_reason: str | None = None
    created_at: datetime
    last_seen: datetime | None = None


class AdminUserPage(BaseModel):
    items: list[AdminUserItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class LockUserRequest(BaseModel):
    duration_days: Literal[1, 7, 30] | None = Field(
        default=None,
        description="Số ngày khóa; null hoặc bỏ trống nghĩa là khóa vĩnh viễn.",
    )
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Lý do khóa không được để trống")
        return value
