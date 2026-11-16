from datetime import datetime
from enum import Enum

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PostStatus(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"


ImageURL = Annotated[str, Field(min_length=1, max_length=500)]


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    image_urls: list[ImageURL] = Field(default_factory=list, max_length=4)
    game_ids: list[int] = Field(default_factory=list)
    status: PostStatus = PostStatus.VISIBLE

    @model_validator(mode="after")
    def validate_image_fields(self):
        image_urls = list(self.image_urls)
        if self.image_url and self.image_url not in image_urls:
            image_urls.insert(0, self.image_url)
        if len(image_urls) > 4:
            raise ValueError("Chỉ được đính kèm tối đa 4 ảnh")
        self.image_urls = image_urls
        if image_urls:
            self.image_url = image_urls[0]
        return self


class PostUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    image_urls: list[ImageURL] | None = Field(default=None, max_length=4)
    game_ids: list[int] | None = None
    status: PostStatus | None = None

class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    content: str
    image_url: str | None
    image_urls: list[str] = Field(default_factory=list)
    game_ids: list[int]
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    like_count: int
    comment_count: int
