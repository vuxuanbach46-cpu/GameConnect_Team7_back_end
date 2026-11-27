from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PostLikeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    created_at: datetime
