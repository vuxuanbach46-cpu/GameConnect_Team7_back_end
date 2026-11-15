from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReportTargetType(str, Enum):
    USER = "USER"
    POST = "POST"
    COMMENT = "COMMENT"
    TEAM_POST = "TEAM_POST"


class ReportReason(str, Enum):
    SPAM = "SPAM"
    HARASSMENT = "HARASSMENT"
    HATE_SPEECH = "HATE_SPEECH"
    INAPPROPRIATE_CONTENT = "INAPPROPRIATE_CONTENT"
    SCAM = "SCAM"
    OTHER = "OTHER"


class ReportCreate(BaseModel):
    target_type: ReportTargetType
    target_id: int = Field(gt=0)
    reason: ReportReason
    description: Optional[str] = Field(default=None, max_length=2000)
