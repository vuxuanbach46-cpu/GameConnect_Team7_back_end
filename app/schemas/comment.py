from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_comment_id: int | None = Field(default=None, ge=1)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    author_name: str | None = None
    author_username: str | None = None
    author_avatar: str | None = None
    content: str
    parent_comment_id: int | None
    created_at: datetime
    updated_at: datetime
