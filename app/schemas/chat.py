from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="Nội dung tin nhắn")

    @field_validator("content")
    @classmethod
    def validate_content_not_blank(cls, v: str) -> str:
        cleaned = (v or "").strip()
        if not cleaned:
            raise ValueError("Nội dung tin nhắn không được để trống")
        if len(cleaned) > 2000:
            raise ValueError("Nội dung tin nhắn tối đa 2000 ký tự")
        return cleaned


class DirectMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: datetime
    is_mine: bool = False


class UnreadCountsResponse(BaseModel):
    total_unread: int = 0
    by_friend: dict[str, int] = {}
