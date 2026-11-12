import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded

from app.schemas.api_response import api_repoint

logger = logging.getLogger(__name__)


def _create_error_response(
    req: Request,
    status_code: int,
    message: str,
    error: Any,
    headers: dict[str, str] | None = None,
):
    response_data = api_repoint(
        req=req,
        status_code=status_code,
        message=message,
        error=error,
    )
    return JSONResponse(
        status_code=response_data.status_code,
        content=jsonable_encoder(response_data),
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Đăng ký tất cả các exception handlers cho FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request, exc: RequestValidationError
    ):
        return _create_error_response(
            req=request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message="Failed",
            error=exc.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(req: Request, exc: StarletteHTTPException):
        return _create_error_response(
            req=req,
            status_code=exc.status_code,
            message="Failed",
            error=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(req: Request, exc: RateLimitExceeded):
        return _create_error_response(
            req=req,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message="Bạn đã đăng nhập quá nhiều lần",
            error=str(exc),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(req: Request, exc: Exception):
        logger.exception("Unhandled API exception", exc_info=exc)
        return _create_error_response(
            req=req,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Lỗi hệ thống",
            error="Đã xảy ra lỗi không mong muốn.",
        )
