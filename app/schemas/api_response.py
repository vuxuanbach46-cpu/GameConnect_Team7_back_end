from pydantic import BaseModel
from typing import Optional, Any
from fastapi import Request
from datetime import datetime


class APIRepoint(BaseModel):
    status_code: int
    message: str
    data: Optional[Any] = None
    error: Optional[Any] = None
    timestamp: str
    path: str


def api_repoint(
    req: Request, status_code: int, message: str, data: Any = None, error: Any = None
):
    return APIRepoint(
        status_code=status_code,
        message=message,
        data=data,
        error=error,
        timestamp=datetime.now().isoformat(),
        path=req.url.path,
    )
