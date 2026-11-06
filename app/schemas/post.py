from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PostStatus(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"


class PostBase(BaseModel):
    content: str = Field(min_length=1)
    image_url: str | None = Field(default=None, max_length=500)
    game_id: int | None = None
    status: PostStatus = PostStatus.VISIBLE


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    image_url: str | None = Field(default=None, max_length=500)
    game_id: int | None = None
    status: PostStatus | None = None


class PostOut(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class CommentBase(BaseModel):
    content: str = Field(min_length=1)
    parent_id: int | None = None


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1)


class CommentOut(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class PostLikeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    created_at: datetime
