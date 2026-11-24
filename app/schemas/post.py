from datetime import datetime
from enum import Enum
from urllib.parse import urlsplit

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PostStatus(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"


ImageURL = Annotated[str, Field(min_length=1, max_length=500)]


def _validate_image_reference(value: str) -> str:
    reference = value.strip()
    uploaded_path_prefix = "/uploads/posts/"
    if reference.startswith(uploaded_path_prefix) and reference.removeprefix(uploaded_path_prefix):
        return reference
    if reference.startswith("../assets/"):
        return reference

    parsed = urlsplit(reference)
    if parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
        return reference

    raise ValueError("Ảnh phải là URL http(s) hoặc đường dẫn ảnh tải lên hợp lệ")


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    image_urls: list[ImageURL] = Field(default_factory=list, max_length=4)
    game_ids: list[int] = Field(default_factory=list)
    status: PostStatus = PostStatus.VISIBLE

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        return _validate_image_reference(value) if value is not None else None

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[ImageURL]) -> list[ImageURL]:
        return [_validate_image_reference(image_url) for image_url in value]

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

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        return _validate_image_reference(value) if value is not None else None

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[ImageURL] | None) -> list[ImageURL] | None:
        if value is None:
            return None
        return [_validate_image_reference(image_url) for image_url in value]

class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    author_name: str | None = None
    author_username: str | None = None
    author_handle: str | None = None
    author_avatar: str | None = None
    content: str
    image_url: str | None
    image_urls: list[str] = Field(default_factory=list)
    game_ids: list[int]
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    like_count: int
    comment_count: int
    liked_by_current_user: bool = False
