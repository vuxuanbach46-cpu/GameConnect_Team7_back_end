from typing import Callable

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token
from app.schemas.api_response import api_repoint
from starlette.requests import Request
from starlette.responses import Response


def _auth_error(request: Request, message: str) -> JSONResponse:
    response = api_repoint(
        req=request,
        status_code=401,
        message="Failed",
        error=message,
    )
    return JSONResponse(
        status_code=response.status_code,
        content=jsonable_encoder(response),
        headers={"WWW-Authenticate": "Bearer"},
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        request.state.user_id = None

        authorization = request.headers.get("Authorization")

        # Không có token: cho phép Guest
        if not authorization:
            return await call_next(request)

        # Kiểm tra Bearer token
        scheme, _, token = authorization.partition(" ")

        if scheme.lower() != "bearer" or not token:
            return _auth_error(request, "Authorization header không hợp lệ.")

        try:
            user_id = decode_access_token(token)

            request.state.user_id = user_id

        except ExpiredSignatureError:
            return _auth_error(request, "Token hết hạn")
        except (JWTError, KeyError, TypeError, ValueError):
            return _auth_error(request, "Token không hợp lệ")
        return await call_next(request)
